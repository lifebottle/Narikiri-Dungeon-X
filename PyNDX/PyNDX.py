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
Menu Bar Start
"""
def work_dir():
    pwd = filedialog.askdirectory()
    os.chdir(pwd)
    cwd.config(text="Current Working Directory: " + pwd)

def about():
   about_win = Toplevel(window)

   about_win.title("About PyNDX")
   
   frame0 = LabelFrame(about_win, text="PyNDX GUI", padx=5, pady=5)
   frame0.pack(padx=10, pady=10)
   
   about_label = Label(frame0, text = "PyNDX is an open-source tool that can unpack and repack resources from Tales of Phantasia: Narikiri Dungeon X (PSP).")
   about_label.pack()

   link1 = Label(frame0, text="GitHub Project", fg="blue", cursor="hand2")
   link1.pack(anchor=W)
   link1.bind("<Button-1>", lambda e: callback("https://github.com/pnvnd/Narikiri-Dungeon-X"))

   link2 = Label(frame0, text="Discord Server", fg="blue", cursor="hand2")
   link2.pack(anchor=W)
   link2.bind("<Button-1>", lambda e: callback("https://discord.gg/HZ2NFjpedn"))

   close_button = Button(about_win, text="Close", command = about_win.destroy)
   close_button.pack(padx=10, pady=10)


"""
Graphical Interface Start
"""

from topx import *

window = Tk()
#window.iconbitmap("favicon.ico")
window.title("PyNDX - Tales of Phantasia: Narikiri Dungeon X Utility")

menubar = Menu(window)

filemenu = Menu(menubar, tearoff=0)

menubar.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Change Work Directory", command= work_dir)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=window.destroy)

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="About", command=about)
menubar.add_cascade(label="Help", menu=helpmenu)

window.config(menu=menubar)

label = Label(window, text = "PyNDX Utility Extracts Files from PSP game Narikiri Dungeon X")
label.grid(row=0, column=0, columnspan=4)

frame1 = LabelFrame(window, text="Unpack", padx=5, pady=5)
frame1.grid(row=1, column=0, padx=10, pady=10)

btn_unpackALL = Button(frame1, text="Unpack all.dat", command = extract_all_dat)
btn_unpackALL.grid(row=0, column=0, sticky='news')

frame2 = LabelFrame(window, text="Repack", padx=5, pady=5)
frame2.grid(row=1, column=1, padx=10, pady=10)

btn_repackALL = Button(frame2, text="Repack all.dat", command = pack_all)
btn_repackALL.grid(row=0, column=0, sticky='news')


"""
Status Bar Start
"""
cwd = Label(window, text = "Current Working Directory: " + os.getcwd(), bd=1, relief=SUNKEN, anchor=W)
cwd.grid(row=5, column=0, columnspan=4, sticky='news')

window.mainloop()
