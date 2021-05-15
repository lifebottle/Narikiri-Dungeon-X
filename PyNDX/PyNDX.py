from tkinter import *
from tkinter import filedialog
import tkinter.messagebox as box

import webbrowser

def callback(url):
    webbrowser.open_new(url)

def extract_filenames():
    input_file = open('ULJS00293.BIN', 'rb')
    output_file = open('filenames.txt', 'w')

    #Extracts filenames to text
    offset_start = 0x187AD0
    offset_end = 0x18C41F

    input_file.seek(offset_start)
    data = input_file.read(offset_end - offset_start)
    
    #Replace NULL bytes with new line
    data = data.replace(b'\x00\x00\x00\x00', b'\x0A')
    data = data.replace(b'\x00\x00\x00', b'\x0A')
    data = data.replace(b'\x00\x00', b'\x0A')
    data = data.replace(b'\x00', b'\x0A')

    output_file.write(data.decode('ascii'))
        
    output_file.close()
    input_file.close()

def get_hash(file_name):
    name_hash = 0
    for char in list(file_name.upper()):
        name_hash = ((name_hash << 7) + name_hash) + (name_hash << 3) + ord(char)
    return ("%X" % (name_hash & 0xFFFFFFFF))

    #print("%X" % get_hash(file_name))
    #file_name = "sysdata/font1.gim"

def extract_files(start,end,filename):
    input_file = open('ULJS00293.BIN', 'rb')

    input_file.seek(start)
    data1 = input_file.read(end - start)
    output_file01 = open(filename, 'wb')
    output_file01.write(data1)
    output_file01.close()

    input_file.close()

def get_eboot_gim():
    extract_files(0x205970,0x206B9F,"01.gim")
    extract_files(0x206BA0,0x20796F,"02.gim")
    extract_files(0x207970,0x207BFF,"03.gim")
    extract_files(0x207C00,0x207E8F,"04.gim")
    extract_files(0x207E90,0x20801F,"05.gim")
    extract_files(0x208020,0x2081AF,"06.gim")
    extract_files(0x2081B0,0x20833F,"07.gim")
    extract_files(0x208340,0x208C0F,"08.gim")
    extract_files(0x208C10,0x208D9F,"09.gim")
    extract_files(0x208DA0,0x2090FF,"10.gim")

"""
Graphical Interface Start
"""

from topx import *

window = Tk()
#window.iconbitmap("favicon.ico")
window.title("PyNDX - Tales of Phantasia: Narikiri Dungeon X Utility")

label = Label(window, text = "PyNDX Utility Extracts Files from PSP game Narikiri Dungeon X")
label.grid(row=0, column=0, columnspan=4)

frame1 = LabelFrame(window, text="Extract", padx=5, pady=5)
frame1.grid(row=1, column=0, padx=10, pady=10)

btn_unpackFPB = Button(frame1, text="Extract all.dat", command = extract_all_dat)
btn_unpackFPB.grid(row=0, column=0)


window.mainloop()
