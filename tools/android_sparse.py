"""Read Android sparse images without allocating their expanded size."""

from __future__ import annotations

import bisect
import hashlib
import os
from pathlib import Path
import struct


class SparseImage:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.file = self.path.open('rb')
        try:
            self._parse()
        except BaseException:
            self.file.close()
            raise

    # 校验稀疏块布局并记录逻辑地址映射
    def _parse(self):
        self.chunks = []
        header = self.file.read(28)
        if len(header) != 28:
            raise ValueError('Short sparse header')
        magic, major, minor, fh, ch, block, blocks, count, crc = struct.unpack('<IHHHHIIII', header)
        if magic != 0xED26FF3A or major != 1 or fh < 28 or ch < 12 or not block or block % 4:
            raise ValueError('Unsupported sparse header')
        self.block_size = block
        self.size = blocks * block
        self.file.seek(fh)
        logical = 0
        for _ in range(count):
            chunk = self.file.read(ch)
            if len(chunk) != ch:
                raise ValueError('Short chunk header')
            kind, reserved, nblocks, total = struct.unpack_from('<HHII', chunk)
            length = nblocks * block
            payload = total - ch
            offset = self.file.tell()
            if kind == 0xCAC1 and payload == length:
                value = offset
            elif kind == 0xCAC2 and payload == 4:
                value = self.file.read(4)
            elif kind == 0xCAC3 and payload == 0:
                value = None
            elif kind == 0xCAC4 and payload == 4 and nblocks == 0:
                self.file.seek(offset + payload)
                continue
            else:
                raise ValueError('Invalid sparse chunk')
            if length:
                self.chunks.append((logical, logical + length, kind, value))
            logical += length
            self.file.seek(offset + payload)
        if logical != self.size or self.file.tell() != self.path.stat().st_size:
            raise ValueError('Sparse length mismatch')
        self.starts = [c[0] for c in self.chunks]

    def close(self):
        self.file.close()

    # 按逻辑地址读取原始块、填充块和空洞
    def read_at(self, offset: int, length: int) -> bytes:
        if offset < 0 or length < 0 or offset + length > self.size:
            raise ValueError('Read outside sparse image')
        output = bytearray()
        while length:
            i = bisect.bisect_right(self.starts, offset) - 1
            start, end, kind, value = self.chunks[i]
            take = min(length, end - offset)
            if kind == 0xCAC1:
                self.file.seek(value + offset - start)
                data = self.file.read(take)
                if len(data) != take:
                    raise ValueError('Truncated raw sparse chunk')
            elif kind == 0xCAC2:
                phase = (offset - start) % 4
                data = (value * ((take + phase + 3) // 4))[phase : phase + take]
            else:
                data = bytes(take)
            output.extend(data)
            offset += take
            length -= take
        return bytes(output)

    def hash_range(self, offset: int, length: int) -> str:
        digest = hashlib.sha256()
        while length:
            take = min(length, 4 * 1024 * 1024)
            digest.update(self.read_at(offset, take))
            offset += take
            length -= take
        return digest.hexdigest()

    # 仅写入有效数据，保留 NTFS 稀疏空洞
    def expand_ntfs_sparse(self, destination: Path):
        """Materialize only data ranges; Windows is required for sparse marking."""
        if os.name != 'nt':
            raise OSError('NTFS sparse expansion requires Windows')
        import ctypes
        import msvcrt

        with Path(destination).open('xb') as out:
            returned = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.DeviceIoControl(
                ctypes.c_void_p(msvcrt.get_osfhandle(out.fileno())),
                0x900C4,
                None,
                0,
                None,
                0,
                ctypes.byref(returned),
                None,
            )
            if not ok:
                raise OSError('Cannot mark verification file sparse')
            for start, end, kind, value in self.chunks:
                if kind == 0xCAC3 or kind == 0xCAC2 and value == bytes(4):
                    continue
                out.seek(start)
                for offset in range(start, end, 4 * 1024 * 1024):
                    out.write(self.read_at(offset, min(end - offset, 4 * 1024 * 1024)))
            out.truncate(self.size)


# 核对动态分区校验和、备份及映射边界
def inspect_super(image: SparseImage) -> dict:
    geometry = image.read_at(4096, 4096)
    if struct.unpack_from('<I', geometry)[0] != 0x616C4467:
        raise ValueError('Invalid LP geometry')
    size = struct.unpack_from('<I', geometry, 4)[0]
    checked = bytearray(geometry[:size])
    expected = checked[8:40]
    checked[8:40] = bytes(32)
    if hashlib.sha256(checked).digest() != expected:
        raise ValueError('LP geometry checksum mismatch')
    if geometry != image.read_at(8192, 4096):
        raise ValueError('LP geometry backup mismatch')
    maximum, slots, block = struct.unpack_from('<III', geometry, 40)
    metadata = image.read_at(12288, maximum)
    header_size = struct.unpack_from('<I', metadata, 8)[0]
    table_size = struct.unpack_from('<I', metadata, 44)[0]
    if struct.unpack_from('<I', metadata)[0] != 0x414C5030:
        raise ValueError('Invalid LP metadata')
    header = bytearray(metadata[:header_size])
    expected = header[12:44]
    header[12:44] = bytes(32)
    if hashlib.sha256(header).digest() != expected:
        raise ValueError('LP metadata header checksum mismatch')
    table = metadata[header_size : header_size + table_size]
    if hashlib.sha256(table).digest() != metadata[48:80]:
        raise ValueError('LP metadata table checksum mismatch')
    for i in range(slots * 2):
        if metadata != image.read_at(12288 + i * maximum, maximum):
            raise ValueError('LP slot/backup metadata mismatch')

    def rows(position, fmt):
        offset, count, entry_size = struct.unpack_from('<III', metadata, position)
        if entry_size < struct.calcsize(fmt) or offset + count * entry_size > len(table):
            raise ValueError('LP table bounds invalid')
        return [struct.unpack_from(fmt, table, offset + i * entry_size) for i in range(count)]

    extents = rows(92, '<QIQI')
    partitions = []
    for name, attributes, first, count, group in rows(80, '<36sIIII'):
        spans = extents[first : first + count]
        if len(spans) != count:
            raise ValueError('LP extent index invalid')
        partitions.append(
            {
                'name': name.split(b'\0')[0].decode(),
                'attributes': attributes,
                'group': group,
                'bytes': sum(e[0] * 512 for e in spans),
                'extents': [list(e) for e in spans],
            }
        )
    groups = [
        {'name': n.split(b'\0')[0].decode(), 'flags': f, 'maximum': m}
        for n, f, m in rows(104, '<36sIQ')
    ]
    devices = [
        {
            'first_sector': s,
            'alignment': a,
            'alignment_offset': o,
            'bytes': z,
            'name': n.split(b'\0')[0].decode(),
            'flags': f,
        }
        for s, a, o, z, n, f in rows(116, '<QIIQ36sI')
    ]
    occupied = []
    for partition in partitions:
        for sectors, kind, start, source in partition['extents']:
            if kind != 0 or source != 0 or start < devices[0]['first_sector']:
                raise ValueError('Unexpected LP extent mapping')
            if (start + sectors) * 512 > devices[0]['bytes']:
                raise ValueError('LP extent exceeds device')
            occupied.append((start, start + sectors))
    occupied.sort()
    if any(a[1] > b[0] for a, b in zip(occupied, occupied[1:])):
        raise ValueError('Overlapping LP extents')
    for i, group in enumerate(groups):
        used = sum(p['bytes'] for p in partitions if p['group'] == i)
        if group['maximum'] and used > group['maximum']:
            raise ValueError('LP group capacity exceeded')
    return {
        'expanded_bytes': image.size,
        'metadata_max_size': maximum,
        'slots': slots,
        'block': block,
        'partitions': partitions,
        'groups': groups,
        'devices': devices,
        'checksums_and_backups_verified': True,
    }
