import struct
from pathlib import Path
from typing import Any, cast


class FileIO:
    _sint64 = struct.Struct("<q")
    _uint64 = struct.Struct("<Q")
    _sint32 = struct.Struct("<i")
    _uint32 = struct.Struct("<I")
    _sint16 = struct.Struct("<h")
    _uint16 = struct.Struct("<H")
    _sint8 = struct.Struct("<b")
    _uint8 = struct.Struct("<B")
    _f64 = struct.Struct("<d")
    _f32 = struct.Struct("<f")

    __slots__ = ("data", "mode", "offset", "path", "written")

    def __init__(self, path: Path | str | bytes, mode="r+b"):
        self.mode: str = mode
        self.offset: int = 0
        self.path: Path | bytes | None = None
        self.written = False

        if type(path) is bytes:
            self.path = None
            self.data = bytearray(path)
        elif isinstance(path, (str, Path)):
            self.path = Path(path)
            if self.path.exists():
                self.data = bytearray(self.path.read_bytes())
            else:
                raise ValueError("File does not exist")
        else:
            self.data = bytearray()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if isinstance(self.path, Path) and self.written:
            self.path.write_bytes(self.data)

    def get_buffer(self):
        return self.data

    def tell(self):
        return self.offset

    def seek(self, pos, whence=0):
        size = len(self.data)

        if whence == 0:
            new = pos
        elif whence == 1:
            new = self.offset + pos
        elif whence == 2:
            new = size + pos
        else:
            raise ValueError("invalid whence")

        if not (0 <= new <= size):
            raise ValueError("seek out of bounds")

        self.offset = new

    def read(self, n=-1):
        if n == -1:
            data = self.data[self.offset:]
            self.offset = len(self.data)
        else:
            data = self.data[self.offset:self.offset+n]
            self.offset += n

        return bytes(data)

    def read_at(self, pos, n=-1):
        current = self.tell()
        self.seek(pos)
        ret = self.read(n)
        self.seek(current)
        return ret

    def write(self, data: bytes, pos: int = -1):
        _pos = self.offset if pos < 0 else pos
        end = _pos + len(data)

        if end > len(self.data):
            self.data.extend(b"\x00" * (end - len(self.data)))

        self.data[_pos:end] = data
        self.written = True

        if pos < 0:
            self.offset = end

    def peek(self, n):
        pos = self.tell()
        ret = self.read(n)
        self.seek(pos)
        return ret

    def write_line(self, data: str, encoding: str = "utf8"):
        self.write(data.encode(encoding))
        self.write(b"\n")

    def read_string(self, encoding: str = "utf8", pos: int = -1) -> str:
        _pos = self.offset if pos < 0 else pos

        end = self.data.find(0, _pos)
        if end == -1:
            raise ValueError("Unterminated string")

        raw = self.data[_pos:end]

        if pos < 0:
            self.offset = end + 1  # skip NUL

        return raw.decode(encoding)

    def _read_generic(self, _s: struct.Struct, pos: int = -1) -> tuple[Any, ...]:
        _pos = self.offset if pos < 0 else pos
        val = _s.unpack_from(self.data, _pos)
        if pos < 0:
            self.offset += _s.size
        return val

    def read_struct(self, fmt: str, pos: int = -1) -> tuple[Any, ...]:
        st = struct.Struct(fmt) if type(fmt) is str else cast(struct.Struct, fmt)
        return self._read_generic(st, pos)

    def read_int8(self, pos: int = -1):
        return self._read_generic(self._sint8, pos)[0]

    def read_uint8(self, pos: int = -1):
        return self._read_generic(self._uint8, pos)[0]

    def read_int16(self, pos: int = -1):
        return self._read_generic(self._sint16, pos)[0]

    def read_uint16(self, pos: int = -1):
        return self._read_generic(self._uint16, pos)[0]

    def read_int32(self, pos: int = -1):
        return self._read_generic(self._sint32, pos)[0]

    def read_uint32(self, pos: int = -1):
        return self._read_generic(self._uint32, pos)[0]

    def read_int64(self, pos: int = -1):
        return self._read_generic(self._sint64, pos)[0]

    def read_uint64(self, pos: int = -1):
        return self._read_generic(self._uint64, pos)[0]

    def read_float(self, pos: int = -1):
        return self._read_generic(self._f32, pos)[0]

    def read_double(self, pos: int = -1):
        return self._read_generic(self._f64, pos)[0]

    def skip_padding(self, alignment):
        while self.tell() % alignment != 0:
            self.read_uint8()

    def write_int8(self, num: int, pos: int = -1):
        self.write(self._sint8.pack(num), pos)

    def write_uint8(self, num: int, pos: int = -1):
        self.write(self._uint8.pack(num), pos)

    def write_int16(self, num: int, pos: int = -1):
        self.write(self._sint16.pack(num), pos)

    def write_uint16(self, num: int, pos: int = -1):
        self.write(self._uint16.pack(num), pos)

    def write_int32(self, num: int, pos: int = -1):
        self.write(self._sint32.pack(num), pos)

    def write_uint32(self, num: int, pos: int = -1):
        self.write(self._uint32.pack(num), pos)

    def write_int64(self, num: int, pos: int = -1):
        self.write(self._sint64.pack(num), pos)

    def write_uint64(self, num: int, pos: int = -1):
        self.write(self._uint64.pack(num), pos)

    def write_float(self, num: int, pos: int = -1):
        self.write(self._f32.pack(num), pos)

    def write_double(self, num: int, pos: int = -1):
        self.write(self._f64.pack(num), pos)

    def write_struct(self, fmt: str, *values, pos: int = -1):
        st = struct.Struct(fmt)
        self.write(st.pack(*values), pos)

    def write_padding(self, alignment, pad_byte=b"\x00") -> int:
        pos = self.tell()
        pad = (-pos) % alignment

        if pad:
            self.write(pad_byte * pad)

        return pad
