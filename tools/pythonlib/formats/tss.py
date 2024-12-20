from dataclasses import dataclass
import struct
from typing import Optional
from .FileIO import FileIO
from .structnode import StructNode, Speaker, Bubble
import os
from pathlib import Path
import re
import io
import lxml.etree as etree
import string
import subprocess
from itertools import groupby

bytecode_dict = {
    "Story": [b'\x0E\x10\x00\x0C\x04', b'\x00\x10\x00\x0C\x04'],
    "NPC": [b'\x40\x00\x0C\x04', b'\x0E\x00\x00\x82\x02'],
    "Misc": [b'\x00\x00\x00\x82\x02', b'\x01\x00\x00\x82\x02', b'\x00\xA3\x04']
}


class Tss():
    def __init__(self, path:Path, list_status_insertion) -> None:
        self.align = False
        self.files = []
        self.file_size = os.path.getsize(path)
        self.offsets_used = []
        self.struct_dict = {}
        self.speaker_dict = {}

        self.id = 1
        self.struct_id = 1
        self.speaker_id = 1
        self.root = etree.Element('SceneText')
        self.list_status_insertion = list_status_insertion
        self.VALID_VOICEID = [r'(<VSM_\w+>)', r'(<VCT_\w+>)', r'(<S\d+>)', r'(<C\d+>)']
        self.COMMON_TAG = r"(<[\w/]+:?\w+>)"
        self.HEX_TAG = r"(\{[0-9A-F]{2}\})"
        self.PRINTABLE_CHARS = "".join(
            (string.digits, string.ascii_letters, string.punctuation, " ")
        )

        with FileIO(path) as tss_f:

            tss_f.read(12)
            self.strings_offset = struct.unpack('<I', tss_f.read(4))[0]
            tss_f.read(4)

            self.create_struct_nodes(tss_f)
    def extract_all_pointers(self, f):

        self.id = 1
        for section, bytecode_list in bytecode_dict.items():
            for bytecode in bytecode_list:
                regex = re.compile(bytecode)
                f.seek(0)
                data = f.read()

                for match_obj in regex.finditer(data):
                    offset = match_obj.start()
                    pointer_offset = offset + len(bytecode)


                    f.seek(pointer_offset, 0)
                    text_offset = struct.unpack('<H', f.read(2))[0] + self.strings_offset
                    struct_node = StructNode(id=self.id, pointer_offset=pointer_offset,
                                              text_offset=text_offset,
                                              tss=f, strings_offset=self.strings_offset, file_size=self.file_size,
                                           section=section)
                    self.speaker_id = struct_node.add_speaker_entry(self.speaker_dict, self.speaker_id)
                    self.struct_dict[pointer_offset] = struct_node
                    self.id += 1



    def create_struct_nodes(self, f_tss:FileIO):


        self.extract_all_pointers(f_tss)


    def find_struct_speaker(self, f:FileIO, pointer_offset:int):
        struct_found = [struct_entry for pointer_offset, struct_entry in self.struct_dict.items() if struct_entry.pointer_offset == pointer_offset]

        if len(struct_found) > 0:
            text_offset = struct_found[0].speaker.text_offset
            jap_text = self.bytes_to_text(f, text_offset)
            return jap_text
        else:
            return 'Variable'


    def add_offset_adjusted(self, start, end):
        self.offsets_used.extend(list(range(start, end)))

    def create_first_nodes(self):

        story_count = len([node for node in self.struct_dict.values() if node.section == "Story"])
        npc_count = len([node for node in self.struct_dict.values() if node.section == "NPC"])
        string_count = len([node for node in self.struct_dict.values() if node.section == "Misc"])

        if story_count >0 or npc_count > 0:
            speakers_node = etree.SubElement(self.root, 'Speakers')
            etree.SubElement(speakers_node, 'Section').text = "Speaker"

        if story_count > 0:
            story_node = etree.SubElement(self.root, 'Strings')
            etree.SubElement(story_node, 'Section').text = "Story"

        if npc_count > 0:
            npc_node = etree.SubElement(self.root, 'Strings')
            etree.SubElement(npc_node, 'Section').text = "NPC"

        #if string_count > 0:
        #    string_node = etree.SubElement(self.root, 'StringsMisc')
        #    etree.SubElement(string_node, 'Section').text = "Misc"
    def extract_to_xml(self, original_path, translated_path, keep_translations=False):

        self.create_first_nodes()

        self.add_speaker_nodes()

        #Split with bubble the entries
        for pointer_offset in sorted(self.struct_dict.keys()):
            struct_obj = self.struct_dict[pointer_offset]

            if struct_obj.section != 'Misc':
                for struct_text in struct_obj.texts_entry:
                    for bubble in struct_text.bubble_list:
                        self.create_entry(struct_node=struct_obj, bubble=bubble, subid=struct_text.sub_id)



        # Write the original data into XML
        txt = etree.tostring(self.root, encoding="UTF-8", pretty_print=True)
        with open(original_path, "wb") as xmlFile:
            xmlFile.write(txt)

        if keep_translations:
            self.copy_translations(original_path, translated_path)

    def add_speaker_nodes(self):
        speakers = self.root.find('Speakers')

        for speaker_id, speaker_node in self.speaker_dict.items():
            entry_node = etree.SubElement(speakers, "Entry")
            etree.SubElement(entry_node, "PointerOffset")
            etree.SubElement(entry_node, "JapaneseText").text = speaker_node.jap_text
            etree.SubElement(entry_node, "EnglishText")
            etree.SubElement(entry_node, "Notes")
            etree.SubElement(entry_node, "Id").text = str(speaker_id)
            etree.SubElement(entry_node, "Status").text = 'To Do'

    def create_entry(self, struct_node:StructNode, bubble:Bubble, subid=None):

        # Add it to the XML node
        if struct_node.section == 'Misc':
            strings_node = self.root.find(f'StringsMisc[Section="Misc"]')
        else:
            strings_node = self.root.find(f'Strings[Section="{struct_node.section}"]')

        entry_node = etree.SubElement(strings_node, "Entry")
        etree.SubElement(entry_node, "PointerOffset").text = str(struct_node.pointer_offset)
        text_split = re.split(self.COMMON_TAG, bubble.jap_text)

        if len(text_split) > 1 and any(re.match(possible_value, bubble.jap_text)  for possible_value in self.VALID_VOICEID):
            etree.SubElement(entry_node, "VoiceId").text = text_split[1].replace('<','').replace('>','')
            etree.SubElement(entry_node, "JapaneseText").text = ''.join(text_split[2:])
        else:
            etree.SubElement(entry_node, "JapaneseText").text = bubble.jap_text

        etree.SubElement(entry_node, "EnglishText")
        etree.SubElement(entry_node, "Notes")

        if int(struct_node.speaker.id) > 0:
            etree.SubElement(entry_node, "SpeakerId").text = str(struct_node.speaker.id)
        etree.SubElement(entry_node, "Id").text = str(struct_node.id)

        if struct_node.section in ["Story", "NPC"]:
            etree.SubElement(entry_node, "BubbleId").text = str(bubble.id)
            etree.SubElement(entry_node, "SubId").text = str(subid)

        etree.SubElement(entry_node, "Status").text = "To Do"
        self.id += 1

    def find_xml_nodes(self, pointer_offset:int):
        node_found = [struct_node for key, struct_node in self.struct_dict.items()
                      if struct_node.pointer_offset == pointer_offset]

        if len(node_found) > 0:
            return node_found

    def parse_write_speakers(self, tss:io.BytesIO):

        for speaker_node in self.root.findall("Speakers/Entry"):



            text_offset = tss.tell()
            speaker = Speaker(pointer_offset=0, text_offset=text_offset)
            speaker.set_node_attributes(speaker_node, self.list_status_insertion)
            speaker.text_offset = tss.tell()
            self.speaker_dict[speaker.id] = speaker
            tss.write(speaker.bytes)
            tss.write(b'\x00')

    def parse_xml_infos(self):

        struct_entries = self.root.findall('Strings/Entry')
        pointers_list = list(set([int(entry.find("PointerOffset").text) for entry in struct_entries]))

        pointers_list.sort()

        for pointer_offset in pointers_list:
            entries = [entry for entry in struct_entries if int(entry.find("PointerOffset").text) == pointer_offset]
            self.struct_dict[pointer_offset].parse_xml_nodes(entries, self.list_status_insertion)

    def copy_translations(self, original_path:Path, translated_path:Path):

        #Open translated XMLs
        tree = etree.parse(original_path)
        root_original = tree.getroot()

        tree = etree.parse(translated_path)
        root_translated = tree.getroot()
        translated_speakers = {int(entry.find('Id').text):entry for entry in root_translated.findall('Speakers/Entry')
                              if entry.find("Status").text in ['Proofread', 'Edited', 'Done']}
        translated_entries = {(int(entry.find('PointerOffset').text),
                               int(entry.find("SubId").text),
                               int(entry.find("BubbleId").text)):entry for entry in root_translated.findall('Strings/Entry')
                            if entry.find("Status").text in ['Proofread', 'Edited', 'Done']}
        original_entries = {(int(entry.find('PointerOffset').text),
                               int(entry.find("SubId").text),
                               int(entry.find("BubbleId").text)): entry for entry in
                              root_original.findall('Strings/Entry')}

        #Speakers
        for speaker_entry in [entry for entry in root_original.findall('SceneText/Speakers/Entry')
                              if int(entry.find('Id').text) in translated_speakers.keys()]:

            speaker_id = int(speaker_entry.find("Id").text)
            speaker_entry.find("EnglishText").text = translated_speakers[speaker_id].find('EnglishText').text
            speaker_entry.find("Status").text = translated_speakers[speaker_id].find('Status').text
            notes = translated_speakers[speaker_id].find('Notes')

            if notes is not None:
                speaker_entry.find("Notes").text = translated_speakers[speaker_id].find('Notes').text


        #Main entries
        original_entries_translated = {(pointer_offset, sub_id, bubble_id):node for (pointer_offset, sub_id, bubble_id), node in original_entries.items()
                                       if (pointer_offset, sub_id, bubble_id) in translated_entries.keys()}
        for (pointer_offset, sub_id, bubble_id), main_entry in original_entries_translated.items():
            translated_entry = translated_entries[(pointer_offset, sub_id, bubble_id)]

            main_entry.find("EnglishText").text = translated_entry.find('EnglishText').text
            main_entry.find("Status").text = translated_entry.find('Status').text
            notes = translated_entry.find('Notes').text

            if notes is not None:
                main_entry.find("Notes").text = translated_entries[pointer_offset].find('Notes').text

        txt = etree.tostring(root_original, encoding="UTF-8", pretty_print=True)
        with open(translated_path, "wb") as xmlFile:
            xmlFile.write(txt)


    def pack_tss_file(self, destination_path:Path, xml_path:Path):



        # Grab the Tss file inside the folder
        with FileIO(destination_path, 'rb') as original_tss:
            data = original_tss.read()
            tss = io.BytesIO(data)
            tree = etree.parse(xml_path)
            self.root = tree.getroot()

            start_offset = self.get_starting_offset()
            tss.seek(start_offset, 0)
            self.parse_write_speakers(tss)
            self.parse_xml_infos()

            #Insert all nodes
            [node.pack_node(tss, self.speaker_dict) for pointer_offset, node in self.struct_dict.items()]

            #Update TSS
            with FileIO(destination_path, 'wb') as f:
               f.write(tss.getvalue())

    def get_starting_offset(self):
        speaker_offset = min([ele.speaker.text_offset for pointer_offset, ele in self.struct_dict.items() if ele.speaker.text_offset > 0], default=None)

        texts_offset = [text_entry.text_offset for key, struct_entry in self.struct_dict.items() for text_entry in struct_entry.texts_entry]
        texts_offset.sort()
        text_offset = min(texts_offset[1:], default=None)
        return min(speaker_offset or 100000000, text_offset)