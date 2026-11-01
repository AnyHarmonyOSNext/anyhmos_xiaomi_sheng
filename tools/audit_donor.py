"""Inventory an extracted donor and check existing patch input hashes, read-only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import stat

ROOT = Path(__file__).resolve().parent.parent


def is_link(path):
    info = path.lstat()
    return path.is_symlink() or bool(
        getattr(info, 'st_file_attributes', 0)
        & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
    )


# 流式计算文件指纹并识别 ELF 架构
def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        header = stream.read(64)
        digest.update(header)
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    result = {'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
    if header.startswith(b'\x7fELF'):
        result['elf'] = {
            'class': header[4] if len(header) > 4 else None,
            'byte_order': header[5] if len(header) > 5 else None,
        }
        if len(header) >= 20 and header[5] in (1, 2):
            order = '<' if header[5] == 1 else '>'
            result['elf']['machine'] = struct.unpack_from(order + 'H', header, 18)[0]
    return result


# 逐个核对同名文件，避免误用其他目录的库
def audit(root, recipe_root):
    files = []
    by_name = {}
    skipped = []
    for directory, folders, names in os.walk(root, followlinks=False):
        folders.sort()
        names.sort()
        # Do not leave the supplied extraction tree through links or junctions.
        for folder in folders[:]:
            child = Path(directory) / folder
            if is_link(child) or not child.resolve().is_relative_to(root):
                folders.remove(folder)
                skipped.append(child.relative_to(root).as_posix())
        for name in names:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if is_link(path) or not path.is_file():
                skipped.append(relative)
                continue
            record = {'path': relative, **fingerprint(path)}
            files.append(record)
            by_name.setdefault(name, []).append(record)
    checks = []
    for recipe_path in sorted(recipe_root.glob('*.json')):
        recipe = json.loads(recipe_path.read_text(encoding='utf-8-sig'))
        name = recipe['name']
        candidates = by_name.get(name, [])
        # Each path is checked separately: a matching basename is not identity.
        results = []
        for candidate in candidates:
            sha = candidate['sha256']
            status = (
                'input_hash_matched'
                if sha == recipe['input_sha256']
                else (
                    'already_patched'
                    if sha == recipe['output_sha256']
                    else 'different_input_requires_review'
                )
            )
            results.append({'path': candidate['path'], 'status': status})
        checks.append(
            {
                'recipe': recipe_path.name,
                'name': name,
                'status': 'candidates_found' if candidates else 'missing',
                'candidates': results,
            }
        )
    return {
        'format_version': 1,
        'read_only': True,
        'scope': 'Extracted files only; model, ABI and bootability are not validated',
        'files': files,
        'skipped_links_or_special_files': sorted(skipped),
        'existing_patch_input_checks': checks,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'root', type=Path, help='Extracted donor directory, not a ZIP or UPDATE.APP'
    )
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument(
        '--model', required=True, help='Declared model, to verify against donor metadata'
    )
    parser.add_argument('--build', required=True, help='Declared complete HarmonyOS build number')
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    if not root.is_dir():
        parser.error('Extract the donor first; root must be a directory')
    if output.is_relative_to(root):
        parser.error('Write the report outside the donor directory')
    if output.exists():
        parser.error('Output already exists; choose a new report path')
    report = audit(root, ROOT / 'patches/donor')
    report['declared_donor'] = {
        'model': args.model,
        'build': args.build,
        'metadata_verified': False,
    }
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(
        json.dumps(
            {'files': len(report['files']), 'report': str(output), 'firmware_modified': False}
        )
    )


if __name__ == '__main__':
    main()
