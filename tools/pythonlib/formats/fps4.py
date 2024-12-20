import shutil
from dataclasses import dataclass
import struct
from typing import Optional
from .FileIO import FileIO
import os
from pathlib import Path
import subprocess


@dataclass
class fps4_file():
    c_type:str
    data:bytes
    name:str
    size:int
    rank:int
    offset:int

dict_buffer = {
    0x2C:16,
    0x28:32
}

class Fps4():

    def __init__(self, header_path:Path , detail_path:Path = None, size_adjusted = 0) -> None:
        self.type = -1
        self.align = False
        self.files = []
        self.header_path = header_path
        self.file_size = os.path.getsize(header_path)
        self.detail_path = detail_path or header_path
        self.size_adjusted = size_adjusted

        self.extract_information()

    def extract_information(self):
        with FileIO(self.header_path) as f_header:
            self.header_data = f_header.read()
            f_header.seek(4,0)
            self.file_amount = f_header.read_uint32()-1
            self.header_size = f_header.read_uint32()
            self.offset = f_header.read_uint32()
            self.block_size = f_header.read_uint16()

            self.files = []


            if self.offset == 0x0:
                self.pack_file = self.pack_fps4_type1

                if self.block_size == 0x2C:
                    self.read_more = True
                    self.extract_type1_fps4(f_header=f_header)

                elif self.block_size == 0x28:
                    self.read_more = False
                    self.extract_type1_fps4(f_header=f_header)

            else:
                self.pack_file = self.pack_fps4_type1
                self.extract_type2_fps4(f_header=f_header)
    #Type 2 = Header with File offset
    def extract_type2_fps4(self, f_header:FileIO):

        #Read all the files offsets
        files_offset = []
        f_header.seek(self.header_size,0)
        for _ in range(self.file_amount):
            files_offset.append(f_header.read_uint32())
        files_offset.append(self.file_size)

        #Create each file
        for i in range(len(files_offset)-1):
            f_header.seek(files_offset[i], 0)
            size = files_offset[i+1] - files_offset[i]
            data = f_header.read(size)
            c_type = 'None'

            if data[0] == 0x10:
                c_type = 'LZ10'
            elif data[0] == 0x11:
                c_type = 'LZ11'

            self.files.append(fps4_file(c_type, data, f'{i}.bin', size, i, files_offset[i]))


    #Type 1 = Header + Detail
    def extract_type1_fps4(self, f_header:FileIO):
        self.type = 1
        files_infos = []
        f_header.seek(self.header_size, 0)

        with FileIO(self.detail_path) as det:
            for _ in range(self.file_amount):
                offset = f_header.read_uint32()
                size = f_header.read_uint32()

                if self.read_more:
                    f_header.read_uint32()
                name = f_header.read(32).decode("ASCII").strip('\x00')
                files_infos.append((offset, size, name))

            i=0
            for offset, size, name in files_infos:
                #print(f'name: {name} - size: {size}')

                det.seek(offset)
                data = det.read(size)

                c_type = 'None'
                if data[0] == 0x10:
                    c_type = 'LZ10'
                elif data[0] == 0x11:
                    c_type = 'LZ11'

                self.files.append(fps4_file(c_type, data, name, size, i, offset))
                i+=1

    def extract_files(self, destination_path:Path, copy_path:Path, decompressed=False):

        destination_path.mkdir(parents=True, exist_ok=True)
        for file in self.files:

            copy_path.mkdir(parents=True, exist_ok=True)
            with open(destination_path / file.name, "wb") as f:
                f.write(file.data)

            shutil.copy(destination_path / file.name, copy_path / file.name)

            #Decompress using LZ10 or LZ11
            if file.c_type == "LZ10":
                args = [Path.cwd() / 'tools/pythonlib/utils/lzss', '-d', destination_path / file.name]
                subprocess.run(args, stdout = subprocess.DEVNULL)

            elif file.c_type == "LZ11":
                args = [Path.cwd() / 'tools/pythonlib/utils/lzx', '-d', destination_path / file.name]
                subprocess.run(args, stdout=subprocess.DEVNULL)

            with open(destination_path / file.name, 'rb') as f:
                head = f.read(4)

                if head == b'FPS4':
                    file.file_extension = 'FPS4'
                elif head[:-1] == b'TSS':
                    file.file_extension = 'TSS'

    def compress_file(self, updated_file_path:Path, file_name:str, c_type:str):
        args = []
        if c_type == 'LZ10':
            args = [Path.cwd() / 'tools/pythonlib/utils/lzss', '-evn', updated_file_path / file_name]
        elif c_type == "LZ11":
            args = [Path.cwd() / 'tools/pythonlib/utils/lzx', '-evb', updated_file_path / file_name]
        subprocess.run(args, stdout = subprocess.DEVNULL)

    def pack_fps4_type1(self, updated_file_path:Path, destination_folder:Path):
        buffer = 0

        #Update detail file
        self.files.sort(key= lambda file: file.offset)

        with FileIO(destination_folder / self.detail_path.name, "wb") as fps4_detail:

            #Writing new dat file and updating file attributes
            for file in self.files:

                #self.compress_file(updated_file_path, file_name=file.name, c_type=file.c)

                with FileIO(updated_file_path / file.name, 'rb') as sub_file:
                    file.data = sub_file.read()
                    file.offset = buffer
                    file.size = len(file.data)
                    buffer += file.size
                    fps4_detail.write(file.data)

        #Update header file
        with FileIO(self.header_data, "r+b") as fps4_header:

            fps4_header.seek(self.header_size,0)
            self.files.sort(key= lambda file: file.rank)
            for file in self.files:
                fps4_header.write(struct.pack('<L', file.offset))
                fps4_header.write(struct.pack('<L', file.size))

                if self.read_more:
                    fps4_header.seek(fps4_header.tell()+4,0)
                    #fps4_header.write(struct.pack('<L', file.size))

                fps4_header.write(file.name.encode())
                fps4_header.write(b'\x00' * (32 - (len(file.name) % 32)))

            fps4_header.write(struct.pack('<L', buffer) + b'\x00' * 12)

            with FileIO(destination_folder / self.header_path.name, "wb") as f_header:
                fps4_header.seek(0,0)
                f_header.write(fps4_header.read())

    def pack_fps4_bg(self, updated_file_path:Path, destination_folder:Path):
        buffer = 0

        #Update detail file
        map = {
            "CC": "NCGR",
            "SS": "NSCR",
            "PP": "NCLR",
            "NCGR": "NCGR",
            "NSCR": "NSCR",
            "NCLR": "NCLR"
        }

        #list all files in folder with new extension
        shutil.copytree(src=Path.cwd() / '2_translated' / 'menu_bg', dst=updated_file_path, dirs_exist_ok=True)
        new_files = [ele.name for ele in updated_file_path.iterdir()]

        self.files.sort(key= lambda file: file.offset)
        with FileIO(destination_folder / self.detail_path.name, "wb") as fps4_detail:

            #Writing new dat file and updating file attributes
            for file in self.files:
                file_split = file.name.split('.')

                if file_split[1] in map.keys():
                    new = file_split[0] + f'.{map[file_split[1]]}'

                    if new in new_files:
                        self.compress_file(updated_file_path, file_name=new, c_type=file.c_type)
                        with FileIO(updated_file_path / new, 'rb') as sub_file:
                            file.data = sub_file.read()

                file.offset = buffer
                file.size = len(file.data)
                buffer += file.size
                fps4_detail.write(file.data)

        #Update header file
        with FileIO(self.header_data, "r+b") as fps4_header:

            fps4_header.seek(self.header_size,0)
            self.files.sort(key= lambda file: file.rank)
            for file in self.files:
                fps4_header.write(struct.pack('<L', file.offset))
                fps4_header.write(struct.pack('<L', file.size))

                if self.read_more:
                    fps4_header.seek(fps4_header.tell()+4,0)
                    #fps4_header.write(struct.pack('<L', file.size))

                fps4_header.write(file.name.encode())
                fps4_header.write(b'\x00' * (32 - (len(file.name) % 32)))

            fps4_header.write(struct.pack('<L', buffer) + b'\x00' * 12)

            with FileIO(destination_folder / self.header_path.name, "wb") as f_header:
                fps4_header.seek(0,0)
                f_header.write(fps4_header.read())


    def get_file_extension(self, file_path:Path):

        with open(file_path, "rb") as f:
            data = f.read(10)

            if data[:4] == b'FPS4':
                return 'FPS4'
            elif data[:3] == b'TSS':
                return 'TSS'

    def look_for_header(self, path:Path):

        base_name = os.path.basename(path).split('.')[0]
        header_found = [ele for ele in os.listdir(path.parent) if ele.endswith('.b') and ele.split('.')[0] == base_name]

        if len(header_found) > 0:
            print(f'header was found: {header_found[0]}')
            return path.parent / header_found[0]
        else:
            return None


    #def get_fps4_type(self):
