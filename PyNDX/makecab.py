import os

"""
This program re-packs scenario files.
"""

# Move each TSS file from TSS folder into corresponding ep_xxx_xxx folder
def move_tss():
    pass

# Run pakcomposer.exe -c ep_xxx_xxx -3 and rename resulting file to script.dat
def pakcomposer3():
    pass

# Run makecab /D CompressionType=LZX /D CompressionMemory=15 /D ReservePerCabinetSize=8 script.dat ep_xxx_xxx.cab
def makecab():
    pass

# After packing CAB files, update identity by replacing hex
def cab_id():
    for file in os.listdir('all/map/pack'):
        if file.endswith(".cab"):
            cab = open(os.path.join('all/map/pack', file), 'r+b')
            cab.seek(0x20)
            cab.write(b'\x28\x11')
            cab.close()

            print(file)
            
# Re-pack scenario files one at a time to avoid conflicting script.dat name
def pack_cab():
    move_tss()
    pakcomposer3()
    makecab()
    cab_id()
