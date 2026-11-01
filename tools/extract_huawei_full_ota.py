"""Stream selected components from a full Huawei ZIP; verify ZIP CRC and hashes.

The L2 container uses 87-byte component records and a 64-bit stored size.
Container hashes prove consistency, not the authenticity of its signature.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

BLOCK = 4 * 1024 * 1024


def exact(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise ValueError('Truncated update payload')
    return data


# 解析含 64 位长度的组件表并检查容器边界
def header(stream, payload_size):
    raw = exact(stream, 180)
    if struct.unpack_from('<H', raw)[0] != 1 or struct.unpack_from('<H', raw, 176)[0] != 5:
        raise ValueError('Unsupported update container header')
    count_bytes = struct.unpack_from('<H', raw, 178)[0]
    if count_bytes == 0 or count_bytes % 87:
        raise ValueError('Unsupported component record layout')
    records = exact(stream, count_bytes)
    exact(stream, 16)
    signature_type = struct.unpack('<H', exact(stream, 2))[0]
    if signature_type == 6:
        exact(stream, 16)
    elif signature_type != 8:
        raise ValueError('Unsupported signature TLV')
    signature_size = struct.unpack('<I', exact(stream, 4))[0]
    if signature_size > 1024 * 1024:
        raise ValueError('Unexpected signature size')
    exact(stream, signature_size)
    offset = stream.tell()
    components = []
    names = set()
    for pos in range(0, count_bytes, 87):
        name = records[pos : pos + 32].split(b'\0')[0].decode().removeprefix('/')
        if (
            not name
            or name in names
            or any(
                c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
                for c in name
            )
        ):
            raise ValueError('Invalid or duplicate component name')
        names.add(name)
        size = struct.unpack_from('<Q', records, pos + 47)[0]
        digest = records[pos + 55 : pos + 87].hex()
        components.append({'name': name, 'offset': offset, 'bytes': size, 'sha256': digest})
        offset += size
    if offset != payload_size:
        raise ValueError('Component lengths do not match payload size')
    return components


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(BLOCK), b''):
            digest.update(block)
    return digest.hexdigest()


# 逐块校验组件，验证后再将临时文件转为镜像
def extract(source, destination, selected):
    before = source.stat()
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / 'extraction-report.json'
    if report_path.exists():
        raise FileExistsError('Existing report; use a new output directory')
    results = []
    with zipfile.ZipFile(source) as archive:
        if len({i.filename for i in archive.infolist()}) != len(archive.infolist()):
            raise ValueError('Duplicate ZIP member names')
        metadata = {}
        for name in ('packageinfo.mbn', 'VERSION.mbn', 'update.tag'):
            if archive.getinfo(name).file_size > 65536:
                raise ValueError('Unexpected metadata size')
            metadata[name] = archive.read(name).decode('utf-8', errors='replace')
        if 'PKG_DATA_TYPE=FULL' not in metadata['update.tag']:
            raise ValueError('Only full OTA packages are accepted')
        info = archive.getinfo('update.bin')
        with archive.open(info) as stream:
            components = header(stream, info.file_size)
            missing = selected - {c['name'] for c in components}
            if missing:
                raise ValueError('Missing requested components: ' + ', '.join(sorted(missing)))
            for component in components:
                output = destination / (component['name'] + '.img')
                temp = output.with_suffix('.img.part')
                save = component['name'] in selected
                if save and (output.exists() or temp.exists()):
                    raise FileExistsError('Refusing to overwrite ' + str(output))
                digest = hashlib.sha256()
                remaining = component['bytes']
                writer = temp.open('xb') if save else None
                try:
                    while remaining:
                        block = exact(stream, min(BLOCK, remaining))
                        digest.update(block)
                        if writer:
                            writer.write(block)
                        remaining -= len(block)
                finally:
                    if writer:
                        writer.close()
                if digest.hexdigest() != component['sha256']:
                    raise ValueError('Component hash mismatch: ' + component['name'])
                if save:
                    temp.rename(output)
                result = {**component, 'hash_verified': True, 'extracted': save}
                results.append(result)
                print(
                    json.dumps(
                        {
                            'component': component['name'],
                            'bytes': component['bytes'],
                            'hash_verified': True,
                            'extracted': save,
                        }
                    ),
                    flush=True,
                )
            if stream.read(1):
                raise ValueError('Unexpected trailing payload data')
        # update.bin was read to EOF, which also checks its ZIP CRC.
        for entry in archive.infolist():
            if entry.filename == 'update.bin' or entry.is_dir():
                continue
            with archive.open(entry) as stream:
                while stream.read(BLOCK):
                    pass
    digest = file_hash(source)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Input ZIP changed during verification')
    report = {
        'input_file': source.name,
        'input_bytes': before.st_size,
        'input_sha256': digest,
        'zip_crc_verified': True,
        'container_component_hashes_verified': True,
        'signature_verified': False,
        'metadata': metadata,
        'components': results,
    }
    with report_path.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(json.dumps({'report': str(report_path), 'sha256': digest}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip_file', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--components', nargs='*', default=[])
    args = parser.parse_args()
    extract(args.zip_file.resolve(strict=True), args.output.resolve(), set(args.components))


if __name__ == '__main__':
    main()
