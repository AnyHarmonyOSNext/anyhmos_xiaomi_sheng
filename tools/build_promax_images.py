"""Build, then read back, the private GEM-W00 experimental image set.

This tool only writes host files. It never opens or flashes a connected device.
Inputs must have passed extract_huawei_full_ota.py component verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from android_sparse import SparseImage, inspect_super

SUPER_BYTES = 11811160064
BASE_HASHES = {
    'boot.img': 'f5212b2ebc2e7cb8f35be7b3da4d2fd39219c63c83b3c9debfee7dbdcdc127b3',
    'init_boot.img': '6f3eb88aa1422f6ed114f58c0e32e991b01b9ab3fa96c386626434891e215ef9',
    'vbmeta.img': 'a4bb3bd335ea7016696137f88e1f8bc661b1d8faeb3f12dbad7d3f22a6ec5eb4',
    'vbmeta_system.img': 'f39d9f548bd51dfd1325aa1ab118a765d0e604b5270271b797ff65b582c61ae2',
}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


# 将 Windows 绝对路径转换为 Cygwin 路径
def cygpath(path):
    path = str(Path(path).resolve()).replace('\\', '/')
    if len(path) < 3 or path[1:3] != ':/':
        raise ValueError('Expected an absolute Windows drive path')
    return '/cygdrive/' + path[0].lower() + path[2:]


def run(args, log):
    with Path(log).open('wb') as out:
        result = subprocess.run([str(a) for a in args], stdout=out, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'Build tool failed ({result.returncode}); see {log}')


# 构建精确容量镜像并回读分区内容
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', type=Path, required=True)
    parser.add_argument('--original', type=Path, required=True, help='Known bootable package root')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--userdata-bytes', type=int, required=True)
    args = parser.parse_args()
    if args.userdata_bytes % 4096 or args.userdata_bytes < 16 * 1024**3:
        raise ValueError('Invalid exact userdata capacity')
    images = args.output / 'images'
    images.mkdir(parents=True, exist_ok=True)
    args.work.mkdir(parents=True, exist_ok=True)
    report_dir = args.output / 'reports'
    report_dir.mkdir(exist_ok=True)
    if any(images.iterdir()):
        raise FileExistsError('Output images directory must be empty; do not overwrite a release')
    seed = args.work / 'seed-root' / 'hmos-promax'
    seed.mkdir(parents=True, exist_ok=True)
    report = {
        'kind': 'experimental-private-image-build',
        'device_boot_tested': False,
        'userdata_bytes': args.userdata_bytes,
        'super_bytes': SUPER_BYTES,
        'donor': 'GEM-LGRP3-CHN 207.0.0.111(SP12)',
        'seed_images': [],
    }
    for name in ['preload', 'chip_prod', 'anco_hmos', 'cust', 'version']:
        folder = 'preload' if name == 'preload' else 'cust' if name == 'version' else 'base'
        source = args.donor / 'extracted' / folder / (name + '.img')
        extraction = json.loads(
            (source.parent / 'extraction-report.json').read_text(encoding='utf-8')
        )
        record = next(c for c in extraction['components'] if c['name'] == name)
        actual = digest(source)
        if not record['hash_verified'] or not record['extracted'] or actual != record['sha256']:
            raise ValueError('Unverified seed input: ' + name)
        link = seed / source.name
        if link.exists():
            if not os.path.samefile(source, link):
                raise ValueError('Seed path is not the expected source hardlink')
        else:
            os.link(source, link)
        report['seed_images'].append(
            {'name': name, 'bytes': source.stat().st_size, 'sha256': actual}
        )
    if set(p.name for p in seed.iterdir()) != {r['name'] + '.img' for r in report['seed_images']}:
        raise ValueError('Unexpected file in userdata seed')
    print('Building the exact-capacity ext4 userdata seed', flush=True)
    ext4 = images / 'userdata.img'
    features = 'none,has_journal,ext_attr,resize_inode,dir_index,filetype,extent,sparse_super,large_file,huge_file,uninit_bg,dir_nlink,extra_isize'
    run(
        [
            args.tools / 'android-fs/mke2fs.exe',
            '-t',
            'ext4',
            '-b',
            '4096',
            '-I',
            '256',
            '-i',
            '16384',
            '-m',
            '0',
            '-L',
            'hmos-promax',
            '-O',
            features,
            '-E',
            'android_sparse,lazy_itable_init=1,lazy_journal_init=1,root_owner=0:0',
            '-d',
            cygpath(seed.parent),
            cygpath(ext4),
            str(args.userdata_bytes // 4096),
        ],
        args.work / 'mke2fs.log',
    )
    sparse = SparseImage(ext4)
    if sparse.size != args.userdata_bytes:
        raise ValueError('Userdata expanded capacity mismatch')
    sb = sparse.read_at(1024, 1024)
    if sb[56:58] != b'\x53\xef' or not int.from_bytes(sb[96:100], 'little') & 0x40:
        raise ValueError('Ext4 extent feature or magic missing')
    raw = args.work / 'userdata-verification.raw.img'
    sparse.expand_ntfs_sparse(raw)
    sparse.close()
    for record in report['seed_images']:
        name = 'hmos-promax/' + record['name'] + '.img'
        proc = subprocess.Popen(
            [r'C:\Program Files\7-Zip\7z.exe', 'x', '-so', str(raw), name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        hashed = hashlib.sha256()
        count = 0
        for block in iter(lambda: proc.stdout.read(4 * 1024 * 1024), b''):
            hashed.update(block)
            count += len(block)
        error = proc.stderr.read()
        if proc.wait() or count != record['bytes'] or hashed.hexdigest() != record['sha256']:
            raise ValueError(f'Ext4 seed readback mismatch: {name}: {error!r}')
        record['ext4_file_readback_verified'] = True
        print('Ext4 file readback verified: ' + record['name'], flush=True)
    # 仅删除当前构建生成的回读临时文件
    if raw.resolve().parent != args.work.resolve() or raw.name != 'userdata-verification.raw.img':
        raise ValueError('Unexpected verification path')
    raw.unlink()
    report['ext4_features_compat'] = int.from_bytes(sb[92:96], 'little')
    report['ext4_features_incompat'] = int.from_bytes(sb[96:100], 'little')
    report['ext4_features_ro_compat'] = int.from_bytes(sb[100:104], 'little')
    report['userdata_readback_verified'] = True
    print('Building conservative 11 GiB super', flush=True)
    empty = args.work / 'empty-preload'
    empty.mkdir(exist_ok=True)
    placeholder = args.work / 'preload-placeholder.img'
    run(
        [
            args.tools / 'erofs-cygwin/mkfs.erofs.exe',
            '--all-root',
            cygpath(placeholder),
            cygpath(empty),
        ],
        args.work / 'empty-preload.log',
    )
    dlkm = args.work / 'vendor_dlkm.img'
    # 从已验证的原包保留小米内核模块分区
    with (args.original / 'images/super.img').open('rb') as source, dlkm.open('wb') as out:
        source.seek(17823744 * 512)
        data = source.read(41869312)
        if (
            len(data) != 41869312
            or data[1024:1028] != b'\xe2\xe1\xf5\xe0'
            or hashlib.sha256(data).hexdigest()
            != 'b617bef0e6faba021f02a032b67ae39b51b11c5a8d49ad76e3c865d67846bd3f'
        ):
            raise ValueError('Unexpected sheng vendor_dlkm source')
        out.write(data)
    sources = {
        'preload': placeholder,
        'system': args.donor / 'extracted/base/system.img',
        'sys_prod': args.donor / 'extracted/base/sys_prod.img',
        'vendor': args.donor / 'extracted/base/vendor.img',
        'vendor_dlkm': dlkm,
    }
    extraction = json.loads(
        (args.donor / 'extracted/base/extraction-report.json').read_text(encoding='utf-8')
    )
    for name in ['system', 'sys_prod', 'vendor']:
        record = next(c for c in extraction['components'] if c['name'] == name)
        if (
            not record['hash_verified']
            or not record['extracted']
            or digest(sources[name]) != record['sha256']
        ):
            raise ValueError('Unverified core image: ' + name)
    command = [
        args.tools / 'android-fs/lpmake.exe',
        '--metadata-size',
        '65536',
        '--metadata-slots',
        '3',
        '--device',
        f'super:{SUPER_BYTES}:1048576:0',
        '--group',
        f'qti_dynamic_partitions_a:{SUPER_BYTES}',
        '--group',
        f'qti_dynamic_partitions_b:{SUPER_BYTES}',
        '--sparse',
        '--output',
        cygpath(images / 'super.img'),
    ]
    for slot in ['a', 'b']:
        for name, path in sources.items():
            size = (path.stat().st_size + 4095) // 4096 * 4096 if slot == 'a' else 0
            command += ['--partition', f'{name}_{slot}:none:{size}:qti_dynamic_partitions_{slot}']
            if slot == 'a':
                command += ['--image', f'{name}_{slot}={cygpath(path)}']
    run(command, args.work / 'lpmake.log')
    sparse = SparseImage(images / 'super.img')
    layout = inspect_super(sparse)
    if sparse.size != SUPER_BYTES or layout['devices'][0]['bytes'] != SUPER_BYTES:
        raise ValueError('Super capacity mismatch')
    for partition in layout['partitions']:
        if partition['name'].endswith('_b'):
            if partition['bytes']:
                raise ValueError('Unexpected populated B slot')
            continue
        name = partition['name'][:-2]
        source = sources[name]
        if len(partition['extents']) != 1:
            raise ValueError('Expected a single sequential LP extent')
        start = partition['extents'][0][2] * 512
        actual = sparse.hash_range(start, source.stat().st_size)
        if actual != digest(source):
            raise ValueError('Super partition content mismatch: ' + name)
        partition['content_sha256'] = actual
        partition['content_readback_verified'] = True
        print('Super LP readback verified: ' + name, flush=True)
    sparse.close()
    (report_dir / 'super-layout.json').write_text(
        json.dumps(layout, indent=2) + '\n', encoding='utf-8'
    )
    for name, expected in BASE_HASHES.items():
        source = args.original / 'images' / name
        if digest(source) != expected:
            raise ValueError('Original bootchain hash mismatch: ' + name)
        shutil.copyfile(source, images / name)
    payload = json.loads(
        (args.donor / 'port-work/payload-integration-report.json').read_text(encoding='utf-8')
    )
    vb = args.donor / 'port-work/vendor_boot_promax_111sp12.img'
    if not payload['cpio_roundtrip_verified'] or digest(vb) != payload['vendor_boot_sha256']:
        raise ValueError('Unverified vendor_boot')
    shutil.copyfile(vb, images / 'vendor_boot.img')
    shutil.copyfile(
        args.donor / 'port-work/payload-integration-report.json',
        report_dir / 'payload-integration.json',
    )
    report['artifacts'] = [
        {'path': 'images/' + p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)}
        for p in sorted(images.iterdir())
    ]
    report['super_readback_verified'] = True
    report['build_unix_time'] = int(time.time())
    (report_dir / 'image-build.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8'
    )
    print('All seven images built and verified; no device was flashed.', flush=True)


if __name__ == '__main__':
    main()
