import shutil
from pathlib import Path

import pyjson5 as json
from loguru import logger

default_iso: Path = Path("ndx.iso")
iso_files: Path = Path("0_disc")
original_eboot: Path = Path("0_disc/PSP_GAME/SYSDIR/EBOOT.BIN")
all_dat: Path = Path("0_disc/PSP_GAME/USRDIR/all.dat")
extracted_files: Path = Path("1_extracted")
decrypted_eboot: Path = Path("1_extracted/EBOOT.BIN")
original_files: Path = Path("1.5_original")
translation_files: Path = Path("2_translated")
patched_files: Path = Path("3_patched")
game_builds: Path = Path("4_builds")
binaries: Path = Path("tools/bin")
hashes: Path = Path("project/hashes.json")
menu_json: Path = Path("project/MenuFiles.json")

def clean_folder(path: Path) -> None:
    target_files = list(path.iterdir())
    if len(target_files) == 0:
        return

    logger.info("Cleaning folder...")
    for file in target_files:
        if file.is_dir():
            shutil.rmtree(file)
        elif file.name.lower() != ".gitignore":
            file.unlink(missing_ok=False)


def clean_builds(path: Path) -> None:
    target_files = sorted(path.glob("*.iso"), key=lambda x: x.name)[:-4]
    if len(target_files) == 0:
        return

    logger.info("Cleaning builds folder...")
    for file in target_files:
        logger.info(f"deleting {file.name!s}...")
        file.unlink()


def read_menu_json():
    with menu_json.open("r", encoding="utf-8") as f:
        data = json.load(f) # type: ignore

        return { ele['friendly_name']:ele for ele in data }
