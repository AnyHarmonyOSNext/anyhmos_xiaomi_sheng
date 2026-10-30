from pathlib import Path
import subprocess
import struct
import hashlib
import json

r = Path('/mnt/c/SHENG_WORKSPACE')
sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
out = r/'compat/debug-tools/native_video_decode_probe'
subprocess.run([str(sdk/'llvm/bin/clang'), '--target=aarch64-linux-ohos', '-O2', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(r/'tools/native_video_decode_probe.c'), '-o', str(out)], check=True)
subprocess.run([str(sdk/'llvm/bin/llvm-strip'), str(out)], check=True)
d = r/'work/video_decode_test'
d.mkdir(exist_ok=True)
subprocess.run(['/usr/bin/ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=64x64:rate=30', '-frames:v', '12', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-bf', '0', '-x264-params', 'aud=1:repeat-headers=1:keyint=12', '-f', 'h264', str(d/'test.h264')], check=True)
b = (d/'test.h264').read_bytes()
starts = []
i = 0
while i < len(b)-4:
    prefix = 4 if b[i:i+4] == b'\0\0\0\1' else 3 if b[i:i+3] == b'\0\0\1' else 0
    if prefix:
        if b[i+prefix] & 31 == 9:
            starts.append(i)
        i += prefix
    else:
        i += 1
assert len(starts) == 12 and starts[0] == 0
ends = starts[1:] + [len(b)]
packets = [b[a:z] for a,z in zip(starts, ends)]
(d/'test-packets.bin').write_bytes(b''.join(struct.pack('<I',len(p))+p for p in packets))
subprocess.run(['/usr/bin/ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(d/'test.h264'), '-pix_fmt', 'nv12', '-f', 'rawvideo', str(d/'reference.nv12')], check=True)
subprocess.run(['/usr/bin/ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=64x64:rate=30', '-frames:v', '12', '-c:v', 'libx265', '-pix_fmt', 'yuv420p', '-bf', '0', '-x265-params', 'aud=1:repeat-headers=1:keyint=12:bframes=0:pools=1:frame-threads=1:log-level=error', '-f', 'hevc', str(d/'test.hevc')], check=True)
b = (d/'test.hevc').read_bytes()
starts = []
i = 0
while i < len(b)-4:
    prefix = 4 if b[i:i+4] == b'\0\0\0\1' else 3 if b[i:i+3] == b'\0\0\1' else 0
    if prefix:
        if (b[i+prefix] >> 1) & 63 == 35:
            starts.append(i)
        i += prefix
    else:
        i += 1
assert len(starts) == 12 and starts[0] == 0
packets = [b[a:z] for a,z in zip(starts, starts[1:] + [len(b)])]
(d/'hevc-packets.bin').write_bytes(b''.join(struct.pack('<I',len(p))+p for p in packets))
subprocess.run(['/usr/bin/ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(d/'test.hevc'), '-pix_fmt', 'nv12', '-f', 'rawvideo', str(d/'reference-hevc.nv12')], check=True)
files = [out, d/'test.h264', d/'test-packets.bin', d/'reference.nv12', d/'test.hevc', d/'hevc-packets.bin', d/'reference-hevc.nv12']
manifest = {str(p.relative_to(r)): {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
(r/'analysis/video-decode-test-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps(manifest, indent=2))
