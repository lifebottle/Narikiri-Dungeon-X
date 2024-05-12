import json, os, struct, sys

struct_bytecode = b'\x18\x00\x0C\x04'
string_bytecode = b'\x00\x00\x82\x02'

def mkdir(d):
    try: os.mkdir(d)
    except: pass
    
def extract_tss(file, infolder, outfolder):
    f = open(f'{infolder}/{file}', 'rb')
    o = open(f'{outfolder}/{file}.txt', 'w', encoding='cp932')
    f.read(12)
    text_block = struct.unpack('<I', f.read(4))[0]
    f.read(4)
    pointer_block_size = struct.unpack('<I', f.read(4))[0]
    text_block_size = struct.unpack('<I', f.read(4))[0]
    read = 0
    struct_pointers = []
    string_pointers = []
    
    while read < pointer_block_size:
        b = f.read(4)
        if b == struct_bytecode:
            struct_pointers.append(struct.unpack('<I', f.read(4))[0])
            read += 4
        elif b == string_bytecode:
            string_pointers.append(struct.unpack('<I', f.read(4))[0])
            read += 4
        read += 4

    # remove duplicates
    struct_pointers = list(dict.fromkeys(struct_pointers))
    
    # string
    for i in string_pointers:
        f.seek(text_block + i, 0)
        s = b''
        b = f.read(1)
        while b != b'\x00':
            if b == b'\x01':
                b = f.read(1)
                s += b'{01}{%02X}' % ord(b)
            elif ord(b) in range(2, 10):
                s += b'{%02X}' % ord(b)
            elif ord(b) == 0xC:
                s += b'{%02X}' % ord(b)
            else:
                s += b
            b = f.read(1)
        o.write(s.decode('cp932'))
        o.write('\n--------------\n')
    # struct
    for i in struct_pointers:
        f.seek(text_block + i, 0)
        f.read(0x8)
        pts = []
        pointer = struct.unpack('<I', f.read(4))[0]
        while pointer != 0 and pointer < text_block_size:
            pts.append(pointer)
            pointer = struct.unpack('<I', f.read(4))[0]
        for p in pts:
            f.seek(text_block + p, 0)
            dialogue = b''
            b = f.read(1)
            while b != b'\x00':
                if b == b'\x0C':
                    dialogue += b'\n<NW>\n'
                elif ord(b) in range(1, 10):
                    dialogue += b'{%02X}' % ord(b)
                else:
                    dialogue += b
                b = f.read(1)
            o.write(dialogue.decode('cp932'))
            o.write('\n--------------\n')
    f.close()
    o.close()
        
def extract_script():
    mkdir('tss_text')
    for f in os.listdir('tss'):
        print(f)
        extract_tss(f, 'tss', 'tss_text')
        
if __name__ == '__main__':
    extract_script()
