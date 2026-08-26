import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import shutil
import pyeboot
from loguru import logger
from pycdlib import pycdlib
from tqdm.rich import tqdm
from struct import unpack, pack
from ndx_tools.formats import cab
from ndx_tools.formats.pak import Pak
from ndx_tools.formats.tss import Tss
from ndx_tools.formats.fps4 import Fps4
from ndx_tools.formats.menu import Menu
from ndx_tools.formats.xml import TlXml
from ndx_tools.utils.fileio import FileIO


from . import ndx_paths

@dataclass
class FileInfo:
    pos: int
    size: int
    hash: int

__SCRIPT_CMD = "repack"
__SCRIPT_DESC = "Given an NDX iso extracts the files, all.dat and misc files to xml"

EBOOT_FILE_TABLE_OFFSET = 0x1FF624
FILE_TABLE_ENTRY_COUNT = 2116
FILE_TABLE_ENTRY_SIZE = 12
LIST_STATUS = ['Editing', 'Proofreading', 'Done']

def main():

    #Reinsert menus text
    reinsert_menus_text()
    repack_alldat_eboot_archive()

def reinsert_menus_text():
    #Copy original eboot into final
    ndx_paths.patched_files.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ndx_paths.decrypted_eboot , ndx_paths.patched_files / 'EBOOT.BIN')

    reinsert_eboot_text()

def reinsert_eboot_text():
    menu_json = ndx_paths.read_menu_json()
    menu = Menu(ndx_paths.decrypted_eboot, menu_json['Eboot'])

    menu.reinsert_file(ndx_paths.patched_files / 'EBOOT.BIN', ndx_paths.translation_files / 'menu', LIST_STATUS)

def repack_alldat_eboot_archive():

    # Ensure output folders exist
    ndx_paths.game_builds.mkdir(parents=True, exist_ok=True)
    ndx_paths.patched_files.mkdir(parents=True, exist_ok=True)
    files = load_file_table(ndx_paths.decrypted_eboot)
    hashes = load_hashes()
    alignment = detect_alignment(files)

    new_files = repack_all_dat(
        patched_root=ndx_paths.patched_files,
        extracted_root=ndx_paths.extracted_files,
        out_path=ndx_paths.game_builds / 'all.dat',
        files=files,
        hashes=hashes,
        alignment=alignment,
    )

    patch_eboot(ndx_paths.patched_files / 'EBOOT.BIN', new_files)

def load_file_table(src_eboot:Path):
    logger.info("Reading file table from decrypted EBOOT...")
    files: list[FileInfo] = []

    with src_eboot.open("rb") as e:
        e.seek(EBOOT_FILE_TABLE_OFFSET)
        for _ in range(FILE_TABLE_ENTRY_COUNT):
            files.append(FileInfo(*unpack("<3I", e.read(FILE_TABLE_ENTRY_SIZE))))

    return files

def detect_alignment(files: list[FileInfo]) -> int:

    alignment = 2048

    for fi in files:
        if fi.pos == 0:
            continue
        while alignment > 1 and (fi.pos % alignment) != 0:
            alignment //= 2

    logger.info(f"Detected all.dat alignment: {alignment} bytes")
    return max(alignment, 1)

def load_hashes():
    # ----------------------------------------------------------- load hashes

    def keystoint(x: dict) -> dict:
        return {int(k, base=16): v.lower() for k, v in x.items()}

    with ndx_paths.hashes.open("r", encoding="utf8") as f:
        hashes: dict[int, str] = json.load(f, object_hook=keystoint)
    return hashes



def repack_all_dat(patched_root: Path, extracted_root: Path, out_path: Path,
                   files: list[FileInfo], hashes: dict[int, str],
                   alignment: int) -> list[FileInfo]:
    """
    Write a new all.dat to out_path.

    For each entry in the original file table (ordered by table index):
      - Use the file from patched_root/all/<name> if it exists.
      - Otherwise fall back to extracted_root/all/<name>.

    Returns a new list of FileInfo with updated pos and size fields
    (hash values are unchanged).
    """
    print("Repacking all.dat...")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    new_files: list[FileInfo] = []
    pad = b"\x00" * alignment  # reuse a zeroed buffer for padding writes

    with out_path.open("wb") as out:
        for fi in (pbar := tqdm(files, desc="Repacking all.dat")):
            rel_path = hashes.get(fi.hash)
            if rel_path is None:
                # Unnamed file — fall back by hash filename
                rel_path_obj = Path("_noname") / f"{fi.hash:08X}.bin"
            else:
                rel_path_obj = Path(rel_path)

            # Prefer patched version, fall back to extracted
            patched_candidate = patched_root / "all" / rel_path_obj
            extracted_candidate = extracted_root / "all" / rel_path_obj

            if patched_candidate.exists():
                src = patched_candidate
            elif extracted_candidate.exists():
                src = extracted_candidate
            else:
                raise FileNotFoundError(
                    f"Cannot find source for hash {fi.hash:08X} "
                    f"(expected at {patched_candidate} or {extracted_candidate})"
                )

            pbar.set_description(rel_path_obj.as_posix())

            data = src.read_bytes()
            new_pos = out.tell()

            # Align the write position if needed
            if alignment > 1 and new_pos % alignment != 0:
                padding_needed = alignment - (new_pos % alignment)
                out.write(pad[:padding_needed])
                new_pos = out.tell()

            out.write(data)
            new_files.append(FileInfo(pos=new_pos, size=len(data), hash=fi.hash))

    logger.info(f"Written: {out_path}")
    return new_files


def patch_eboot(out_eboot: Path, new_files: list[FileInfo]) -> None:
    print("Patching EBOOT.BIN...")


    with out_eboot.open("r+b") as f:
        f.seek(EBOOT_FILE_TABLE_OFFSET)
        for fi in new_files:
            f.write(pack("<3I", fi.pos, fi.size, fi.hash))

    logger.info(f"Patched EBOOT written to {out_eboot}")
    print("Done.")

def add_arguments_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--iso-only",
        help="Extract only the iso files",
        action="store_true",
    )
    parser.add_argument(
        "--iso",
        help="Path to the game's .iso file",
        default=ndx_paths.default_iso,
        type=Path,
    )


def process_arguments(args: argparse.Namespace):
    main()


def add_subparser(subparser: argparse._SubParsersAction):
    parser = subparser.add_parser(
        __SCRIPT_CMD, help=__SCRIPT_DESC, description=__SCRIPT_DESC
    )
    add_arguments_to_parser(parser)
    parser.set_defaults(func=process_arguments)


parser = argparse.ArgumentParser(description=__SCRIPT_DESC)
add_arguments_to_parser(parser)

if __name__ == "__main__":
    args = parser.parse_args()
    process_arguments(args)