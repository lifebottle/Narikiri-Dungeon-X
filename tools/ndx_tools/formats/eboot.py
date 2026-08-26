import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from struct import unpack, pack

from loguru import logger
from tqdm.rich import tqdm

from ndx_tools.project import ndx_paths

__SCRIPT_CMD = "repack"
__SCRIPT_DESC = (
    "Repacks 3_patched/all into 4_builds/all.dat and updates the EBOOT.BIN file table. "
    "Files present in 3_patched/all override those from 1_extracted/all; "
    "everything else is taken from 1_extracted/all."
)

  # 3 × uint32 LE  (pos, size, hash)





def keystoint(x: dict) -> dict:
    return {int(k, base=16): v.lower() for k, v in x.items()}





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

    return new_files


def patch_eboot(src_eboot: Path, out_eboot: Path, new_files: list[FileInfo]) -> None:
    """
    Copy src_eboot to out_eboot, then overwrite the file table in-place
    with the updated pos/size/hash entries.
    """
    out_eboot.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_eboot, out_eboot)

    with out_eboot.open("r+b") as f:
        f.seek(EBOOT_FILE_TABLE_OFFSET)
        for fi in new_files:
            f.write(pack("<3I", fi.pos, fi.size, fi.hash))

    logger.info(f"Patched EBOOT written to {out_eboot}")


def main() -> None:
    # ------------------------------------------------------------------ paths
    patched_root   = ndx_paths.patched_files        # 3_patched
    extracted_root = ndx_paths.extracted_files      # 1_extracted
    builds_root    = ndx_paths.game_builds          # 4_builds
    src_eboot      = ndx_paths.decrypted_eboot      # 1_extracted/EBOOT.BIN
    out_all_dat    = builds_root / "all.dat"
    out_eboot      = builds_root / "EBOOT.BIN"

    # Ensure output folders exist
    builds_root.mkdir(parents=True, exist_ok=True)
    patched_root.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------- load file table




    # --------------------------------------------------- detect alignment


    # ------------------------------------------------------- repack all.dat
    print("Repacking all.dat...")
    new_files = repack_all_dat(
        patched_root=patched_root,
        extracted_root=extracted_root,
        out_path=out_all_dat,
        files=files,
        hashes=hashes,
        alignment=alignment,
    )
    logger.info(f"Written: {out_all_dat}")

    # ------------------------------------------------------- patch eboot

    patch_eboot(src_eboot, out_eboot, new_files)

    print("Done.")
    print(f"  all.dat  -> {out_all_dat}")
    print(f"  EBOOT.BIN -> {out_eboot}")


def add_arguments_to_parser(parser: argparse.ArgumentParser) -> None:
    # No required arguments for now — all paths come from ndx_paths
    pass


def process_arguments(args: argparse.Namespace) -> None:
    main()


def add_subparser(subparser: argparse._SubParsersAction) -> None:
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
