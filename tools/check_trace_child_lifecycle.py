"""Compare the saved v71 tracer and the fix using the same 96-child workload."""
from pathlib import Path
import subprocess,json
r=Path('/mnt/c/SHENG_WORKSPACE')
d=Path('/root/hmos-work/desktop-debug')
new=(r/'tools/hmos_probe.c').read_text()
old=(r/'tools/archive/hmos_probe_v71.c').read_text()
a=new.index('static int trace_selftest(');b=new.index('static void trace_handoff(',a)
c=old.index('static int trace_selftest(');e=old.index('static void trace_handoff(',c)
old=old[:c]+new[a:b]+old[e:]
old=old.replace('trace_selftest(0);','trace_selftest(0,0);').replace('trace_selftest(1);','trace_selftest(1,0);')
old=old.replace('if(argc==2&&!strcmp(argv[1],"--ptrace-selftest"))',
 'if(argc==2&&!strcmp(argv[1],"--ptrace-stress-selftest"))return trace_selftest(1,1);\n    if(argc==2&&!strcmp(argv[1],"--ptrace-selftest"))')
report={}
for name,source in [('v71-baseline',old),('lifecycle-fix',new)]:
 p=d/(name+'.c');p.write_text(source)
 # Includes are copied only into this isolated host-test directory.
 for header in ['probe_graphics.inc','probe_command.inc']:(d/header).write_bytes((r/'tools'/header).read_bytes())
 exe=d/(name+'-test')
 subprocess.run(['gcc','-O2','-Wall','-Wextra','-Wno-unused-function',str(p),'-o',str(exe)],check=True)
 with (d/(name+'.log')).open('w') as log:
  result=subprocess.run(['timeout','12',str(exe),'--ptrace-stress-selftest'],stdout=log,stderr=log)
 report[name]={'exit':result.returncode,'log':str(d/(name+'.log'))}
(r/'analysis/ptrace-child-lifecycle.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
assert report['lifecycle-fix']['exit']==0
