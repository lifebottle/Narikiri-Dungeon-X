from .FileIO import FileIO
from .text_toh import text_to_bytes, bytes_to_text
import struct
class Bubble:

    def __init__(self, id:int, jap_text:str, eng_text:str, status:str = 'To Do', bytes = b''):
        self.eng_text = eng_text
        self.jap_text = jap_text
        self.id = id
        self.status = status
        self.bytes = bytes

class StructEntry:

    def __init__(self, pointer_offset:int, text_offset:int):
        self.pointer_offset = pointer_offset
        self.text_offset = text_offset
        self.pointer_offset_list = []
        self.sub_id = 1
        self.bubble_list = []



class StructNode:
    def __init__(self, id: int, pointer_offset: int, text_offset: int, tss: FileIO, strings_offset:int, file_size:int, section:str):
        self.id = id
        self.pointer_offset = pointer_offset
        self.pointer_offset_str = ''
        self.text_offset = text_offset
        self.strings_offset = strings_offset
        self.file_size = file_size
        self.section = section
        self.nb_unknowns = 0
        self.unknowns = []
        self.texts_entry = []
        self.end_unknowns = []
        self.speaker = Speaker(0,0)
        self.speaker.text = 'Variable'

        self.extract_struct_information(tss)

    def find_unknowns(self, tss:FileIO):

        first_entry = tss.read_uint32()
        second_entry = tss.read_uint32()
        third_entry = tss.read_uint32()

        if self.section == "Story":
            self.nb_unknowns = 2
        else:

            if 0x0 <= first_entry <= 0x20 and 0x0 <= second_entry <= 0x20:
                tss.seek(self.text_offset)
                if 0x0 <= third_entry <= 0x20:

                    if self.section == "Misc":
                        self.nb_unknowns = 10

                    else:
                        self.nb_unknowns = 6

    def extract_struct_information(self, tss: FileIO):

        #Test if first entries are unknown values to be kept
        tss.seek(self.text_offset)
        if self.pointer_offset == 75404:
            t = 2
        if tss.tell() <= (self.file_size - 12):
            self.find_unknowns(tss)

        tss.seek(self.text_offset)
        for _ in range(self.nb_unknowns):
            self.unknowns.append(tss.read_uint32())

        if self.section == "Story" or (self.section == "NPC" and self.nb_unknowns > 0):

            pointer_offset = tss.tell()
            self.extract_speaker_information(tss, pointer_offset)
            tss.seek(pointer_offset + 4)


        self.extract_texts_information(tss)


    def extract_speaker_information(self, tss:FileIO, pointer_offset:int):
        offset = tss.read_uint32() + self.strings_offset
        self.speaker = Speaker(pointer_offset, offset)
        tss.seek(offset)
        self.speaker.jap_text, self.speaker.bytes = bytes_to_text(tss, offset)

    def extract_bubbles(self, text, entry_bytes:bytes):
        bubble_id = 1
        text_split = text.split('<Bubble>')
        bytes_split = entry_bytes.split(b'\x0C')
        bubble_list = []
        for text, bubble_bytes in zip(text_split, bytes_split):
            bubble = Bubble(id=bubble_id, jap_text=text, eng_text='', bytes=bubble_bytes)
            bubble_list.append(bubble)
            bubble_id += 1

        return bubble_list
    def extract_texts_information(self, tss:FileIO):
        offset = tss.tell()

        normal_text = False
        sub_id = 1
        if offset <= self.file_size-4:


            val = tss.read_uint32()
            if val + self.strings_offset < self.file_size:
                while val != 0 and val != 0x1 and val < self.file_size:
                    pointer_offset = tss.tell()-4
                    text_offset = val + self.strings_offset
                    entry = StructEntry(pointer_offset, text_offset)
                    tss.seek(text_offset)
                    jap_text, bytes = bytes_to_text(tss, text_offset)


                    entry.bubble_list = self.extract_bubbles(jap_text, bytes)
                    entry.sub_id = sub_id
                    self.texts_entry.append(entry)
                    sub_id += 1

                    tss.seek(pointer_offset + 4)

                    if tss.tell() < self.file_size - 4:
                        val = tss.read_uint32()

                        if val == 0x1 or val == 0x0:
                            self.end_unknowns.append(val)
                    else:
                        break
            else:
                normal_text = True
        else:
            normal_text = True

        if normal_text:
            entry = StructEntry(self.pointer_offset, self.text_offset)
            jap_text, bytes = bytes_to_text(tss, self.text_offset)
            entry.bubble_list = self.extract_bubbles(jap_text, bytes)
            self.texts_entry.append(entry)

    def parse_xml_nodes(self, xml_nodes_list, list_status_insertion):
        self.id = int(xml_nodes_list[0].find("Id").text)

        max_sub_id = max([int(entry.find("SubId").text) for entry in xml_nodes_list])

        for sub_id in range(1, max_sub_id + 1):

            sub_nodes = [sub for sub in xml_nodes_list if int(sub.find('SubId').text) == sub_id]
            max_bubble_id = max([int(entry.find('BubbleId').text) for entry in sub_nodes])
            for bubble_id in range(1, max_bubble_id + 1):
                bubble = [bubble for bubble in sub_nodes if int(bubble.find('BubbleId').text) == bubble_id][0]
                entry_bytes, japanese_text, final_text, status = self.get_node_bytes(bubble, list_status_insertion, pad=False)

                self.texts_entry[sub_id-1].bubble_list[bubble_id-1].jap_text = japanese_text
                self.texts_entry[sub_id-1].bubble_list[bubble_id-1].eng_text = final_text
                self.texts_entry[sub_id-1].bubble_list[bubble_id-1].status = status
                self.texts_entry[sub_id-1].bubble_list[bubble_id-1].bytes = entry_bytes
    def intersperse(self, my_list, item):
        result = [item] * (len(my_list) * 2 - 1)
        result[0::2] = my_list
        return result

    def adjust_bubble(self, entry):
        buffer = b''
        buffer_text = ''
        nb_entries = len(entry.bubble_list)

        for entry_node in entry.bubble_list:
            bytes_text, text = self.get_node_bytes(entry_node.eng_text)
            buffer += bytes_text
            buffer_text += text

            if nb_entries >= 2:
                buffer += b'\x0C'
                buffer_text += '<Bubble>'
        return buffer, buffer_text

    def pad(self, offset:int, nb_bytes):
        rest = nb_bytes - offset % nb_bytes
        return (b'\x00' * rest)

    def add_speaker_entry(self, speaker_dict:dict, speaker_id:int):

        speaker_found = [speaker for id, speaker in speaker_dict.items() if speaker.jap_text == self.speaker.jap_text]

        if speaker_id == 16:
            t =2

        if len(speaker_found) > 0:
            self.speaker = speaker_found[0]

            if str(self.speaker.pointer_offset) not in speaker_found[0].pointer_offset_list:
                speaker_found[0].pointer_offset_list.append(str(self.speaker.pointer_offset))
            return speaker_id
        else:
            self.speaker.id = speaker_id
            speaker_dict[speaker_id] = self.speaker
            return speaker_id+1


    def get_node_bytes(self, entry_node, list_status_insertion, pad=False) -> (bytes, str):

        # Grab the fields from the Entry in the XML
        #print(entry_node.find("JapaneseText").text)
        status = entry_node.find("Status").text
        japanese_text = entry_node.find("JapaneseText").text
        english_text = entry_node.find("EnglishText").text

        # Use the values only for Status = Done and use English if non-empty
        final_text = ''
        if (status in list_status_insertion):
            final_text = english_text or ''
        else:
            final_text = japanese_text or ''

        voiceid_node = entry_node.find("VoiceId")

        if voiceid_node is not None:
            final_text = f'<{voiceid_node.text}>' + final_text

        # Convert the text values to bytes using TBL, TAGS, COLORS, ...
        bytes_entry = text_to_bytes(final_text)

        #Pad with 00
        if pad:
            rest = 4 - len(bytes_entry) % 4 - 1
            bytes_entry += (b'\x00' * rest)

        return bytes_entry, japanese_text, final_text, status

    def write_entries(self, tss):

        for entry in self.texts_entry:
            bubble_bytes = [bubble.bytes for bubble in entry.bubble_list]
            buffer = b''.join(self.intersperse(bubble_bytes, b'\x0C'))
            entry.text_offset = tss.tell()
            tss.write(buffer)
            tss.write(b'\x00')

    def write_unknowns(self, tss):
        for val in self.unknowns:
            tss.write(struct.pack('<I', val))

    def write_speaker_pointer(self, tss, speaker_dict):
        if self.speaker:

            if self.speaker.jap_text == 'イヌ':
                t = 2

            tss.write(struct.pack('<I', speaker_dict[self.speaker.id].text_offset - self.strings_offset))


    def write_entry_pointers(self, tss):

        for entry in self.texts_entry:
            tss.write(struct.pack('<I', entry.text_offset - self.strings_offset))

    def write_end_unknowns(self, tss):
        for unk in self.end_unknowns:
            tss.write(struct.pack('<I', unk))

    def pack_node(self, tss, speaker_dict:dict):
        self.text_offset = tss.tell()
        self.write_entries(tss)

        if self.nb_unknowns > 0:
            tss.write(self.pad(tss.tell(), 4))
            self.text_offset = tss.tell()
            self.write_unknowns(tss)
            self.write_speaker_pointer(tss, speaker_dict)
            self.write_entry_pointers(tss)
            self.write_end_unknowns(tss)

        offset = tss.tell()
        tss.seek(self.pointer_offset)
        tss.write(struct.pack('<I', self.text_offset - self.strings_offset))
        tss.seek(offset)


class Speaker(StructNode):

    def __init__(self, pointer_offset:int, text_offset:int):
        self.pointer_offset_list = []
        self.pointer_offset = pointer_offset
        self.text_offset = text_offset
        self.id = ''
        self.jap_text = 'Variable'
        self.eng_text = ''
        self.bytes = b''
        self.status = 'To Do'

    def set_node_attributes(self, node, list_status_insertion):
        speaker_id = int(node.find("Id").text)
        bytes_entry, jap_text, final_text, status = self.get_node_bytes(node, list_status_insertion)
        self.id = speaker_id
        self.bytes = bytes_entry
        self.jap_text = jap_text
        self.eng_text = final_text
        self.status = status