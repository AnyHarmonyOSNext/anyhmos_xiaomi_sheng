"""Promote a reviewed round note to the four continuation documents."""
from pathlib import Path
import sys

r = Path(__file__).resolve().parent.parent
p = Path(sys.argv[1]).resolve()
assert p.is_relative_to(r / 'analysis')
body = p.read_text(encoding='utf-8').strip() + '\n'
assert body.startswith('## ')
for name in ['analysis/续接检查点.md', 'analysis/轮次总结.md', 'analysis/20261027续接进展.md']:
    dest = r / name
    old = dest.read_text(encoding='utf-8')
    if not old.startswith(body):
        dest.write_text(body + '\n' + old, encoding='utf-8')
(r / '当前状态.md').write_text('# 当前移植状态\n\n' + body, encoding='utf-8')
print(body.splitlines()[0])
