"""Fetch pinned public header sources outside the read-only reference checkout.

Run with WSL Python. No commits, pushes, vendor payloads or SDK in any repo.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess

reference = Path('/root/hmos-reference/AnyHarmonyOS')
destination = Path('/root/hmos-work/graphics-deps/source')
destination.mkdir(parents=True, exist_ok=True)
names = {'drivers_hdf_core', 'drivers_peripheral', 'drivers_interface', 'hiviewdfx_hilog', 'bounds_checking_function', 'commonlibrary_c_utils', 'communication_ipc'}
sources = [item for item in json.loads((reference/'docs/upstream-dependencies.json').read_text()) if item['name'] in names]

def fetch(item):
    path = destination/item['name']
    if path.exists():
        head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        if head != item['commit']:
            raise RuntimeError(f'Existing source differs: {path}')
        return {'name': item['name'], 'commit': head, 'reused': True}
    subprocess.run(['git', 'init', '-q', str(path)], check=True)
    subprocess.run(['git', '-C', str(path), 'remote', 'add', 'origin', item['origin']], check=True)
    subprocess.run(['git', '-C', str(path), 'fetch', '-q', '--depth=1', 'origin', item['commit']], check=True)
    subprocess.run(['git', '-C', str(path), 'checkout', '-q', '--detach', 'FETCH_HEAD'], check=True)
    return {'name': item['name'], 'commit': item['commit'], 'origin': item['origin']}

with ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(fetch, sources))
Path('/root/hmos-work/graphics-deps/sources.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
