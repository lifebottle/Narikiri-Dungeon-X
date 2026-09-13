import subprocess
import sys
from pathlib import Path

import ndx_tools.project.paths as ndx_paths
from ndx_tools.utils.fileio import FileIO
from ndx_tools.utils.lzx.decoder import LZXDecompressor

_IS_LINUX = sys.platform.startswith("linux")
_EXE = ndx_paths.binaries / "CabArc.exe"
_CMD_EXTRACT = [_EXE]
_CMD_EXTRACT += ["-o", "-p"]
_CMD_MAKE = [_EXE]
_CMD_MAKE += ["-m", "LZX:15", "-i", "4392", "-s", "8"]


def _check_wibo() -> None:
    try:
        subprocess.run(["wibo"], check=False)
    except FileNotFoundError:
        print("ERROR: wibo does not appear to be accessible")
        print("To install it, please download it and put it in your PATH:")
        print(
            "  wget https://github.com/decompals/wibo/releases/download/1.0.0/wibo-x86_64",
            "&& chmod +x wibo-x86_64 && sudo mv wibo-x86_64 /usr/bin/wibo"
        )
        sys.exit(-1)


if _IS_LINUX:
    _check_wibo()
    _CMD_EXTRACT = ["wibo"] + _CMD_EXTRACT
    _CMD_MAKE = ["wibo"] + _CMD_MAKE


# Replicates the functions at 0x088d96c4 and 0x088d9588
def parse_cab(input: bytes) -> tuple[str, bytes, bytes]:
    with FileIO(input) as f:
        magic, files, flags = f.read_struct("<4s24xHH")
        if magic != b"MSCF":
            raise ValueError("Not a cabinet file!")

        if files != 1:
            raise ValueError("File count not 1!")

        if flags & 3:
            raise ValueError("Can't handle chunked cab files")

        hdr_off = 0x24
        if flags & 4: # reserve header skip
            hdr, folder, data = f.read_struct("<HBB", hdr_off)
            hdr_off += hdr + folder + data + 4

        file_off, blks, comp, level = f.read_struct("<IHBB", hdr_off)

        if (comp & 15) != 3 or level != 15: # 3 -> LZX / 15 -> 32K window size
            raise ValueError("Invalid compressor!")

        f.seek(hdr_off + 0x18)
        name = f.read_string()
        head = f.read_at(0, file_off)

        # Game actually keeps parsing the header
        # but I'll just assume file_off is valid
        f.seek(file_off)
        out = []

        dec = LZXDecompressor()
        for _ in range(blks):
            _csum, csize, usize = f.read_struct("<IHH")
            data = dec.decompress(f.read(csize), usize)
            out.append(data)

        return name, head, b"".join(out)


def decode_cab(input: bytes) -> bytes:
    return parse_cab(input)[2]


def extract_cab(input: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        _CMD_EXTRACT + ["X", str(input), str(output) + "\\"],
        check=False, stdout=subprocess.DEVNULL,
    )


def make_cab(input: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        _CMD_MAKE + ["N", str(output), str(input) + "*"],
        check=False, stdout=subprocess.DEVNULL,
    )


def make_cab_list(inputs: list[Path], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)

    files = [str(x) for x in inputs]
    subprocess.run(
        _CMD_MAKE + ["N", str(output)] + files,
        check=False, stdout=subprocess.DEVNULL,
    )
