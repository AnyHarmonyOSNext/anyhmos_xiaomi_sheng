import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'audit_donor', Path(__file__).resolve().parents[1] / 'tools/audit_donor.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DonorAuditTests(unittest.TestCase):
    def test_duplicate_library_names_are_checked_individually(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            donor = base / 'donor'
            recipes = base / 'recipes'
            recipes.mkdir()
            for partition, data in [('system', b'original'), ('vendor', b'changed')]:
                (donor / partition).mkdir(parents=True)
                (donor / partition / 'libtest.so').write_bytes(data)
            recipe = {
                'name': 'libtest.so',
                'input_sha256': hashlib.sha256(b'original').hexdigest(),
                'output_sha256': hashlib.sha256(b'patched').hexdigest(),
            }
            (recipes / 'test.json').write_text(json.dumps(recipe), encoding='utf-8')
            report = module.audit(donor.resolve(), recipes)
            results = report['existing_patch_input_checks'][0]['candidates']
            self.assertEqual(
                results,
                [
                    {'path': 'system/libtest.so', 'status': 'input_hash_matched'},
                    {'path': 'vendor/libtest.so', 'status': 'different_input_requires_review'},
                ],
            )
            self.assertEqual((donor / 'vendor/libtest.so').read_bytes(), b'changed')

    def test_missing_and_already_patched_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            donor, recipes = base / 'donor', base / 'recipes'
            donor.mkdir()
            recipes.mkdir()
            (donor / 'present.so').write_bytes(b'patched')
            for name in ('missing.so', 'present.so'):
                (recipes / (name + '.json')).write_text(
                    json.dumps(
                        {
                            'name': name,
                            'input_sha256': '0' * 64,
                            'output_sha256': hashlib.sha256(b'patched').hexdigest(),
                        }
                    ),
                    encoding='utf-8',
                )
            checks = module.audit(donor.resolve(), recipes)['existing_patch_input_checks']
            self.assertEqual(checks[0]['status'], 'missing')
            self.assertEqual(checks[1]['candidates'][0]['status'], 'already_patched')

    def test_elf_machine_and_streamed_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'aarch64.so'
            data = bytearray(2 * 1024 * 1024 + 21)
            data[:6] = b'\x7fELF\x02\x01'
            struct.pack_into('<H', data, 18, 183)
            path.write_bytes(data)
            record = module.fingerprint(path)
            self.assertEqual(record['elf'], {'class': 2, 'byte_order': 1, 'machine': 183})
            self.assertEqual(record['sha256'], hashlib.sha256(data).hexdigest())

    def test_truncated_elf_does_not_claim_an_architecture(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.so'
            path.write_bytes(b'\x7fELF')
            self.assertNotIn('machine', module.fingerprint(path)['elf'])


if __name__ == '__main__':
    unittest.main()
