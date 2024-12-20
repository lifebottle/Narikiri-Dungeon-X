import io
import struct
from io import BytesIO
from pathlib import Path
from typing import Union


class FileIO(object):
    def __init__(self, path: Union[Path, str, BytesIO, bytes], mode="r+b", endian="little"):
        self.mode: str = mode
        self._isBitesIO = False
        if type(path) is bytes:
            self.path = None
            self.f = path # type: ignore
            self.is_memory_file = True
        elif type(path) is BytesIO:
            self.path = None
            self.f = path
            self._isBitesIO = True
            self.is_memory_file = True
        else:
            self.path = path
            self.is_memory_file = False
        self.endian = "<" if endian == "little" or endian == "<" else ">"

    def __enter__(self):
        if self.is_memory_file:
            self.f: io.BufferedIOBase = self.f if self._isBitesIO else BytesIO(self.f) # type: ignore
        else:
            self.f:io.BufferedIOBase = open(self.path, self.mode) # type: ignore
        self.f.seek(0)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.f.close()

    def close(self):
        self.f.close()

    def tell(self):
        return self.f.tell()
    
    def truncate(self, size=None):
        if size is None:
            self.f.truncate(self.f.tell())
        else:
            self.f.truncate(size)

    def seek(self, pos, whence=0):
        self.f.seek(pos, whence)

    def read(self, n=-1):
        return self.f.read(n)

    def read_at(self, pos, n=-1):
        current = self.tell()
        self.seek(pos)
        ret = self.read(n)
        self.seek(current)
        return ret

    def write(self, data):
        self.f.write(data)

    def write_at(self, pos, data):
        current = self.tell()
        self.seek(pos)
        self.write(data)
        self.seek(current)

    def peek(self, n):
        pos = self.tell()
        ret = self.read(n)
        self.seek(pos)
        return ret

    def write_line(self, data):
        self.f.write(data + "\n")

    def set_endian(self, endian):
        self.endian = "<" if endian == "little" or endian == "<" else ">"

    def read_int8(self):
        return struct.unpack("b", self.read(1))[0]

    def read_int8_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_int8()
        self.seek(current)
        return ret

    def read_uint8(self):
        return struct.unpack("B", self.read(1))[0]

    def read_uint8_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_uint8()
        self.seek(current)
        return ret

    def read_int16(self):
        return struct.unpack(self.endian + "h", self.read(2))[0]

    def read_int16_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_int16()
        self.seek(current)
        return ret

    def read_uint16(self):
        return struct.unpack(self.endian + "H", self.read(2))[0]

    def read_uint16_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_uint16()
        self.seek(current)
        return ret

    def read_int32(self):
        return struct.unpack(self.endian + "i", self.read(4))[0]

    def read_int32_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_int32()
        self.seek(current)
        return ret

    def read_uint32(self):
        return struct.unpack(self.endian + "I", self.read(4))[0]

    def read_uint32_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_uint32()
        self.seek(current)
        return ret

    def read_int64(self):
        return struct.unpack(self.endian + "q", self.read(8))[0]

    def read_int64_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_int64()
        self.seek(current)
        return ret

    def read_uint64(self):
        return struct.unpack(self.endian + "Q", self.read(8))[0]

    def read_uint64_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_uint64()
        self.seek(current)
        return ret

    def read_single(self):
        return struct.unpack(self.endian + "f", self.read(4))[0]

    def read_single_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_single()
        self.seek(current)
        return ret

    def read_double(self):
        return struct.unpack(self.endian + "d", self.read(8))[0]

    def read_double_at(self, pos):
        current = self.tell()
        self.seek(pos)
        ret = self.read_double()
        self.seek(current)
        return ret
    
    def skip_padding(self, alignment):
        while self.tell() % alignment != 0:
            self.read_uint8()

    def write_int8(self, num):
        self.f.write(struct.pack("b", num))

    def write_int8_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_int8(num)
        self.seek(current)

    def write_uint8(self, num):
        self.f.write(struct.pack("B", num))

    def write_uint8_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_uint8(num)
        self.seek(current)

    def write_int16(self, num):
        self.f.write(struct.pack(self.endian + "h", num))

    def write_int16_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_int16(num)
        self.seek(current)

    def write_uint16(self, num):
        self.f.write(struct.pack(self.endian + "H", num))

    def write_uint16_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_uint16(num)
        self.seek(current)

    def write_int32(self, num):
        self.f.write(struct.pack(self.endian + "i", num))

    def write_int32_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_int32(num)
        self.seek(current)

    def write_uint32(self, num):
        self.f.write(struct.pack(self.endian + "I", num))

    def write_uint32_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_uint32(num)
        self.seek(current)

    def write_int64(self, num):
        self.f.write(struct.pack(self.endian + "q", num))

    def write_int64_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_int64(num)
        self.seek(current)

    def write_uint64(self, num):
        self.f.write(struct.pack(self.endian + "Q", num))

    def write_uint64_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_uint64(num)
        self.seek(current)

    def write_single(self, num):
        self.f.write(struct.pack(self.endian + "f", num))

    def write_single_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_single(num)
        self.seek(current)

    def write_double(self, num):
        self.f.write(struct.pack(self.endian + "d", num))

    def write_double_at(self, pos, num):
        current = self.tell()
        self.seek(pos)
        self.write_double(num)
        self.seek(current)

    def write_padding(self, alignment, pad_byte=0x00):
        while self.tell() % alignment != 0:
            self.write_uint8(pad_byte)
