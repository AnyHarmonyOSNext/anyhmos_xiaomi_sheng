"""Create and verify a text-only, redacted source snapshot without device access.

Only the destination copy is redacted. Existing destinations are never replaced.
Run the WSL exporter first, then supply its output with --wsl-export.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote
import zipfile


EXTENSIONS = {
    '.c', '.cc', '.cpp', '.h', '.hpp', '.s', '.inc', '.py', '.sh', '.ps1',
    '.cfg', '.hcs', '.json', '.ini', '.map', '.yaml', '.yml', '.toml',
    '.config', '.patch', '.diff', '.mk', '.cmake', '.gn', '.gni', '.idl',
    '.def', '.lds', '.dts', '.dtsi', '.md', '.path', '.list',
}
NAMES = {
    'Makefile', 'Kbuild', 'Kconfig', 'CMakeLists.txt', 'meson.build',
    'meson_options.txt', 'LICENSE', 'COPYING', 'NOTICE', 'README', 'VERSION',
}
SKIP_PARTS = {'.git', '__pycache__', 'node_modules', '.venv', 'build', 'out'}
PRIVATE_KEYS = re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')
SECRET_PATTERNS = {
    'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'private_key': PRIVATE_KEYS,
    'literal_credential': re.compile(
        r'''(?im)^\s*(?:["']?)(?:password|psk|access_token|api_key)(?:["']?)\s*[:=]\s*["']([^"'\r\n]{6,})["']'''),
    'bearer_token': re.compile(r'(?i)Authorization\s*[:=]\s*["\']?Bearer\s+[A-Za-z0-9_.-]{20,}'),
}
PRIVATE_IPV4 = re.compile(
    r'(?<![\w.])(?:192\.168\.(?:\d{1,3}\.)\d{1,3}|10\.(?:\d{1,3}\.){2}\d{1,3}|'
    r'172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3})(?![\w.])')
MAC = re.compile(r'(?i)(?<![\w:])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![\w:])')

GITIGNORE = '''# Generated runtime inputs, proprietary extracts, and personal data
/work/
/release/
/output/releases/
/output/logs/
/output/screenshots/
/output/device-backup/
/output/platform-tools/
__pycache__/
*.pyc
.venv/
node_modules/
*.img
*.bin
*.dtb
*.so
*.so.*
*.ko
*.o
*.a
*.elf
*.exe
*.dll
*.hap
*.abc
*.hcb
*.zip
*.gz
*.log
.env
.env.*
*.pem
*.key
'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def accepted(path: Path) -> bool:
    return (path.suffix.lower() in EXTENSIONS or path.name in NAMES or
            path.name.startswith(('LICENSE', 'COPYING', 'NOTICE')))


def analysis_selected(path: Path) -> bool:
    if path.suffix in {'.patch', '.config'}:
        return True
    # Do not publish raw round notes, runtime captures, GPT dumps or telemetry.
    if path.suffix != '.json' or path.name.startswith(('round-', 'runtime-', 'gpt-')):
        return False
    return (path.name.endswith(('-verification.json', '-build.json', '-inputs.json',
                                '-package.json', '-preparation.json', '-abi.json',
                                '-patch.json')) or
            path.name in {'sheng-ipc-reference-sha256.json', 'stock-module-import-crcs.json'})


def replacements(root: Path) -> list[tuple[str, str]]:
    home = Path.home()
    # Longest paths first, including escaped JSON and source-code spellings.
    items = []
    for original, target in [(str(root), r'C:\SHENG_WORKSPACE'),
                             (str(home), r'C:\Users\YOUR_USER')]:
        items += [(original.replace('\\', '\\\\'), target.replace('\\', '\\\\')),
                  (original.replace('\\', '/'), target.replace('\\', '/')),
                  (original, target),
                  (json.dumps(original, ensure_ascii=True)[1:-1],
                   json.dumps(target)[1:-1])]
    if root.drive:
        wsl = '/mnt/' + root.drive[0].lower() + root.as_posix()[2:]
        items.append((wsl, '/mnt/c/SHENG_WORKSPACE'))
    if home.drive:
        wsl_home = '/mnt/' + home.drive[0].lower() + home.as_posix()[2:]
        items.append((wsl_home, '/mnt/c/Users/YOUR_USER'))
    stock = os.environ.get('SHENG_REDACT_STOCK_IMAGES', '')
    if stock:
        items.extend([(stock.replace('\\', '/'), 'E:/SHENG_STOCK_303/images'),
                      (stock, r'E:\SHENG_STOCK_303\images')])
    # JSON reports may escape non-ASCII usernames even in forward-slash paths.
    for original, target in list(items):
        items.append((json.dumps(original, ensure_ascii=True)[1:-1],
                      json.dumps(target, ensure_ascii=True)[1:-1]))
    serial = os.environ.get('SHENG_REDACT_DEVICE_SERIAL', '')
    if not serial:
        raise RuntimeError('Set SHENG_REDACT_DEVICE_SERIAL to the private test-device serial.')
    items.append((serial, 'YOUR_DEVICE_SERIAL'))
    return sorted(set(items), key=lambda item: -len(item[0]))


def redact(text: str, rules, counts: Counter) -> str:
    for index, (original, target) in enumerate(rules):
        n = text.count(original)
        if n:
            text = text.replace(original, target)
            counts['path_or_serial_rule_' + str(index)] += n
    # Redact textual network observations/defaults; byte-array constants in
    # driver code are intentionally not matched by these dotted/colon patterns.
    for label, pattern, replacement in [
        ('private_ipv4', PRIVATE_IPV4, '192.0.2.1'),
        ('mac_address', MAC, '02:00:00:00:00:01'),
    ]:
        text, n = pattern.subn(replacement, text)
        counts[label] += n
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--wsl-export', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    export = args.wsl_export.resolve()
    destination = args.destination.resolve()
    archive = args.archive.resolve()
    if destination.exists() or archive.exists() or archive.with_suffix('.zip.sha256').exists():
        raise RuntimeError('Destination/archive already exists; select new output names.')
    if (not (export/'upstream-sources.json').is_file() or
            not (export/'custom-sources.json').is_file()):
        raise RuntimeError('Missing completed WSL source export.')
    if destination == root or root.is_relative_to(destination):
        raise RuntimeError('Destination cannot contain the development root.')
    rules = replacements(root)
    candidates: dict[str, Path] = {}
    excluded = Counter()

    def add_tree(source: Path, prefix: str, allow_all_text=False):
        for path in sorted(source.rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(source)
            if path.is_symlink() or any(part in SKIP_PARTS for part in rel.parts):
                excluded['symlink_or_cache'] += 1
                continue
            if not allow_all_text and not accepted(path):
                excluded['not_source_extension'] += 1
                continue
            candidates[prefix+'/'+rel.as_posix()] = path

    for name in ('README.md', 'README.en.md'):
        candidates[name] = root/name
    for name in ('tools', 'compat', 'docs'):
        add_tree(root/name, name)
    add_tree(export, 'external', allow_all_text=True)
    for path in sorted((root/'output').glob('*.ps1')):
        if path.is_file() and not path.is_symlink():
            candidates['output/'+path.name] = path
    for path in sorted((root/'analysis').iterdir()):
        if path.is_file() and analysis_selected(path):
            candidates['analysis/'+path.name] = path

    destination.mkdir(parents=True, exist_ok=False)
    copied = Counter()
    redactions = Counter()
    issues = []
    for rel, path in sorted(candidates.items()):
        raw = path.read_bytes()
        if b'\0' in raw or raw.startswith((b'\x7fELF', b'MZ')):
            excluded['binary_content'] += 1
            continue
        try:
            value = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            excluded['non_utf8_content'] += 1
            continue
        value = redact(value, rules, redactions)
        for label, pattern in SECRET_PATTERNS.items():
            # This tool's regular expressions are not actual credentials.
            if rel != 'tools/package_source_release.py' and pattern.search(value):
                issues.append(dict(path=rel, check=label))
        if any(original in value for original, _ in rules):
            issues.append(dict(path=rel, check='private_host_path'))
        target = destination/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
        target.write_bytes(value.replace('\r\n', '\n').encode(encoding))
        copied[rel.split('/')[0]] += 1

    # Keep source bytes stable across clone/checkout so the manifest remains valid.
    (destination/'.gitattributes').write_text('* -text\n', encoding='utf-8')
    (destination/'.gitignore').write_text(GITIGNORE, encoding='utf-8')
    release_info = dict(
        snapshot_date='2026-10-30', current_persistent_version='v145',
        package_type='redacted_text_source_snapshot', complete_rom=False,
        screen_off_user_accepted=True, git_upload_performed=False,
        external_binaries_included=False, files_by_section=dict(copied),
        excluded_categories=dict(excluded),
        notes=['Historical and withdrawn experiments are included for review, not automatic enablement.',
               'Host paths, the test serial, and textual private network addresses are publication placeholders.',
               'Checksums cover the exported/redacted bytes, not the original development files.',
               'No blanket license is assigned; see docs/PROVENANCE.md.'])
    (destination/'RELEASE.json').write_text(json.dumps(release_info, indent=2)+'\n', encoding='utf-8')

    files = sorted(path for path in destination.rglob('*') if path.is_file())
    records = [dict(path=path.relative_to(destination).as_posix(),
                    bytes=path.stat().st_size, sha256=digest(path.read_bytes())) for path in files]
    manifest = dict(format_version=1, hash_algorithm='SHA256', files=records,
                    excludes=['SOURCE-MANIFEST.json', 'SHA256SUMS'])
    manifest_path = destination/'SOURCE-MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (destination/'SHA256SUMS').write_text(''.join(
        f"{item['sha256']}  {item['path']}\n" for item in records) +
        f'{digest(manifest_path.read_bytes())}  SOURCE-MANIFEST.json\n', encoding='utf-8')

    # Markdown navigation must resolve in the export; external URLs are not fetched.
    for path in [destination/'README.md', destination/'README.en.md',
                 *sorted((destination/'docs').glob('*.md'))]:
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            resolved = path.parent/unquote(target.split('#')[0].strip('<>'))
            if not resolved.exists():
                issues.append(dict(path=str(path.relative_to(destination)), check='markdown_link', target=target))
    for record in records:
        data = (destination/record['path']).read_bytes()
        if len(data) != record['bytes'] or digest(data) != record['sha256']:
            issues.append(dict(path=record['path'], check='manifest_hash'))
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  release=release_info, redaction_counts=dict(redactions),
                  candidate_files=len(candidates), published_files=len(records)+2,
                  published_bytes=sum(p.stat().st_size for p in destination.rglob('*') if p.is_file()),
                  issues=issues, archive_created=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if issues:
        args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        raise RuntimeError(f'{len(issues)} publication issues; review report (values are not logged).')

    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                bundle.write(path, destination.name+'/'+path.relative_to(destination).as_posix())
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('ZIP CRC validation failed.')
        entries = bundle.namelist()
        expected = {destination.name+'/'+p.relative_to(destination).as_posix(): p
                    for p in destination.rglob('*') if p.is_file()}
        if set(entries) != set(expected) or len(entries) != len(expected):
            raise RuntimeError('Archive file coverage mismatch.')
        for name, path in expected.items():
            if bundle.read(name) != path.read_bytes():
                raise RuntimeError('Archive byte comparison failed: '+name)
    archive_sha = digest(archive.read_bytes())
    archive.with_suffix('.zip.sha256').write_text(archive_sha+'  '+archive.name+'\n', encoding='utf-8')
    report.update(archive_created=True, archive_bytes=archive.stat().st_size,
                  archive_sha256=archive_sha, zip_crc_and_byte_comparison_passed=True,
                  manifest_verified=True, markdown_navigation_verified=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
