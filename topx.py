import struct, os, sys, json

json_file = open('hashes.json', 'r')
hashes = json.load(json_file)
json_file.close()

def mkdir(d):
    try: os.mkdir(d)
    except: pass

def make_dirs():
    mkdir('all')
    mkdir('all/battle')
    mkdir('all/battle/character')
    mkdir('all/battle/charsnd')
    mkdir('all/battle/data')
    mkdir('all/battle/effect')
    mkdir('all/battle/event')
    mkdir('all/battle/gui')
    mkdir('all/battle/map')
    mkdir('all/battle/resident')
    mkdir('all/battle/tutorial')
    mkdir('all/chat')
    mkdir('all/gim')
    mkdir('all/map')
    mkdir('all/map/data')
    mkdir('all/map/pack')
    mkdir('all/movie')
    mkdir('all/snd')
    mkdir('all/snd/init')
    mkdir('all/snd/se3')
    mkdir('all/snd/se3/map_mus')
    mkdir('all/snd/strpck')
    mkdir('all/sysdata')
    
def extract_files(start, size, filename):
    hash_name = filename
    if filename in hashes.keys():
        hash_name = hashes[filename]
    input_file = open('all.dat', 'rb')
    input_file.seek(start, 0)
    data1 = input_file.read(size)
    try:
        output_file = open('all/' + hash_name, 'wb')
    except:
        output_file = open('all/' + filename, 'wb')
    output_file.write(data1)
    output_file.close()

    input_file.close()

def extract_all_dat():
    make_dirs()
    eboot = open('ULJS00293.BIN', 'rb')
    eboot.seek(0x1FF624)
    while True:
        file_info = struct.unpack('<3I', eboot.read(12))
        if(file_info[2] == 0):
            break
        extract_files(file_info[0], file_info[1], "%4X" % file_info[2])
        print("%4X" % file_info[2])

if __name__ == '__main__':
    extract_all_dat()
