import pathlib
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from android_sparse import SparseImage


class SparseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.directory.name) / 'image.img'

    def tearDown(self):
        self.directory.cleanup()

    def write(self, chunks, blocks=3):
        self.path.write_bytes(
            struct.pack('<IHHHHIIII', 0xED26FF3A, 1, 0, 28, 12, 4096, blocks, len(chunks), 0)
            + b''.join(chunks)
        )

    def test_cross_chunk_reads_and_fill_phase(self):
        self.write(
            [
                struct.pack('<HHII', 0xCAC1, 0, 1, 4108) + b'a' * 4096,
                struct.pack('<HHII', 0xCAC2, 0, 1, 16) + b'abcd',
                struct.pack('<HHII', 0xCAC3, 0, 1, 12),
            ]
        )
        image = SparseImage(self.path)
        try:
            self.assertEqual(image.read_at(4094, 8), b'aaabcdab')
            self.assertEqual(image.read_at(4097, 5), b'bcdab')
            self.assertEqual(image.read_at(8190, 5), b'cd\0\0\0')
            with self.assertRaises(ValueError):
                image.read_at(12288, 1)
        finally:
            image.close()

    def test_rejects_truncated_raw_payload(self):
        self.write([struct.pack('<HHII', 0xCAC1, 0, 3, 12300) + b'a'])
        with self.assertRaises(ValueError):
            SparseImage(self.path)

    def test_rejects_inconsistent_expanded_size(self):
        self.write([struct.pack('<HHII', 0xCAC3, 0, 2, 12)])
        with self.assertRaises(ValueError):
            SparseImage(self.path)

    def test_rejects_invalid_chunk_shape(self):
        self.write([struct.pack('<HHII', 0xCAC2, 0, 3, 12)])
        with self.assertRaises(ValueError):
            SparseImage(self.path)


if __name__ == '__main__':
    unittest.main()
