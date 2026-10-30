"""Export project-owned WSL sources and upstream provenance without build blobs."""
from pathlib import Path
import json
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=False)
extensions = {'.c', '.cc', '.cpp', '.h', '.hpp', '.S', '.inc', '.py', '.sh',
              '.cfg', '.hcs', '.json', '.md', '.patch', '.diff', '.mk', '.cmake',
              '.ini', '.map', '.yaml', '.yml', '.toml', '.config', '.gn', '.gni',
              '.idl', '.def', '.lds', '.dts', '.dtsi', '.cmake'}
names = {'Makefile', 'Kbuild', 'Kconfig', 'CMakeLists.txt', 'meson.build',
         'meson_options.txt', 'LICENSE', 'COPYING', 'NOTICE', 'README', 'VERSION'}
skip = {'.git', '__pycache__', 'out', 'build', 'node_modules', '.venv'}

def source_file(path):
    return (path.suffix in extensions or path.name in names or
            path.name.startswith(('LICENSE', 'COPYING', 'NOTICE'))) and \
        path.is_file() and not path.is_symlink() and b'\0' not in path.read_bytes()[:8192]

def copy_sources(root, target):
    count = 0
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in skip for part in relative.parts) or not source_file(path):
            continue
        out = target/relative
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(path.read_bytes())
        count += 1
    return count

custom = [Path('/root/hmos-work')/name for name in (
    'sheng-hmos-ipc', 'sheng-hmos-ipc-exports', 'sheng-firmware-contract',
    'sheng-useriam-port', 'sheng-display-dsc', 'sheng-ipc-tests')]
custom.append(Path('/root/hmos-work/graphics-deps/sheng-graphics-port'))
copied = {root.name: copy_sources(root, destination/'custom'/root.name)
          for root in custom if root.is_dir()}

def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout

roots = sorted(Path('/root/hmos-reference').glob('*/.git'))
roots += sorted(Path('/root/hmos-work/graphics-deps/source').glob('*/.git'))
roots += sorted(Path('/root/hmos-work/desktop-debug').glob('*/.git'))
roots += sorted(Path('/root/hmos-work/brightness-reference').glob('*/.git'))
roots += [Path('/root/hmos-work/gki-5.15.178/.git'),
          Path('/root/hmos-work/gki-sheng-exports/.git')]
manifest = []
for marker in roots:
    root = marker.parent
    if not marker.exists():
        continue
    group = root.parent.name
    key = group+'--'+root.name
    try:
        head = git(root, 'rev-parse', 'HEAD').decode().strip()
        url = git(root, 'remote', 'get-url', 'origin').decode().strip()
        if '://' in url:
            parsed = urlsplit(url)
            url = urlunsplit((parsed.scheme, parsed.netloc.split('@')[-1], parsed.path, '', ''))
        elif '@' in url:
            url = url.split('@', 1)[1]
        status = git(root, 'status', '--porcelain').decode(errors='replace')
        patch = git(root, 'diff', 'HEAD', '--no-ext-diff', '--no-color')
        item = dict(name=key, origin=url, commit=head,
                    worktree_dirty=bool(status), patch_bytes=len(patch))
        if patch:
            out = destination/'patches'/(key+'.patch')
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(patch)
            item['patch'] = str(out.relative_to(destination))
        untracked = git(root, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
        count = 0
        for raw in untracked:
            if not raw:
                continue
            relative = Path(raw.decode())
            path = root/relative
            if any(part in skip for part in relative.parts) or not source_file(path):
                continue
            out = destination/'overlays'/key/relative
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(path.read_bytes())
            count += 1
        item['untracked_source_files'] = count
        for path in root.iterdir():
            if path.is_file() and path.name.startswith(('LICENSE', 'COPYING', 'NOTICE')):
                out = destination/'licenses'/key/path.name
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(path.read_bytes())
        manifest.append(item)
    except subprocess.CalledProcessError as error:
        raise RuntimeError('Cannot record upstream '+key) from error

# Dependency pin lists belong with the WSL source snapshot, not its binaries.
for root in [Path('/root/hmos-work/graphics-deps')]:
    for path in root.glob('*.json'):
        out = destination/'dependency-records'/path.name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(path.read_bytes())
(destination/'upstream-sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
(destination/'custom-sources.json').write_text(json.dumps(copied, indent=2)+'\n')
print(json.dumps(dict(custom=copied, upstreams=len(manifest),
                      patches=sum(bool(item['patch_bytes']) for item in manifest)), indent=2))
