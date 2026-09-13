"""
Standalone runner for repack.py — run this directly from the repo root:

    python run_repack.py

No package install needed. Just make sure loguru and tqdm are available:

    pip install loguru tqdm
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from struct import unpack, pack

from loguru import logger
from tqdm.rich import tqdm

# ---------------------------------------------------------------------------
# Paths — mirrors ndx_paths.py, adjust if your layout differs
# ---------------------------------------------------------------------------

extracted_files: Path = Path("1_extracted")
patched_files:   Path = Path("3_patched")
game_builds:     Path = Path("3_patched")
decrypted_eboot: Path = Path("1_extracted/EBOOT.BIN")
hashes:          Path = Path("project/hashes.json")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EBOOT_FILE_TABLE_OFFSET = 0x1FF624
FILE_TABLE_ENTRY_COUNT  = 2116
FILE_TABLE_ENTRY_SIZE   = 12  # 3 × uint32 LE  (pos, size, hash)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass
class FileInfo:
    pos:  int
    size: int
    hash: int


def keystoint(x: dict) -> dict:
    return {int(k, base=16): v.lower() for k, v in x.items()}


# ---------------------------------------------------------------------------
# Alignment detection
# ---------------------------------------------------------------------------

def detect_alignment(files: list[FileInfo]) -> int:
    """
    Find the largest power-of-2 (up to 2048) that divides every non-zero
    file position in the original table.  Falls back to 1 (no alignment).
    """
    alignment = 2048
    for fi in files:
        if fi.pos == 0:
            continue
        while alignment > 1 and (fi.pos % alignment) != 0:
            alignment //= 2
    return max(alignment, 1)


# ---------------------------------------------------------------------------
# Repack
# ---------------------------------------------------------------------------

def repack_all_dat(
    patched_root:   Path,
    extracted_root: Path,
    out_path:       Path,
    files:          list[FileInfo],
    hashes_map:     dict[int, str],
    alignment:      int,
) -> list[FileInfo]:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    new_files: list[FileInfo] = []
    zeroes = b"\x00" * alignment

    with out_path.open("wb") as out:
        for fi in (pbar := tqdm(files, desc="Repacking all.dat")):
            rel_path = hashes_map.get(fi.hash)
            rel_path_obj = (
                Path("_noname") / f"{fi.hash:08X}.bin"
                if rel_path is None
                else Path(rel_path)
            )

            patched_candidate   = patched_root   / "all" / rel_path_obj
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

            data    = src.read_bytes()
            new_pos = out.tell()

            if alignment > 1 and new_pos % alignment != 0:
                padding = alignment - (new_pos % alignment)
                out.write(zeroes[:padding])
                new_pos = out.tell()

            out.write(data)
            new_files.append(FileInfo(pos=new_pos, size=len(data), hash=fi.hash))

    return new_files


def patch_eboot(src: Path, dst: Path, new_files: list[FileInfo]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    with dst.open("r+b") as f:
        f.seek(EBOOT_FILE_TABLE_OFFSET)
        for fi in new_files:
            f.write(pack("<3I", fi.pos, fi.size, fi.hash))

    logger.info(f"Patched EBOOT written to {dst}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    out_all_dat = game_builds / "all.dat"
    out_eboot   = game_builds / "EBOOT.BIN"

    game_builds.mkdir(parents=True, exist_ok=True)
    patched_files.mkdir(parents=True, exist_ok=True)

    # Load file table from decrypted EBOOT
    logger.info("Reading file table from decrypted EBOOT...")
    files: list[FileInfo] = []
    with decrypted_eboot.open("rb") as e:
        e.seek(EBOOT_FILE_TABLE_OFFSET)
        for _ in range(FILE_TABLE_ENTRY_COUNT):
            files.append(FileInfo(*unpack("<3I", e.read(FILE_TABLE_ENTRY_SIZE))))

    # Load hashes
    with hashes.open("r", encoding="utf8") as f:
        hashes_map: dict[int, str] = json.load(f, object_hook=keystoint)

    # Detect alignment from original positions
    alignment = detect_alignment(files)
    logger.info(f"Detected all.dat alignment: {alignment} bytes")

    # Repack
    print("Repacking all.dat...")
    new_files = repack_all_dat(
        patched_root   = patched_files,
        extracted_root = extracted_files,
        out_path       = out_all_dat,
        files          = files,
        hashes_map     = hashes_map,
        alignment      = alignment,
    )
    logger.info(f"Written: {out_all_dat}")

    # Patch EBOOT
    print("Patching EBOOT.BIN...")
    patch_eboot(decrypted_eboot, out_eboot, new_files)

    print("Done.")
    print(f"  all.dat   -> {out_all_dat}")
    print(f"  EBOOT.BIN -> {out_eboot}")


if __name__ == "__main__":
    main()
