from ndx_tools.formats.xml import TlXml, TlNode
from ndx_tools.utils.fileio import FileIO
from ndx_tools.formats.xml import TlText
from ndx_tools.utils.string import bytes_to_text, text_to_bytes
from dataclasses import dataclass, field
from typing import Any, List, Tuple
import struct
import shutil
import pandas as pd
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
        self.split_sections = entry['split_sections']
        self.menu_sections = [
            MenuSection.from_dict(section)
            for section in entry.get("sections", [])
        ]
        self.entry_sections: List[Tuple[str, List]] = []
        self.id = 1

    @staticmethod
    def fetch_clean_section_name(section:str):
        first_occ = section.find("[")

        if first_occ > 0:
            return section[:first_occ-1]
        else:
            return section

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
        #self.entry_sections = []

        with FileIO(self.file_path, 'rb') as f:
            for section in self.menu_sections:
                self.extract_section_basic(section, f)

        #if keep_translations:
        #    self.copy_translations_menu(root_original=xml_root, translated_path=self.paths['menu_xml'] / f"{file_def['friendly_name']}.xml")


    def get_style_pointers(self, f:FileIO, ptr_range: tuple[int, int], style: str):

        if style == "*":
            return self.get_all_possible(f, ptr_range)

        else:
            return self.get_regular_pattern(f, ptr_range, style)



    def extract_section_basic(self, section: MenuSection, f:FileIO) -> None:

        # Extract Pointers list out of the file,
        pointers_offset, pointers_value, mlen = self.get_style_pointers(f, (section.pointers_start, section.pointers_end),
                                                                    section.style)
        if len(mlen) == 0:
            mlen = [0] * len(pointers_offset)

        # Make a list, we also merge the emb pointers with the
        # other kind in the case they point to the same text
        entries = []
        temp = dict()
        f.seek(0)
        for off, val, max_len in zip(pointers_offset, pointers_value, mlen):
            text = bytes_to_text(f, offset=val)
            temp.setdefault(text, dict()).setdefault("ptr", []).append(off)
            entries.append( (off, text, self.id, max_len))
            self.id = self.id + 1

        #if section.style[0] == "T":
        #    max_len = int(section.style[1:])

        # Remove duplicates
        #list_informations = [(k, str(v['ptr'])[1:-1], v.setdefault('emb', None)) for k, v in temp.items()]
        self.entry_sections.append((section.name, entries))

    def make_xml(self, folder: Path) -> None:

        xml = TlXml()
        for section, entries in (pb := tqdm(self.entry_sections)):

            pb.set_description(f'menu/{section}')

            for off, text, id, mlen in entries:
                xml.add_text(section, text, off, max_len=mlen)

            if self.split_sections:
                name = f'{self.friendly_name} - {section}.xml'
                xml.save_xml(folder / name)
                xml = TlXml()

        if not self.split_sections:
            name = f'{self.friendly_name}.xml'
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

        return pointers_offset, pointers_value, [0] * len(pointers_offset)

    def get_regular_pattern(self, f:FileIO, ptr_range: tuple[int, int], style: str):
        split: list[str] = [ele for ele in re.split(r'([PT])|(\d+)', style) if ele]
        pointers_offset: list[int] = []
        pointers_value: list[int] = []
        mlen: list[int] = []
        f.seek(ptr_range[0])

        while f.tell() < ptr_range[1]:
            for i, step in enumerate(split):

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
                    mlen.append(int(split[i+1]))
                else:
                    f.read(int(step))

        return pointers_offset, pointers_value, mlen

    def get_xmls_list(self):
        if self.split_sections:
            return [f'{self.friendly_name} - {sect.name}.xml' for sect in self.menu_sections]

        else:
            return f'{self.friendly_name}.xml'

    def get_sections_entries(self, tl_folder:Path):

        xmls = self.get_xmls_list()
        entries_list = []
        for xml in xmls:
            #if xml != 'Eboot - Synopsis.xml':
            entries = TlXml.load_entries(tl_folder / xml)
            entries_list.extend(entries)

        return entries_list

    def reinsert_file(self, destination_path:Path, tl_folder:Path, list_status_insertion):

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.file_path, destination_path)
        pools = self.get_pools2()

        with open(destination_path, "r+b") as f:

            entries = self.get_sections_entries(tl_folder)

            self.reinsert_file_with_pools(entries, pools, f, list_status_insertion)

    def reinsert_file_with_pools(self, entries:list[TlText], pools: list[list[int]], f, list_status_insertion, pad=False) -> None:

        inserted = 0
        for entry in entries:

            hi = []
            lo = []


            if entry.max_len > 0:
                off = next(iter(entry.offsets))
                f.seek(off)
                text_bytes = text_to_bytes(entry.text)

                if len(text_bytes) > entry.max_len:
                    tqdm.write(
                        f"Line ({entry.eng_text}) too long, truncating...")
                    f.write(text_bytes[:entry.max_len - 1] + b"\x00")
                else:
                    f.write(text_bytes + (b"\x00" * (entry.max_len - len(text_bytes))))
                continue

            text_bytes = text_to_bytes(entry.eng_text) + b'\x00'
            l = len(text_bytes)
            for pool in pools:

                if l <= pool[1]:
                    str_pos = pool[0]
                    pool[0] += l
                    pool[1] -= l
                    break
            else:
                print("Ran out of space")
                raise ValueError(f"Ran out of space {entry.eng_text}")

            f.seek(str_pos)
            f.write(text_bytes)
            virt_pos = str_pos + self.base_offset
            inserted += 1
            if entry.eng_text == 'Items':
                t = 2

            for off in entry.offsets:
                f.seek(off)
                f.write(struct.pack('<I', virt_pos))


    def get_pools(self):
        pools: list[list[int]] = []
        for sect in self.menu_sections:
            name = sect.name
            size = sect.text_areas[1] - sect.text_areas[0]

            if name in "Title Dio":
                p = [sect.text_areas[0], size]
                pools.append(p)

        pools.sort(key=lambda x: x[1])
        return pools

    def get_pools2(self):
        sheet_id = "15iwB_zRS86ovL7z25QYzVpM1cTO0b1a7IRzKaYOAxhM"
        gid = "418814154"

        url = (
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
            f"?format=csv&gid={gid}"
        )

        df = pd.read_csv(
            url,
            dtype=str,
            keep_default_na=False,
        )
        df = df[df['safe_section_start'] != '']

        pools = []
        for index, row in df.iterrows():
            start = int(row['safe_section_start'], 16)
            end = int(row['safe_section_end'], 16)
            size = end - start
            pools.append([start, size])

        pools.sort(key=lambda x: x[1])
        return pools