from pathlib import Path
import tarfile
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-framework/useriam-v1'
with tarfile.open(r/'work/useriam-contract-bundle.tar.gz','w:gz') as tar:
 for name in ['libsheng_userauth_4_0.so','libuser_auth_interface_service_4.1.z.so','useriam_empty_contract']:
  tar.add(d/name,arcname=name,recursive=False)
print((r/'work/useriam-contract-bundle.tar.gz').stat().st_size)
