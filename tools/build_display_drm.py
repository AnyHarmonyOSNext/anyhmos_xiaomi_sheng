"""Build the libdrm core used by the display compatibility layer."""

from pathlib import Path
import argparse
import hashlib
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    build = output / 'drm-build'
    build.mkdir(exist_ok=True)
    suffix = '.exe' if sys.platform == 'win32' else ''
    tools = args.sdk / 'llvm/bin'
    compiler = tools / ('clang' + suffix)
    # 仅启用 Linux 核心接口，设备号通过系统宏解析
    config = build / 'config.h'
    config.write_text(
        '#define MAJOR_IN_SYSMACROS 1\n'
        '#define HAVE_LIBDRM_ATOMIC_PRIMITIVES 1\n'
        '#define HAVE_SYS_SYSCTL_H 0\n'
        '#define UDEV 0\n'
        '#define HAVE_LIB_ATOMIC_OPS 0\n'
        '#define HAVE_VISIBILITY 1\n'
        '#define HAVE_OPEN_MEMSTREAM 1\n',
        encoding='utf-8',
    )
    subprocess.run(
        [
            sys.executable,
            str(source / 'gen_table_fourcc.py'),
            str(source / 'include/drm/drm_fourcc.h'),
            str(build / 'generated_static_table_fourcc.h'),
        ],
        check=True,
    )
    objects = []
    for name in ('xf86drm', 'xf86drmHash', 'xf86drmRandom', 'xf86drmSL', 'xf86drmMode'):
        target = build / (name + '.o')
        subprocess.run(
            [
                str(compiler),
                '--target=aarch64-linux-ohos',
                '-O2',
                '-fPIC',
                '-D_GNU_SOURCE',
                '-Werror=implicit-function-declaration',
                '-include',
                str(config),
                '-I' + str(build),
                '-I' + str(source),
                '-I' + str(source / 'include/drm'),
                '-c',
                str(source / (name + '.c')),
                '-o',
                str(target),
            ],
            check=True,
        )
        objects.append(str(target))
    library = output / 'lib/libdrm.a'
    library.parent.mkdir(exist_ok=True)
    # 新建归档后原子替换，避免残留旧构建成员
    archive = build / 'libdrm-new.a'
    archive.unlink(missing_ok=True)
    subprocess.run([str(tools / ('llvm-ar' + suffix)), 'rcs', str(archive), *objects], check=True)
    archive.replace(library)
    # 安装编译时使用的同一组 DRM 头文件
    include = output / 'include'
    (include / 'libdrm').mkdir(parents=True, exist_ok=True)
    for header in (source / 'include/drm').glob('*.h'):
        shutil.copyfile(header, include / 'libdrm' / header.name)
    for name in ('xf86drm.h', 'xf86drmMode.h'):
        shutil.copyfile(source / name, include / name)
    print(hashlib.sha256(library.read_bytes()).hexdigest(), library)


if __name__ == '__main__':
    main()
