#pyinstaller --onefile --noconsole --icon favicon.ico PyNDX.py

from tkinter import *
from tkinter import filedialog
import tkinter.messagebox as box

import webbrowser

def callback(url):
    webbrowser.open_new(url)

def get_hash(file_name):
    name_hash = 0
    for char in list(file_name.upper()):
        name_hash = ((name_hash << 7) + name_hash) + (name_hash << 3) + ord(char)
    return ("%08X" % (name_hash & 0xFFFFFFFF))

    #print("%X" % get_hash(file_name))
    #file_name = "sysdata/font1.gim"

def extract_files(start,end,filename):
    input_file = open('ULJS00293.BIN', 'rb')

    input_file.seek(start)
    data = input_file.read(end - start)
    output_file = open(filename, 'wb')
    output_file.write(data)
    output_file.close()

    input_file.close()


"""
Graphical Interface Start
"""

from topx import *

window = Tk()
#window.iconbitmap("favicon.ico")
window.title("PyNDX - Tales of Phantasia: Narikiri Dungeon X Utility")

label = Label(window, text = "PyNDX Utility Extracts Files from PSP game Narikiri Dungeon X")
label.grid(row=0, column=0, columnspan=4)

frame1 = LabelFrame(window, text="Unpack", padx=5, pady=5)
frame1.grid(row=1, column=0, padx=10, pady=10)

btn_unpackALL = Button(frame1, text="Unpack all.dat", command = extract_all_dat)
btn_unpackALL.grid(row=0, column=0)

frame2 = LabelFrame(window, text="Repack", padx=5, pady=5)
frame2.grid(row=1, column=1, padx=10, pady=10)

btn_repackALL = Button(frame2, text="Repack all.dat", command = pack_all)
btn_repackALL.grid(row=0, column=0)


window.mainloop()
