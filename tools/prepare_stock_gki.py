"""Run in WSL. Prepare an isolated ABI build from the exact 303 GKI source.

This does not build or flash a replacement kernel. Source repositories and
the user-provided ROMs are read-only except for a local .scmversion cache in
the newly fetched, isolated GKI directory. No commits or network writes.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess

workspace = Path(__file__).resolve().parent.parent
source = Path('/root/hmos-work/gki-5.15.178')
out = Path('/root/hmos-work/gki-out-stock')
compiler = Path('/root/hmos-work/clang-prebuilt/clang-r450784e/bin')
expected = '6f2f96be86b93de6ed58a2c46b456fb49734c382'
revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == expected, revision
version = subprocess.check_output([str(compiler / 'clang'), '--version'], text=True)
assert '14.0.7' in version and 'r450784e' in version, version
out.mkdir(exist_ok=True)
stock = (workspace / 'analysis/kernel.config').read_text()
config = out / '.config'
if config.exists():
    raise SystemExit('Existing build config: inspect it instead of overwriting this build.')
names = set()
buildconfig = (source / 'build.config.gki.aarch64').read_text()
lists = ['android/abi_gki_aarch64'] + re.findall(r'^android/abi_gki_aarch64_[A-Za-z0-9_]+$', buildconfig, re.M)
for name in lists:
    for line in (source / name).read_text().splitlines():
        symbol = line.split('#', 1)[0].strip()
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', symbol):
            names.add(symbol)
whitelist = out / 'abi_symbollist.raw'
whitelist.write_text('\n'.join(sorted(names)) + '\n')
prepared = re.sub(r'^CONFIG_UNUSED_KSYMS_WHITELIST=.*$', f'CONFIG_UNUSED_KSYMS_WHITELIST="{whitelist}"', stock, flags=re.M)
config.write_text(prepared)
# The source is shallow, so git describe cannot reconstruct the original count.
(source / '.scmversion').write_text('-android13-8-00021-g6f2f96be86b9\n')
env = os.environ.copy()
env['PATH'] = str(compiler) + ':' + env['PATH']
args = ['make', '-C', str(source), 'O=' + str(out), 'ARCH=arm64', 'LLVM=1',
        'LLVM_IAS=1', 'CROSS_COMPILE=aarch64-linux-gnu-',
        'KCFLAGS=-D__ANDROID_COMMON_KERNEL__', 'BUILD_NUMBER=13729987']
subprocess.run(args + ['olddefconfig'], env=env, check=True)
release = subprocess.check_output(args + ['-s', 'kernelrelease'], env=env, text=True).strip()
assert release == '5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987', release
before, after = set(prepared.splitlines()), set(config.read_text().splitlines())
report = {'source_commit': revision, 'toolchain': version, 'kernelrelease': release,
          'stock_config_sha256': hashlib.sha256(stock.encode()).hexdigest(),
          'whitelist_files': lists, 'whitelist_symbols': len(names),
          'olddefconfig_removed': sorted(before - after),
          'olddefconfig_added': sorted(after - before),
          'scope': 'ABI preparation only; kernel image not flashed'}
(workspace / 'analysis/stock-gki-abi-preparation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
