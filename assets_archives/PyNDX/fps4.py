import os, struct, sys

def dump_fps4(name, name2):

    f = open(name, 'rb')
    
    fps4 = f.read(4)
    if fps4 != b'FPS4':
        #print("Wrong file.")
        return
        
    file_number = struct.unpack('<L', f.read(4))[0]
    header_size = struct.unpack('<L', f.read(4))[0]
    offset = struct.unpack('<L', f.read(4))[0]
    block_size = struct.unpack('<H', f.read(2))[0]
    
    if block_size == 0x2C:
        f.seek(header_size, 0)
        files_offsets = []
        files_sizes = []
        files_names = []
        
        for i in range(file_number-1):
            files_offsets.append(struct.unpack('<L', f.read(4))[0])
            files_sizes.append(struct.unpack('<L', f.read(4))[0])
            f.read(4) # File size
            fname = f.read(block_size-0xC).decode("ASCII").strip('\x00')
            files_names.append(fname)
            
        try:
            os.mkdir(name.split('.')[0].upper())
        except:
            pass

        if offset != 0x00:
            for i in range(file_number-1):
                o = open(os.path.join(name.split('.')[0], files_names[i]), 'wb')
                f.seek(files_offsets[i], 0)
                o.write(f.read(files_sizes[i]))
                o.close()
        else:
            f2 = open(name2, 'rb')
            for i in range(file_number-1):
                o = open(os.path.join(name.split('.')[0], files_names[i]), 'wb')
                f2.seek(files_offsets[i], 0)
                o.write(f2.read(files_sizes[i]))
                o.close()
            f2.close()
                
        f.close()

def dump_folder(folder):
    
    os.chdir(folder)

    # Only for m.b & m.dat
    for f in os.listdir(os.getcwd()):
        if '.B' in f:
            dump_fps4(f, f.split('.')[0]+'.MAPBIN')
        print ("Extracting %s" % f)

def pack_folder(folder, dat='.DAT'):
    
    buffer = 0
    files_sizes = []
    files_names = []
    b_file = open(folder + '.B', 'wb')
    dat_file = open(folder + dat, 'wb')
    files = os.listdir(folder)
    
    for n in files:
        f = open(os.path.join(folder, n), 'rb')
        files_names.append(n)
        data = f.read()
        dat_file.write(data)
        files_sizes.append(len(data))
        f.close()

    dat_file.close()

    b_file.write(b'\x46\x50\x53\x34') # FPS4
    b_file.write(struct.pack('<L', len(files) + 1))
    b_file.write(struct.pack('<L', 0x1C))
    b_file.write(b'\x00' * 4 + b'\x2C\x00\x0F\x00\x01\x01\x00\x00' +  b'\x00' * 4)

    for i in range(len(files)):
        b_file.write(struct.pack('<L', buffer))
        b_file.write(struct.pack('<L', files_sizes[i]))
        b_file.write(struct.pack('<L', files_sizes[i]))
        b_file.write(files_names[i].encode())
        b_file.write(b'\x00' * (32 - (len(files_names[i]) % 32)))
        buffer += files_sizes[i]

    b_file.write(struct.pack('<L', buffer) + b'\x00'*12)
    b_file.close()

def pack_all(folder):
    
    os.chdir(folder)
    
    for d in os.listdir(os.getcwd()):
        if os.path.isdir(d):
            pack_folder(d)
            print ("Packing %s" % d)

def pack_m(folder):
    
    os.chdir(folder)
    
    for d in os.listdir(os.getcwd()):
        if os.path.isdir(d):
            pack_folder(d, '.MAPBIN')
            print ("Packing %s" % d)



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Error")
        sys.exit(1)
    if sys.argv[1] == '-d':
        if len(sys.argv) == 3:
            dump_fps4(sys.argv[2], None)
        elif len(sys.argv) == 4:
            dump_fps4(sys.argv[2], sys.argv[3])
        else:
            print ("Error.")
    elif sys.argv[1] == '-dm':
        dump_folder(sys.argv[2])
    elif sys.argv[1] == '-i':
        pack_folder(sys.argv[2])
    elif sys.argv[1] == '-ia':
        pack_all(sys.argv[2])
    elif sys.argv[1] == '-im':
        pack_m(sys.argv[2])
        print ("Done!")

        
    sys.exit(1)
