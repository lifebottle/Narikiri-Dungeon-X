from ndx_tools.formats.xml import TlXml
from ndx_tools.utils.fileio import FileIO
from ndx_tools.formats.xml import TlText
from ndx_tools.utils.string import bytes_to_text
from dataclasses import dataclass, field
from typing import Any

from pathlib import Path
from typing import Self, cast
import re
from tqdm.rich import tqdm

@dataclass
class MenuSection:
    name: str
    pointers_start: int
    pointers_end: int
    style: str
    text_areas: (int, int)

    @classmethod
    def from_dict(cls, data: dict) -> "MenuSection":
        return cls(
            name=Menu.fetch_clean_section_name(data["section"]),
            text_areas=Menu.fetch_text_area(data["section"]),
            pointers_start=data["pointers_start"],
            pointers_end=data["pointers_end"],
            style=data["style"]
        )

class Menu:

    def __init__(self, file_path:Path, entry:dict) -> None:
        self.entry = entry
        self.file_path = file_path
        self.base_offset = entry['base_offset']
        self.friendly_name = entry['friendly_name']
        self.menu_sections = [
            MenuSection.from_dict(section)
            for section in entry.get("sections", [])
        ]
        self.id = 1

    @staticmethod
    def fetch_clean_section_name(section:str):
        first_occ = section.find("[")
        return section[:first_occ-1]

    @staticmethod
    def fetch_text_area(name:str):
        match = re.search(r'\[(0x[0-9A-Fa-f]+)\s*-\s*(0x[0-9A-Fa-f]+)\]', name)

        if match:
            start = int(match.group(1), 16)
            end = int(match.group(2), 16)

            return start, end

        else:
            return 0, 0

    def extract_data(self, keep_translations:bool = True) -> None:

        # Collect the canonical pointer for the embedded pairs
        # might need a function extract here?
        self.entry_sections = []

        with FileIO(self.file_path, 'rb') as f:
            for section in self.menu_sections:
                self.extract_section_basic(section, f)

        #if keep_translations:
        #    self.copy_translations_menu(root_original=xml_root, translated_path=self.paths['menu_xml'] / f"{file_def['friendly_name']}.xml")


    def get_style_pointers(self, f:FileIO, ptr_range: tuple[int, int], style: str):

        if style == "*":
            pointers_offset, pointers_value = self.get_all_possible(f, ptr_range)

        else:
            pointers_offset, pointers_value = self.get_regular_pattern(f, ptr_range, style)

        return pointers_offset, pointers_value



    def extract_section_basic(self, section: MenuSection, f:FileIO) -> None:

        # Extract Pointers list out of the file
        pointers_offset = []
        pointers_value = []

        pointers_offset_, pointers_value_ = self.get_style_pointers(f, (section.pointers_start, section.pointers_end),
                                                                    section.style)
        pointers_offset.extend(pointers_offset_)
        pointers_value.extend(pointers_value_)

        # Make a list, we also merge the emb pointers with the
        # other kind in the case they point to the same text
        entries = []
        temp = dict()
        f.seek(0)
        for off, val in zip(pointers_offset, pointers_value):
            text = bytes_to_text(f, offset=val)
            temp.setdefault(text, dict()).setdefault("ptr", []).append(off)
            entries.append( (off, text, self.id))
            self.id = self.id + 1


        # Remove duplicates
        #list_informations = [(k, str(v['ptr'])[1:-1], v.setdefault('emb', None)) for k, v in temp.items()]
        self.entry_sections.append((section.name, entries))

    def make_xml(self, folder: Path) -> None:

        for section, entries in (pb := tqdm(self.entry_sections)):
            xml = TlXml()
            pb.set_description(f'menu/{section}')

            for off, text, id in entries:
                xml.add_text(section, text, off)

            name = f'Eboot - {section}.xml'
            xml.save_xml(folder / name)

    def get_all_possible(self, f:FileIO, ptr_range: tuple[int, int]):
        pointers_offset: list[int] = []
        pointers_value: list[int] = []
        f.seek(ptr_range[0])

        while f.tell() < ptr_range[1]:
            memory_offset = f.read_uint32()
            file_offset = memory_offset - self.base_offset

            if file_offset > 0:
                prev = f.read_at(file_offset - 1, 1)

                if prev == b'\x00':
                    pointers_offset.append(f.tell() - 4)
                    pointers_value.append(file_offset)

        return pointers_offset, pointers_value

    def get_regular_pattern(self, f:FileIO, ptr_range: tuple[int, int], style: str):
        split: list[str] = [ele for ele in re.split(r'([PT])|(\d+)', style) if ele]
        pointers_offset: list[int] = []
        pointers_value: list[int] = []
        f.seek(ptr_range[0])

        while f.tell() < ptr_range[1]:
            for step in split:

                if step == "P":
                    off = f.read_uint32()
                    if self.base_offset != 0 and off == 0: continue

                    if f.tell() - 4 < ptr_range[1] and off - self.base_offset > 0:
                        pointers_offset.append(f.tell() - 4)
                        pointers_value.append(off - self.base_offset)

                elif step == "T":
                    off = f.tell()
                    pointers_offset.append(off)
                    pointers_value.append(off)
                else:
                    f.read(int(step))

        return pointers_offset, pointers_value

    def pack_file(self, destination_path:Path, xml_path:Path, list_status_insertion):

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.file_path, destination_path)
        pools = self.get_pools()

        with FileIO(destination_path, "r+b") as f:
            self.pack_menu_file(xml_path, pools, f, list_status_insertion)

    def pack_menu_file(self, xml_path:Path, pools: list[list[int]], f: FileIO, list_status_insertion, pad=False) -> None:


        entries = XML.load_xml_entries(xml_path, list_status_insertion)
        ptrs = [str(p) for p in range(0x1CB4EC, 0x1CB560, 4)]
        filters = [
            entry
            for entry in entries
            if not any(ptr in entry.pointer_offset for ptr in ptrs)
        ]
        for entry in filters:

            if entry.final_text == 'Lv':
                t = 2


            hi = []
            lo = []
            flat_ptrs = []

            if entry.pointer_offset != '':
                flat_ptrs = [int(x) for x in entry.pointer_offset.split(",")]

            if entry.mlen > 0:
                f.seek(flat_ptrs[0])
                text_bytes = text_to_bytes(entry)

                if len(text_bytes) > entry.mlen:
                    tqdm.write(
                        f"Line ({entry.eng_text}) too long, truncating...")
                    f.write(text_bytes[:entry.mlen - 1] + b"\x00")
                else:
                    f.write(text_bytes + (b"\x00" * (entry.mlen - len(text_bytes))))
                continue

            text_bytes = text_to_bytes(entry, 2)

            for pool in pools:

                if l <= pool[1]:
                    str_pos = pool[0]
                    pool[0] += l
                    pool[1] -= l
                    break
            else:
                print("Ran out of space")
                raise ValueError(f"Ran out of space {entry.final_text}")

            f.seek(str_pos)
            f.write(text_bytes)
            virt_pos = str_pos + self.base_offset

            for off in flat_ptrs:
                f.write_uint32_at(off, virt_pos)

    def get_pools(self):
        pools: list[list[int]] = [
            [reg.text_start - self.base_offset, reg.text_end - reg.text_start]
            for x in self.menu_sections for reg in x.regions]
        pools.sort(key=lambda x: x[1])
        return pools