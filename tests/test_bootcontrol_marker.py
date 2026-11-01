"""Exercise the actual launcher pattern against both authoritative helper paths."""

from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MarkerTests(unittest.TestCase):
    def test_verified_paths_and_rejected_states(self):
        source = (ROOT / 'runtime/compat/graphics/mark-boot-success-v135.sh').read_text(
            encoding='utf-8'
        )
        pattern = re.search(r"grep -Eq '([^']+)'", source).group(1)
        bash = shutil.which('bash') or r'C:\Program Files\Git\bin\bash.exe'
        cases = {
            'SCREENLOCK_VERIFIED after=0 already_unlocked=1': True,
            'SCREENLOCK_VERIFIED after=0 callback=0 elapsed=1': True,
            'SCREENLOCK_VERIFIED after=0 callback=0 elapsed=24': True,
            'SCREENLOCK_VERIFIED after=0 callback=0': True,
            'SCREENLOCK_VERIFIED after=0 callback=-999 elapsed=1': True,
            'SCREENLOCK_VERIFIED after=1 already_unlocked=1': False,
            'SCREENLOCK_VERIFIED after=0 already_unlocked=0': False,
            'SCREENLOCK_VERIFIED after=0 callback=bad elapsed=1': False,
            'SCREENLOCK_VERIFIED after=0 callback=0 elapsed=bad': False,
            'untrusted SCREENLOCK_VERIFIED after=0 already_unlocked=1': False,
        }
        for line, expected in cases.items():
            with self.subTest(line=line):
                result = subprocess.run(
                    [bash, '-c', 'grep -Eq "$1"', 'marker-test', pattern],
                    input=line + '\n',
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode == 0, expected, result.stderr)


if __name__ == '__main__':
    unittest.main()
