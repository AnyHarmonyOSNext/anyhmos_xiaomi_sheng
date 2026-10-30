from pathlib import Path
import subprocess,tempfile,sys
B=Path(__file__).resolve().parent;sys.path.insert(0,str(B.parent/'tools'));import build_adapter as a
(B/"out").mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='native-render-') as td:
 d=Path(td)
 for source,name,inc in [('fullscreen.vert','vertex_spv','vertex.inc'),('solid.frag','fragment_spv','fragment.inc')]:
  subprocess.run(['glslangValidator','-V','--vn',name,'-o',str(d/inc),str(B/'src'/source)],check=True)
 subprocess.run(a.COMMON+['-I'+str(d),str(B/'src/native_buffer_contract.cpp'),str(a.CPP),'-o',str(d/'native_buffer_contract')],check=True)
 raw=(d/'native_buffer_contract').read_bytes();assert raw[:4]==b'\x7fELF';(B/'out/native_buffer_contract').write_bytes(raw);assert (B/'out/native_buffer_contract').read_bytes()==raw

with tempfile.TemporaryDirectory(prefix="rosen-gpu-") as td:
 d=Path(td);subprocess.run(a.COMMON+[str(B/"src/rosen_gpu_contract.cpp"),str(a.CPP),"-o",str(d/"rosen_gpu_contract")],check=True)
 raw=(d/"rosen_gpu_contract").read_bytes();assert raw[:4]==b"\x7fELF";(B/"out/rosen_gpu_contract").write_bytes(raw)

with tempfile.TemporaryDirectory(prefix='nv12-') as td:
 d=Path(td)
 for source,name,inc in [('fullscreen.vert','vertex_spv','vertex.inc'),('nv12.frag','fragment_spv','fragment.inc')]:
  subprocess.run(['glslangValidator','-V','--vn',name,'-o',str(d/inc),str(B/'src'/source)],check=True)
 subprocess.run(a.COMMON+['-DACE5_YUV_CONTRACT','-I'+str(d),str(B/'src/native_buffer_contract.cpp'),str(a.CPP),'-o',str(d/'native_yuv_contract')],check=True)
 raw=(d/'native_yuv_contract').read_bytes();assert raw[:4]==b'\x7fELF';(B/'out/native_yuv_contract').write_bytes(raw)

with tempfile.TemporaryDirectory(prefix='rosen-nv12-') as td:
 d=Path(td);name='rosen_yuv_contract';subprocess.run(a.COMMON+[str(B/'src'/(name+'.cpp')),str(a.CPP),'-o',str(d/name)],check=True)
 raw=(d/name).read_bytes();assert raw[:4]==b'\x7fELF';(B/'out'/name).write_bytes(raw);assert (B/'out'/name).read_bytes()==raw
