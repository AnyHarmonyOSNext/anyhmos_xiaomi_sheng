from pathlib import Path
import hashlib,subprocess
r=Path(__file__).resolve().parent.parent
p=r/'compat/debug-tools/input_latency_monitor'
subprocess.run(['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(r/'tools/input_latency_monitor.c'),'-o',str(p)],check=True)
subprocess.run(['aarch64-linux-gnu-strip',str(p)],check=True)
print(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
