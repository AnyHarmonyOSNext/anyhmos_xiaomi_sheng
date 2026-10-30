from pathlib import Path
import subprocess,json,struct
adb=str(Path('output/platform-tools/adb.exe').resolve());out=Path('analysis/device-before');out.mkdir(exist_ok=True)
for name,command in [('mounts','cat /proc/mounts'),('cmdline','cat /proc/cmdline'),('bootconfig','cat /proc/bootconfig'),('metadata','blkid /dev/block/by-name/metadata'),('partition-links','ls -l /dev/block/by-name'),('recovery-dmesg','dmesg')]:
 r=subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','shell',command],capture_output=True);(out/f'{name}.txt').write_bytes(r.stdout+r.stderr)
 if name in ['metadata','cmdline']: print(name,r.stdout.decode(errors='replace')[:3000])
for part,bs,count,filename in [('super',4096,99,'actual-super-metadata.raw'),('vbmeta_a',8192,1,'vbmeta_a.img'),('vbmeta_system_a',4096,1,'vbmeta_system_a.img')]:
 tmp='/tmp/hmos-'+filename;r=subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','shell',f'dd if=/dev/block/by-name/{part} of={tmp} bs={bs} count={count}'],capture_output=True);print(part,'dd',r.returncode)
 if r.returncode==0:
  subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','pull',tmp,str(out/filename)],check=True,capture_output=True)
  subprocess.run([adb,'-s','YOUR_DEVICE_SERIAL','shell',f'rm -f {tmp}'],check=True,capture_output=True)
  if part.startswith('vbmeta'):
   b=(out/filename).read_bytes();print(part,b[:4], 'flags', struct.unpack_from('>I',b,120)[0] if b[:4]==b'AVB0' else 'unknown')
