import struct, os, sys, json, subprocess
#from fps4 import *

# True to extract files with names
# False so extract files with hashes
extract_names = False

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
    data = input_file.read(size)
    if extract_names:
        try:
            output_file = open('all/' + hash_name, 'wb')
        except:
            output_file = open('all/' + filename, 'wb')
    else:
        output_file = open('all/' + filename, 'wb')
    output_file.write(data)
    output_file.close()
    input_file.close()

def extract_all_dat():
    make_dirs()
    order = {}
    order['order'] = []
    order_json = open('order.json', 'w')
    eboot = open('ULJS00293.BIN', 'rb')
    eboot.seek(0x1FF624)
    while True:
        file_info = struct.unpack('<3I', eboot.read(12))
        if(file_info[2] == 0):
            break
        hash_ = "%08X" % file_info[2]
        extract_files(file_info[0], file_info[1], hash_)
        order['order'].append(hash_)
    json.dump(order, order_json, indent = 4)
    order_json.close()

def extract_map_data():
    mkdir('all/map/cab')
    for f in os.listdir('all/map'):
        if os.path.isfile('all/map/' + f):
            subprocess.run(['expand', 'all/map/' + f, 'all/map/cab/'+ f])

def extract_map_pack():
    mkdir('all/map/pack/cab')
    for f in os.listdir('all/map/pack'):
        if os.path.isfile('all/map/pack/' + f):
            subprocess.run(['expand', 'all/map/pack/' + f, 'all/map/pack/cab/'+ f])

def extract_script():
    for f in os.listdir('all/map/pack/cab'):
        if os.path.isfile('all/map/pack/cab/' + f) and 'ep_' in f:
            mkdir('all/map/pack/cab/' + f[:-4])
            extract_pak3(f)

def extract_pak3(name):
    f = open('all/map/pack/cab/' + name, 'rb')
    files = struct.unpack('<I', f.read(4))[0]
    offsets = []
    for i in range(files):
        offsets.append(struct.unpack('<I', f.read(4))[0])
    f.seek(offsets[0], 0)
    offsets.append(os.path.getsize('all/map/pack/cab/' + name))
    for i in range(files):
        o = open('all/map/pack/cab/' + name[:-4] + '/' + '%02d' % i + '.bin', 'wb')
        o.write(f.read(offsets[i+1] - offsets[i]))
        o.close()
    f.close()

def pack_all():
    addrs = []
    sizes = []
    buffer = 0
    all_file = open('all_new.dat', 'wb')
    order_json = open('order.json', 'r')
    order_hash = json.load(order_json)
    order_json.close()
    elf = open('ULJS00293_new.bin', 'r+b')
    elf.seek(0x1FF624)
    for name in order_hash['order']:
        f = open('all/' + name, 'rb')
        data = f.read()
        sizes.append(len(data))
        remainder = 2048 - (len(data)%2048)
        if remainder == 2048:
            remainder = 0
        addrs.append(buffer)
        buffer += len(data) + remainder
        all_file.write(data)
        all_file.write(b'\x00' * remainder)
        f.close()
    for i in range(len(sizes)):
        elf.write(struct.pack('<I', addrs[i]))
        elf.write(struct.pack('<I', sizes[i]))
        elf.write(struct.pack('<I', int(order_hash['order'][i], 16)))
    elf.close()
    all_file.close()
    
            
if __name__ == '__main__':
    #extract_all_dat()
    #extract_map_data()
    #extract_map_pack()
    #extract_script()
    pack_all()
