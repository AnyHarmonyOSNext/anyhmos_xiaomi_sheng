"""Compare steady windows; omit each first window which crosses a case boundary."""
from pathlib import Path
import gzip
import json
import re

r = Path(__file__).resolve().parent.parent
source = r / 'output/logs/v87-gpu-floor-cases.txt.gz'
cases = {}
case = None
skip = False
for line in gzip.decompress(source.read_bytes()).decode().splitlines():
    if line.startswith('GPU_FLOOR_CASE_BEGIN='):
        case = line.split('=')[1]
        cases[case] = {'windows': 0, 'frames': 0, 'commit_us_weighted': 0, 'gaps': [0]*8}
        skip = True
    elif line.startswith('GPU_FLOOR_CASE_END='):
        case = None
    elif case and ' submit frames=' in line:
        match = re.search(r'frames=(\d+).* commit=(\d+)', line)
        if not skip:
            frames, commit = map(int, match.groups())
            c = cases[case]
            c['windows'] += 1
            c['frames'] += frames
            c['commit_us_weighted'] += frames*commit
    elif case and ' FRAME_GAPS ' in line:
        if skip:
            skip = False
        else:
            counts = list(map(int, line.split('counts=')[1].split(',')))
            c = cases[case]
            c['gaps'] = [a+b for a,b in zip(c['gaps'], counts)]
for c in cases.values():
    c['mean_commit_us'] = round(c.pop('commit_us_weighted') / c['frames'])
    active = sum(c['gaps'][:7])
    c['active_gaps_le12ms_percent'] = round(sum(c['gaps'][:2])*100/active, 1)
    c['active_gaps_12to17ms_percent'] = round(c['gaps'][2]*100/active, 1)
result = {'source': str(source.relative_to(r)), 'omit_first_window_per_case': True,
          'idle_gaps_gt100ms_excluded_from_percent': True,
          'not_sustained_fps': True, 'cases': cases}
(r/'analysis/v87-gpu-floor-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
