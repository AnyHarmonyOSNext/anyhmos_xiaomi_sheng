"""Apply one frozen graphics profile to Mesa ea74a6339917390657db153cb9792f9ccac9f5ae.

Use separate clean source trees for gallium-egl and turnip. Gallium requires
platforms=ohos, gallium-drivers=zink, vulkan-drivers='', shader-cache=disabled;
Turnip requires platforms='', gallium-drivers='', vulkan-drivers=freedreno,
freedreno-kmds=kgsl. Both use the OHOS AArch64 SDK, cpp_rtti=false and
femulated-tls. Pass dmabuf_sync/uapi as an include directory for Gallium.
The donor BufferHandle/display_type headers and surface/hilog/libc++ libraries
are external build inputs. This prepares sources; it does not deploy binaries.
"""

import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--profile', choices=('gallium-egl', 'turnip'), required=True)
    args = parser.parse_args()
    patch = Path(__file__).resolve().with_name('mesa-' + args.profile + '.patch')
    # 两套已验证构建使用独立源码树，避免混入其他试验分支
    command = ['git', '-C', str(args.source.resolve()), 'apply', str(patch)]
    subprocess.run(command[:4] + ['--check'] + command[4:], check=True)
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
