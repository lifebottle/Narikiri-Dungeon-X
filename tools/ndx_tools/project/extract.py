import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from struct import unpack

import pyeboot
from loguru import logger
from pycdlib import pycdlib
from tqdm.rich import tqdm

import ndx_tools.project.paths as ndx_paths
from ndx_tools.formats import cab
from ndx_tools.formats.menu import Menu
from ndx_tools.formats.pak import Pak
from ndx_tools.formats.tss import Tss
from ndx_tools.formats.xml import TlXml
from ndx_tools.utils.fileio import FileIO

__SCRIPT_CMD = "extract"
__SCRIPT_DESC = "Given an NDX iso extracts the files, all.dat and misc files to xml"


def main(iso_path: Path, iso_only: bool, xml: bool):
    logger.debug(f"{iso_only}, {iso_path}")
    extract_iso(iso_path)
    decrypt_eboot()

    if iso_only:
        return

    extract_files()
    extract_maps()
    extract_events()
    extract_skits()

    if xml:
        return

    print("Creating XML files...")
    extract_menus_xmls()
    extract_xmls()


def extract_iso(iso_path: Path) -> None:
    print("Extracting ISO files...")

    iso = pycdlib.PyCdlib()
    iso.open(str(iso_path))

    ext_folder = ndx_paths.iso_files
    ndx_paths.clean_folder(ext_folder)

    files: list[Path] = []

    for dirname, _, filelist in iso.walk(iso_path="/"):
        for file in filelist:
            p = dirname + "/" + file
            p = p.lstrip("/")
            files.append(Path(p))

    total_size = 0
    for file in files:
        with iso.open_file_from_iso(iso_path="/" + file.as_posix()) as f:
            f.seek(0, 2)
            total_size += f.tell()

    with tqdm(
        total=total_size,
        desc=f"Extracting {file.as_posix()}", # type: ignore
        unit="B",
        unit_divisor=1024,
        unit_scale=True,
    ) as pbar:
        for file in files:
            out_path = ext_folder / file
            out_path.parent.mkdir(parents=True, exist_ok=True)
            pbar.set_description(file.as_posix())
            with (
                iso.open_file_from_iso(iso_path="/" + file.as_posix()) as f,
                out_path.open("wb+") as output,
            ):
                while data := f.read(0x8000):
                    output.write(data)
                    pbar.update(len(data))

    iso.close()


def decrypt_eboot() -> None:
    in_path = ndx_paths.original_eboot
    out_path = ndx_paths.decrypted_eboot
    pyeboot.decrypt(str(in_path), str(out_path)) # type: ignore


@dataclass
class FileInfo:
    pos: int
    size: int
    hash: int


def keystoint(x: dict):
    return { int(k, base=16): v.lower() for k, v in x.items() }


def get_hash(file_name: str) -> str:
    name_hash = 0
    for char in list(file_name.upper()):
        name_hash = ((name_hash << 7) + name_hash) + (name_hash << 3) + ord(char)
    return ("%08X" % (name_hash & 0xFFFFFFFF))


def extract_files() -> None:
    print("Extracting Game files...")

    eboot = ndx_paths.decrypted_eboot
    files: list[FileInfo] = []
    og_hash = {}
    with eboot.open("rb") as e:
        e.seek(0x1FF624)
        for _ in range(2116):
            files.append(FileInfo(*unpack("<3I", e.read(12))))
            og_hash[files[-1].hash] = True

    hashes_p = ndx_paths.hashes
    with hashes_p.open("r", encoding="utf8") as f:
        hashes: dict = json.load(f, object_hook=keystoint)

    all = ndx_paths.all_dat
    out_p = Path()
    with all.open("rb") as f:
        for file in (pbar := tqdm(files)):
            p = hashes.get(file.hash)
            out_p = Path("_noname") / f"{file.hash:08X}.bin" if p is None else Path(p)

            pbar.set_description(f"{out_p.as_posix()}")

            out_p = ndx_paths.extracted_files / "all" / out_p
            out_p.parent.mkdir(parents=True, exist_ok=True)
            f.seek(file.pos)
            with out_p.open("wb") as o:
                o.write(f.read(file.size))

def extract_menus_xmls() -> None:
    menu_json = ndx_paths.read_menu_json()
    xml_folder = ndx_paths.original_files / "menu"
    xml_folder.mkdir(parents=True, exist_ok=True)

    eboot = Menu(ndx_paths.decrypted_eboot, menu_json['Eboot'])
    eboot.extract_data()
    eboot.make_xml(xml_folder)

def extract_maps() -> None:
    print("Extracting Map files...")
    map_folder = ndx_paths.extracted_files / "all" / "map"
    out_folder = ndx_paths.extracted_files / "maps"

    files = list(map_folder.glob("*.bin"))

    for file in (pbar := tqdm(files)):
        pbar.set_description(f"{file.stem}")

        cab.extract_cab(file, out_folder / file.stem)

        # field.arc is special, game also hardcodes the offset
        offset = 0x94 if file.stem == "field" else 0x6C

        ar = out_folder / file.stem / "ar.dat"
        tss = out_folder / file.stem / "script.so"
        with FileIO(ar) as f:
            f.seek(f.read_int32(offset))
            with tss.open("wb") as g:
                g.write(f.read())


def extract_events() -> None:
    print("Extracting Event files...")
    map_folder = ndx_paths.extracted_files / "all" / "map" / "pack"
    out_folder = ndx_paths.extracted_files / "events"

    files = list(map_folder.glob("*.cab"))

    for file in (pbar := tqdm(files)):
        pbar.set_description(f"{file.stem}")
        cab.extract_cab(file, out_folder / file.stem)
        ar = out_folder / file.stem / "script.dat"
        tss = out_folder / file.stem / "script.so"
        pak = Pak.from_path(ar, 3)

        # TSS is always the first file in the PAK
        with tss.open("wb") as g:
            g.write(pak.files[0])


def extract_skits() -> None:
    print("Extracting Skit files...")
    skit_folder = ndx_paths.extracted_files / "all" / "chat"
    out_folder = ndx_paths.extracted_files / "skits"

    files = list(skit_folder.glob("*.bin"))

    for file in (pbar := tqdm(files)):
        pbar.set_description(f"{file.stem}")
        cab.extract_cab(file, out_folder / file.stem)
        ar = out_folder / file.stem / "ar.dat"
        tss = out_folder / file.stem / "script.so"
        pak = Pak.from_path(ar, 3)

        # TSS is always the second file in the PAK
        with tss.open("wb") as g:
            g.write(pak.files[1])


def extract_xmls() -> None:
    ef = ndx_paths.extracted_files
    of = ndx_paths.original_files
    paths = [
        (ef / "maps", of / "maps"),
        (ef / "events", of / "story"),
        (ef / "skits", of / "skits"),
    ]

    # Fill the common replacements dict
    TlXml.load_common(ndx_paths.translation_files / "menu" / "Common.xml")

    for folder, out_folder in paths:
        folder.mkdir(parents=True, exist_ok=True)

        for path in (pbar := tqdm(list(folder.rglob("*.so")))):
            n = out_folder / (path.parent.name + ".xml")
            pbar.set_description(f"{out_folder.name}/{path.parent.name}")
            Tss.from_file(path).make_xml(n)


def add_arguments_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--iso-only",
        help="Extract only the iso files",
        action="store_true",
    )
    parser.add_argument(
        "--xml",
        help="Re-Extract xml files",
        action="store_true",
    )
    parser.add_argument(
        "--iso",
        help="Path to the game's .iso file",
        default=ndx_paths.default_iso,
        type=Path,
    )


def process_arguments(args: argparse.Namespace):
    main(args.iso, args.iso_only, args.xml)


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
