#!/usr/bin/env python3
"""Build the retained WSI/GLES regressions; does not execute them on a device."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--scratch', type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(BASE.parent / 'tools'))
    import build_adapter as adapter
    args.output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {}
    with tempfile.TemporaryDirectory(prefix='anyharmonyos-wsi-', dir=args.scratch) as folder:
        work = Path(folder)
        for source, name, inc in [('fullscreen.vert', 'vertex_spv', 'vertex.inc'),
                                  ('solid.frag', 'fragment_spv', 'fragment.inc')]:
            subprocess.run(['glslangValidator', '-V', '--vn', name, '-o', str(work / inc),
                            str(BASE / 'src' / source)], check=True)
        for source, name in [('swapchain_import_contract.cpp', 'swapchain_import_contract'),
                             ('egl_contract.cpp', 'egl_contract')]:
            subprocess.run(adapter.COMMON + ['-I' + str(work), '-I' + str(BASE / 'src'),
                           str(BASE / 'src' / source), str(adapter.CPP), '-o', str(work / name)], check=True)
            raw = (work / name).read_bytes()
            if raw[:6] != b'\x7fELF\x02\x01' or int.from_bytes(raw[18:20], 'little') != 183:
                raise ValueError('Invalid AArch64 ELF: ' + name)
            output = args.output_dir / name
            with output.open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if output.read_bytes() != raw:
                raise ValueError('Copy verification failed: ' + name)
            manifest[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    (args.output_dir / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
