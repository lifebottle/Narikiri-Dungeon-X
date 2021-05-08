#Extracts filenames to text
offset_start = 0x187AD0
offset_end = 0x18C41F

def extract_filenames():
    input_file = open('ULJS00293.BIN', 'rb')
    output_file = open('filenames.txt', 'w')

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
