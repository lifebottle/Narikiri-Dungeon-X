from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from ndx_tools.formats import cab
from ndx_tools.utils.fileio import FileIO


@dataclass(slots=True)
class Fps4File:
    off: int | None = None
    size_al: int | None = None
    size: int | None = None
    name: str | None = None
    offset: int | None = None
    file_extension: str | None = None
    data: bytes = b""
    is_compressed: bool = False
    cab_hdr: bytes = b""
    cab_name: str = ""

@dataclass(slots=True)
class Fps4:
    file_count: int = 0
    header_size: int = 0
    file_start: int = 0
    entry_size: int = 0
    flags: int = 0
    is_split: bool = False
    is_sorted: bool = False
    is_unk16: bool = False
    is_unk17: bool = False
    comm_offset: int = 0
    files: list[Fps4File] = field(default_factory=list)
    files_dict: dict[str, bytes] = field(default_factory=dict)

    @classmethod
    def from_file(cls, header: Path, content: Path | None = None) -> Self:
        content = content if content else header
        fps = cls()
        with FileIO(header) as f:
            if f.read(4) != b"FPS4":
                raise ValueError("Not a FPS4 file!")

            fps.file_count = f.read_uint32() - 1
            fps.header_size = f.read_uint32()
            fps.file_start = f.read_uint32()
            fps.entry_size = f.read_uint16()
            fps.flags = f.read_uint16()
            fps.is_split = f.read_uint8() == 1
            fps.is_sorted = f.read_uint8() == 1
            fps.is_unk16 = f.read_uint8() == 1
            fps.is_unk17 = f.read_uint8() == 1
            fps.comm_offset = f.read_uint32()

            # The proper way to read these involves checking
            # which flag bits are set and parse the fields
            # the flag enables, but we take a shortcut for
            # easier parsing code, later it could be done
            # properly

            f.seek(fps.header_size)

            for _ in range(fps.file_count):
                if fps.flags == 0xF:
                    f0, f1, f2, f3 = f.read_struct("<3I32s")
                elif fps.flags == 0xB:
                    f0, f1, f3 = f.read_struct("<2I32s")
                    f2 = f1
                elif fps.flags == 0x1FF:
                    f0, f1, f2, f3 = f.read_struct("<3I32s")
                    f4, f5, f6, f7, f8 = f.read_struct("<5I")
                    if any(x != 0 for x in (f5, f6, f7, f8)):
                        raise ValueError("????")
                else:
                    raise ValueError(f"Unknown flags value 0x{fps.flags:03X}")

                f3: bytes
                name = f3.rstrip(b'\x00').decode()
                fd = Fps4File(f0, f1, f2, name)
                fps.files.append(fd)

        with FileIO(content) as f:
            for file in fps.files:
                f.seek(file.off)

                assert file.size is not None, "FPS4 subfile size not set!"
                assert file.name is not None, "FPS4 subfile name not set!"

                file.data = f.read(file.size)
                if file.data[:4] == b"MSCF":
                    file.cab_name, file.cab_hdr, file.data = cab.parse_cab(file.data)
                    fps.files_dict[file.cab_name] = file.data
                fps.files_dict[file.name] = file.data

        return fps
