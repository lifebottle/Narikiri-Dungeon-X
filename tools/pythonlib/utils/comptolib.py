import ctypes
import struct
from pathlib import Path

# Error codes
SUCCESS               =  0
ERROR_FILE_IN         = -1
ERROR_FILE_OUT        = -2
ERROR_MALLOC          = -3
ERROR_BAD_INPUT       = -4
ERROR_UNKNOWN_VERSION = -5
ERROR_FILES_MISMATCH  = -6


class ComptoFileInputError(Exception):
    pass


class ComptoFileOutputError(Exception):
    pass


class ComptoMemoryAllocationError(Exception):
    pass


class ComptoBadInputError(Exception):
    pass


class ComptoUnknownVersionError(Exception):
    pass


class ComptoMismatchedFilesError(Exception):
    pass


class ComptoUnknownError(Exception):
    pass


def RaiseError(error: int):
    if error == SUCCESS:
        return
    elif error == ERROR_FILE_IN:
        raise ComptoFileInputError("Error with input file")
    elif error == ERROR_FILE_OUT:
        raise ComptoFileOutputError("Error with output file")
    elif error == ERROR_MALLOC:
        raise ComptoMemoryAllocationError("Malloc failure")
    elif error == ERROR_BAD_INPUT:
        raise ComptoBadInputError("Bad Input")
    elif error == ERROR_UNKNOWN_VERSION:
        raise ComptoUnknownVersionError("Unknown version")
    elif error == ERROR_FILES_MISMATCH:
        raise ComptoMismatchedFilesError("Mismatch")
    else:
        raise ComptoUnknownError("Unknown error")


comptolib_path = Path(__file__).parent / "comptolib.dll"

comptolib = ctypes.cdll.LoadLibrary(str(comptolib_path))
compto_decode = comptolib.Decode
compto_decode.argtypes = (
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_uint),
)
compto_decode.restype = ctypes.c_int

compto_encode = comptolib.Encode
compto_encode.argtypes = (
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_uint),
)
compto_encode.restype = ctypes.c_int

compto_fdecode = comptolib.DecodeFile
compto_fdecode.argtypes = ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int
compto_fdecode.restype = ctypes.c_int

compto_fencode = comptolib.EncodeFile
compto_fencode.argtypes = ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int
compto_fencode.restype = ctypes.c_int


class ComptoFile:
    def __init__(self, type: int, data: bytes) -> None:
        self.type = type
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data)


def compress_data(input: bytes, raw: bool = False, version: int = 3) -> bytes:
    input_size = len(input)
    output_size = ((input_size * 9) // 8) + 10
    output = b"\x00" * output_size
    output_size = ctypes.c_uint(output_size)
    error = compto_encode(version, input, input_size, output, ctypes.byref(output_size))
    RaiseError(error)

    if not raw:
        output = (
            struct.pack("<b", version)
            + struct.pack("<L", output_size.value)
            + struct.pack("<L", input_size)
            + output[: output_size.value]
        )

    return output


def decompress_data(input: bytes, raw: bool = False, version: int = 3) -> bytes:
    if raw:
        input_size = len(input)
        output_size = input_size * 10
    else:
        version = struct.unpack("<b", input[:1])[0]
        input_size, output_size = struct.unpack("<2L", input[1:9])

    output = b"\x00" * output_size
    input = input[9:]

    error = compto_decode(
        version, input, input_size, output, ctypes.byref(ctypes.c_uint(output_size))
    )
    RaiseError(error)
    return output


def compress_file(input: str, output: str, raw: bool = False, version: int = 3) -> None:
    error = compto_fencode(input.encode("utf-8"), output.encode("utf-8"), raw, version)
    RaiseError(error)


def decompress_file(
    input: str, output: str, raw: bool = False, version: int = 3
) -> None:
    error = compto_fdecode(input.encode("utf-8"), output.encode("utf-8"), raw, version)
    RaiseError(error)


def is_compressed(data: bytes) -> bool:
    if len(data) < 0x09:
        return False

    if data[0] not in (0, 1, 3):
        return False

    expected_size = struct.unpack("<L", data[1:5])[0]
    aligned_size = (expected_size + 9) + (0x100 - ((expected_size + 9) % 0x100))
    tail_data = abs(len(data) - (expected_size + 9))

    if expected_size == len(data) - 9 or aligned_size == len(data):
        return True

    if (tail_data <= 0x10 and data[expected_size + 9 :] == b"#" * tail_data) or (
        tail_data <= 0x4 and data[expected_size + 9 :] == b"\x00" * tail_data
    ):
        return True  # SCPK files have these trailing "#" bytes :(

    return False
