"""Build a private copy of AnyHarmonyOS's software backend; never edit its repo."""
from pathlib import Path
import shutil,subprocess,tarfile,os,json
r=Path('/mnt/c/SHENG_WORKSPACE')
reference=Path('/root/hmos-reference/AnyHarmonyOS/sm8650/bringup/useriam-port')
d=Path('/root/hmos-work/sheng-useriam-port')
if not d.exists():shutil.copytree(reference,d)
link=d/'donor';link.mkdir(exist_ok=True)
with tarfile.open(r/'work/useriam-original-link.tar.gz') as tar:
 for item in tar.getmembers():
  assert item.isfile() and '..' not in Path(item.name).parts and not item.name.startswith('/')
  p=link/item.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tar.extractfile(item).read())
openssl=d/'openssl-include'
if not openssl.exists():
 shutil.copytree('/usr/include/openssl',openssl/'openssl')
 for p in Path('/usr/include/x86_64-linux-gnu/openssl').glob('*.h'):shutil.copy2(p,openssl/'openssl'/p.name)
builder=d/'build.py';s=builder.read_text()
s=s.replace("str(R/'graphics-port/tests/platform_cpp_config.h')","'/root/hmos-work/graphics-deps/sheng-graphics-port/tests/platform_cpp_config.h'")
s=s.replace("'-ldl','-o'", "'-ldl','-Wl,--allow-shlib-undefined','-o'")
builder.write_text(s)
env=os.environ.copy();env.update(
 ANYHARMONYOS_OHOS_SOURCE='/root/hmos-work/graphics-deps/source',
 ANYHARMONYOS_SDK=json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'],
 ANYHARMONYOS_OPENSSL_INCLUDE=str(openssl),
 ANYHARMONYOS_ROM_SYSTEM_LIBS=str(r/'work/donor-hdi-link'),
 ANYHARMONYOS_ROM_VENDOR_LIBS=str(link/'vendor/lib64'))
# The reference contract additionally links the original 4.0 proxy.
proxy=r/'work/donor-hdi-link/libuser_auth_proxy_4.0.z.so'
if not proxy.exists():shutil.copy2(link/'system/lib64'/proxy.name,proxy)
subprocess.run(['python3',str(builder)],check=True,env=env)
