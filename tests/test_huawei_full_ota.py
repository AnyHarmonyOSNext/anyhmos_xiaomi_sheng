import hashlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location(
    'extract_huawei_full_ota',
    Path(__file__).resolve().parents[1] / 'tools/extract_huawei_full_ota.py',
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def payload(content=b'partition', name=b'/system', declared_size=None, digest=None):
    record = bytearray(87)
    record[: len(name)] = name
    struct.pack_into('<Q', record, 47, len(content) if declared_size is None else declared_size)
    record[55:87] = hashlib.sha256(content).digest() if digest is None else digest
    header = bytearray(180)
    struct.pack_into('<H', header, 0, 1)
    struct.pack_into('<HH', header, 176, 5, 87)
    return bytes(header) + record + bytes(16) + struct.pack('<HI', 8, 0) + content


def archive(path, data, full=True):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as target:
        target.writestr('packageinfo.mbn', 'deviceModel=TEST\n')
        target.writestr('VERSION.mbn', 'TEST-VERSION')
        target.writestr('update.tag', 'PKG_DATA_TYPE=' + ('FULL' if full else 'DIFF'))
        target.writestr('update.bin', data)


class HuaweiFullOtaTests(unittest.TestCase):
    def test_stream_extraction_and_crc(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'test.zip'
            archive(source, payload())
            before = source.read_bytes()
            report = module.extract(source, root / 'output', {'system'})
            self.assertEqual((root / 'output/system.img').read_bytes(), b'partition')
            self.assertEqual(source.read_bytes(), before)
            self.assertTrue(report['zip_crc_verified'])
            self.assertFalse(report['signature_verified'])

    def test_bad_component_hash_never_promotes_image(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'test.zip'
            archive(source, payload(digest=bytes(32)))
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                module.extract(source, root / 'output', {'system'})
            self.assertFalse((root / 'output/system.img').exists())
            self.assertFalse((root / 'output/extraction-report.json').exists())

    def test_large_component_uses_64_bit_size(self):
        size = 2**32 + 12345
        stream = io.BytesIO(payload(content=b'', declared_size=size))
        records = module.header(stream, len(stream.getvalue()) + size)
        self.assertEqual(records[0]['bytes'], size)

    def test_rejects_unsafe_component_path(self):
        raw = payload(name=b'/../system')
        with self.assertRaisesRegex(ValueError, 'component name'):
            module.header(io.BytesIO(raw), len(raw))

    def test_rejects_mismatched_container_lengths(self):
        raw = payload(declared_size=10000)
        with self.assertRaisesRegex(ValueError, 'lengths'):
            module.header(io.BytesIO(raw), len(raw))

    def test_rejects_diff_package_before_writing_images(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'test.zip'
            archive(source, payload(), full=False)
            with self.assertRaisesRegex(ValueError, 'full OTA'):
                module.extract(source, root / 'output', {'system'})
            self.assertFalse((root / 'output/system.img.part').exists())


if __name__ == '__main__':
    unittest.main()
