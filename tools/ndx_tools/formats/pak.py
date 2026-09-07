import itertools
import struct
from typing import Self

from ndx_tools.utils.fileio import FileIO


class Pak:
    def __init__(self) -> None:
        self.type = -1
        self.align = False
        self.files: list[bytes] = []

    @classmethod
    def from_path(cls, path, type: int) -> Self:
        with FileIO(path) as f:
            self = cls()
            if type != -1:
                self.type = type

            file_amount = f.read_uint32()
            self.files = []
            blobs: list[bytes] = []
            offsets: list[int] = []
            sizes: list[int] = []

            # Pak0
            if type == 0:
                for _ in range(file_amount):
                    sizes.append(f.read_uint32())

                for size in sizes:
                    blobs.append(f.read(size))

            # Pak1
            elif type == 1:
                for _ in range(file_amount):
                    offsets.append(f.read_uint32())
                    sizes.append(f.read_uint32())

                for offset, size in zip(offsets, sizes):
                    f.seek(offset)
                    blobs.append(f.read(size))
            # Pak3
            elif type == 3:
                for _ in range(file_amount):
                    offsets.append(f.read_uint32())
                f.seek(0, 2)
                offsets.append(f.tell())
                for i, j in itertools.pairwise(offsets):
                    sizes.append(j - i)
                for offset, size in zip(offsets, sizes):
                    f.seek(offset)
                    blobs.append(f.read(size))

            for off in offsets:
                if off % 0x10 == 0:
                    self.align = True
                break

        for blob in blobs:
            self.files.append(blob)

        return self

    @staticmethod
    def get_pak_type(data: bytes) -> int | None:
        is_aligned = False

        data_size = len(data)
        if data_size < 0x8:
            return None

        files = struct.unpack("<I", data[:4])[0]
        first_entry = struct.unpack("<I", data[4:8])[0]

        # Expectations
        pak1_header_size = 4 + (files * 8)
        pak3_header_size = 4 + (files * 4)

        # Check for alignment
        if first_entry % 0x10 == 0:
            is_aligned = True

        if pak1_header_size % 0x10 != 0:
            pak1_check = pak1_header_size + (0x10 - (pak1_header_size % 0x10))
        else:
            pak1_check = pak1_header_size

        # First test pak0
        # (pak0 can't be aligned, so header size
        # would be the same as unaligned pak3)
        if len(data) > pak3_header_size:
            calculated_size = 0
            for size in struct.unpack(f"<{files}I", data[4 : (files + 1) * 4]):
                calculated_size += size
            if calculated_size == len(data) - pak3_header_size:
                return 0

        # Test for pak1
        if is_aligned:
            if pak1_check == first_entry:
                return 1
        elif pak1_header_size == first_entry:
            return 1

        # Test for pak3
        previous = 0
        for offset in struct.unpack(f"<{files}I", data[4 : (files + 1) * 4]):
            if offset > previous and offset >= pak3_header_size:
                previous = offset
            else:
                return None

        last_offset = (4 * (files + 1)) + 8
        if data[last_offset:first_entry] == b"\x00" * (first_entry - last_offset):
            return 3
        return None

    def to_bytes(self, type=-1) -> bytes:
        compose_mode = type if type != -1 else self.type
        if compose_mode == -1:
            raise ValueError("Trying to compose an invalid PAK type")

        # Collect blobs
        blobs = self.files.copy()

        # Compose
        out = struct.pack("<I", len(self.files))

        # Pak0
        if compose_mode == 0:
            for blob in blobs:
                out += struct.pack("<I", len(blob))
        # Pak1
        elif compose_mode == 1:
            offset = 4 + (8 * len(blobs))
            sizes = [0] + [len(x) for x in blobs]
            if self.align:
                offset = (offset + 0xF) & ~0xF

            for i, j in itertools.pairwise(sizes):
                if self.align:
                    i = (i + 0xF) & ~0xF
                out += struct.pack("<I", offset + i)
                out += struct.pack("<I", j)
                offset += i
        # Pak3
        elif compose_mode == 3:
            offset = 4 + (4 * len(blobs))
            if self.align:
                offset = (offset + 0xF) & ~0xF

            cur = offset
            for blob in blobs:
                out += struct.pack("<I", cur)
                cur += len(blob)
                if self.align:
                    cur = (cur + 0xF) & ~0xF

        # add files
        for blob in blobs:
            if self.align:
                out += b"\x00" * (((len(out) + 0xF) & ~0xF) - len(out))
            out += blob

        return out

    def replace_tss(self, tss_data: bytes):

        for file in self.files:
            if file[0:3] == b"TSS":
                file = tss_data
                break

    def __getitem__(self, item):
        return self.files[item]

    def __len__(self):
        return len(self.files)
