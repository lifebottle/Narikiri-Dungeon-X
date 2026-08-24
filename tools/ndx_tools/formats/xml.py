from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import ClassVar, Self

from loguru import logger
import lxml.etree as ET


class TlStatus(StrEnum):
    TO_DO = "To Do"
    EDITED = "Edited"
    PROOFREAD = "Proofread"
    PROBLEMATIC = "Problematic"
    DONE = "Done"


@dataclass
class TlName:
    id: int
    offsets: set[int] = field(default_factory=set)
    max_len: int = 0xFFFFFFFF
    eng_text: str | None = None
    status: str = TlStatus.TO_DO
    dedup: bool = True


@dataclass
class TlText:
    text: str | None
    id: int
    note: str | None = None
    voice: str | None = None
    subid: int | None = None
    name: TlName | None = None
    offsets: set[int] = field(default_factory=set)
    max_len: int = 0xFFFFFFFF
    eng_text: str | None = None
    status: str = TlStatus.TO_DO


@dataclass
class TlNode:
    jp_text: str
    en_text: str
    id: int


@dataclass
class TlRefPool:
    entries: list[str] = field(default_factory=list)
    by_text: dict[str, int] = field(default_factory=dict)

    def get_ref(self, string: str) -> int | None:
        return self.by_text.get(string)

    def get_ref_by_id(self, id: int) -> str | None:
        id -= 1
        if len(self.entries) < id:
            return None
        return self.entries[id]


@dataclass
class TlXml:
    _names: dict[str, TlName] = field(default_factory=dict)
    _text: defaultdict[str, list[TlText]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _common: ClassVar[dict[str, TlRefPool]] = {}

    @classmethod
    def serialize_entries(cls, nodes: list[ET._Element]) -> list[TlNode]:
        grouped = defaultdict(list)

        for entry in nodes:
            id_ = int(entry.findtext("Id"))
            jp = entry.findtext("JapaneseText") or ""
            en = entry.findtext("EnglishText") or ""
            voice = entry.findtext("VoiceId") or ""
            grouped[id_].append((voice + jp, voice + en))

        result = []

        for k, wins in grouped.items():
            jp = "<Bubble>".join(text for text, _ in wins)
            en = "<Bubble>".join(text for _, text in wins)
            result.append(TlNode(jp, en, k))

        return result

    @classmethod
    def _new_pool(cls, section: str, nodes: list[ET._Element]) -> TlRefPool:
        pool = TlRefPool()
        for node in cls.serialize_entries(nodes):
            jp = node.jp_text
            en = node.en_text
            id = node.id
            pool.by_text[jp] = id
            pool.entries.append(en)

        cls._common[section] = pool

    @classmethod
    def _get_ref(self, section: str, string: str) -> int | None:
        if section not in self._common:
            return None
        return self._common[section].get_ref(string)

    @classmethod
    def _get_ref_by_id(self, section: str, id: int) -> str | None:
        if section not in self._common:
            return None
        return self._common[section].get_ref_by_id(id)

    def _get_voice(self, line: str) -> tuple[str | None, str]:
        if line.startswith("<audio:"):
            end = line.find(">")
            if end != -1:
                tag = line[: end + 1]
                rest = line[end + 1 :]
                return tag, rest
        return None, line

    def add_text(
        self,
        section: str,
        text: str | None,
        offset: int,
        max_len: int = 0xFFFFFFFF,
        note: str | None = None,
        name: TlName | None = None,
    ) -> None:
        if text is None:
            return

        sect = self._text[section]
        id = len(sect) + 1

        if rid := self._get_ref(section, text):
            entry = TlText(None, id, max_len=max_len)
            entry.status = f"ref:{section}:{rid}"
            entry.offsets.add(offset)
            sect.append(entry)
            return

        parts = text.split("<Bubble>")
        has_multiple = len(parts) > 1

        for i, line in enumerate(parts):
            voice, rest = self._get_voice(line)
            entry = TlText(rest, id, max_len=max_len)
            entry.subid = i if has_multiple else None
            entry.name = name
            entry.note = note
            entry.voice = voice
            entry.offsets.add(offset)
            sect.append(entry)

    def add_name(
        self, name: str, offset: int, max_len: int = 0xFFFFFFFF
    ) -> TlName | None:
        if name is None or offset is None:
            return None

        if name not in self._names:
            self._names[name] = TlName(id=len(self._names) + 1)
        item = self._names[name]
        item.offsets.add(offset)
        item.max_len = max_len
        return item

    def _make_speakers(self) -> ET._Element | None:
        if len(self._names) == 0:
            return None

        spkrs = ET.Element("Speakers")
        ET.SubElement(spkrs, "Section").text = "Speaker"
        for name, data in self._names.items():
            entry = ET.SubElement(spkrs, "Entry")
            if data.dedup and (rid := self._get_ref("Speaker", name)):
                offsets = None
                name = None
                en_text = None
                status = f"ref:Speaker:{rid}"
            else:
                offsets = ",".join([str(x) for x in sorted(data.offsets)])
                en_text = data.eng_text
                status = TlStatus.TO_DO

            ET.SubElement(entry, "PointerOffset").text = offsets
            if data.max_len != 0xFFFFFFFF:
                ET.SubElement(entry, "MaxLen").text = str(data.max_len)
            ET.SubElement(entry, "JapaneseText").text = name
            ET.SubElement(entry, "EnglishText").text = en_text
            ET.SubElement(entry, "Notes")
            ET.SubElement(entry, "Id").text = str(data.id)
            ET.SubElement(entry, "Status").text = status
        return spkrs

    def _make_strings(self) -> list[ET._Element]:
        out = []
        for name, lines in self._text.items():
            strings = ET.Element("Strings")
            ET.SubElement(strings, "Section").text = name
            out.append(strings)

            for line in lines:
                entry = ET.SubElement(strings, "Entry")
                if line.offsets:
                    offsets = ",".join([str(x) for x in sorted(line.offsets)])
                else:
                    offsets = None
                ET.SubElement(entry, "PointerOffset").text = offsets
                if line.voice:
                    ET.SubElement(entry, "VoiceId").text = line.voice
                ET.SubElement(entry, "JapaneseText").text = line.text
                ET.SubElement(entry, "EnglishText").text = line.eng_text
                ET.SubElement(entry, "Notes").text = line.note
                if line.name:
                    line.name.dedup = False
                    ET.SubElement(entry, "SpeakerId").text = str(line.name.id)
                ET.SubElement(entry, "Id").text = str(line.id)
                if line.subid is not None:
                    ET.SubElement(entry, "BubbleId").text = str(line.subid)
                ET.SubElement(entry, "Status").text = line.status

        return out

    def save_xml(self, path: Path) -> None:
        root = ET.Element("SceneText")
        for x in self._text["Notice"]:
            if x.name:
                x.name.dedup = True

        strings = self._make_strings()
        speaker = self._make_speakers()

        if speaker is not None:
            root.append(speaker)

        for string in strings:
            root.append(string)

        txt = ET.tostring(
            root, encoding="UTF-8", pretty_print=True, xml_declaration=True
        )
        with path.open("wb") as xmlFile:
            xmlFile.write(txt)

    @classmethod
    def load_common(cls, path: Path) -> None:
        if not path.exists():
            logger.warning(f"Couldn't load common xml at {path}")
            return

        xml = ET.parse(path)
        root = xml.getroot()
        for node in root.xpath("Strings|Speakers"):
            cls._new_pool(node.findtext("Section"), node.findall("Entry"))

    @classmethod
    def load_xml(cls, path: Path) -> Self:
        xml = ET.parse(path)
        root = xml.getroot()
        for foo in root.xpath("Strings|Speakers"):
            for node in foo.findall("Entry"):
                status: str = node.findtext("Status")
                if status.startswith("ref:"):
                    _, section, _id = status.split(":")
                    print(cls._get_ref_by_id(section, int(_id)))
                else:
                    print(node.findtext("JapaneseText"))
        # return x
