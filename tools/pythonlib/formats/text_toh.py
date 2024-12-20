import re
import struct
import pyjson5 as json
import string
from .FileIO import FileIO
from itertools import chain

VALID_VOICEID = [r'(VSM_\w+)', r'(VCT_\w+)', r'(S\d+)', r'(C\d+)']
COMMON_TAG = r"(<[\w/]+:?\w+>)"
HEX_TAG = r"(\{[0-9A-F]{2}\})"
PRINTABLE_CHARS = "".join(
            (string.digits, string.ascii_letters, string.punctuation, " ")
        )
jsonTblTags = dict()
with open('../Tales-of-Hearts-DS/Project/tbl_all.json') as f:
    jsonraw = json.loads(f.read(), encoding="utf-8")
    for k, v in jsonraw.items():
        jsonTblTags[k] = {int(k2, 16): v2 for k2, v2 in v.items()}

ijsonTblTags = dict()
for k, v in jsonTblTags.items():
    if k in ['TAGS', 'TBL']:
        ijsonTblTags[k] = {v2: k2 for k2, v2 in v.items()}
    else:
        ijsonTblTags[k] = {v2: hex(k2).replace('0x', '').upper() for k2, v2 in v.items()}
iTags = {v2.upper(): k2 for k2, v2 in jsonTblTags['TAGS'].items()}

letter_values = {}
letter_path = '../Tales-of-Hearts-DS/Project/letter_values.txt'
try:
    with open(letter_path, 'r',encoding='utf-8') as file:
        for line in file:
            letter, value = line.strip().split()
            letter_values[letter] = int(value)
except FileNotFoundError:
    print(f"Error: File '{letter_path}' not found.")
except ValueError:
    print(f"Error: Invalid format in file '{letter_path}'.")

def bytes_to_text(src: FileIO, offset: int = -1) -> (str, bytes):
    finalText = ""
    chars = jsonTblTags['TBL']

    if (offset > 0):
        src.seek(offset, 0)
    buffer = []
    while True:
        b = src.read(1)

        if b == b"\x00": break


        b = ord(b)
        buffer.append(b)

        # Button
        if b == 0x81:
            next_b = src.read(1)
            if ord(next_b) in jsonTblTags['BUTTON'].keys():
                finalText += f"<{jsonTblTags['BUTTON'].get(ord(next_b))}>"
                buffer.append(ord(next_b))
                continue
            else:
                src.seek(src.tell( ) -1 ,0)



        # Custom Encoded Text
        if (0x80 <= b <= 0x9F) or (0xE0 <= b <= 0xEA):
            v  = src.read_uint8()
            c = (b << 8) | v
            buffer.append(v)
            finalText += chars.get(c, "{%02X}{%02X}" % (c >> 8, c & 0xFF))
            continue

        if b == 0xA:
            finalText += ("\n")
            continue

        # Voice Id
        elif b in [0x9]:

            val = ""
            while src.read(1) != b"\x29":
                src.seek(src.tell() - 1)
                val += src.read(1).decode("cp932")

            buffer.extend(list(val.encode("cp932")))
            buffer.append(0x29)

            val += ">"
            val = val.replace('(', '<')

            finalText += val
            continue

        # ASCII text
        if chr(b) in PRINTABLE_CHARS:
            finalText += chr(b)
            continue

        # cp932 text
        if 0xA0 < b < 0xE0:
            finalText += struct.pack("B", b).decode("cp932")
            continue



        if b in [0x3, 0x4, 0xB]:
            b_value = b''

            if ord(src.read(1) )== 0x28:
                tag_name = jsonTblTags['TAGS'].get(b)
                buffer.append(0x28)

                b_v = b''
                while b_v != b'\x29':
                    b_v = src.read(1)
                    b_value += b_v
                b_value = b_value[:-1]
                buffer.extend(list(b_value))
                buffer.append(0x29)

                parameter = int.from_bytes(b_value, "big")
                tag_param = jsonTblTags.get(tag_name.upper(), {}).get(parameter, None)

                if tag_param is not None:
                    finalText += f"<{tag_param}>"
                else:
                    finalText += f"<{tag_name}:{parameter}>"

                continue

        if b == 0xC:

            finalText += "<Bubble>"
            continue

        finalText += "{%02X}" % b

    return finalText, bytes(buffer)


def text_to_bytes(text:str):
    multi_regex = (HEX_TAG + "|" + COMMON_TAG + r"|(\n)")
    tokens = [sh for sh in re.split(multi_regex, text) if sh]
    output = b''
    for t in tokens:
        # Hex literals
        if re.match(HEX_TAG, t):
            output += struct.pack("B", int(t[1:3], 16))

        # Tags

        elif re.match(COMMON_TAG, t):
            tag, param, *_ = t[1:-1].split(":") + [None]

            if tag == "icon":
                output += struct.pack("B", ijsonTblTags["TAGS"].get(tag))
                output += b'\x28' + struct.pack('B', int(param)) + b'\x29'

            elif any(re.match(possible_value, tag)  for possible_value in VALID_VOICEID):
                output += b'\x09\x28' + tag.encode("cp932") + b'\x29'

            elif tag == "Bubble":
                output += b'\x0C'

            else:
                if tag in ijsonTblTags["TAGS"]:
                    output += struct.pack("B", ijsonTblTags["TAGS"][tag])
                    continue

                for k, v in ijsonTblTags.items():
                    if tag in v:
                        if k in ['NAME', 'COLOR']:
                            output += struct.pack('B',iTags[k]) + b'\x28' + bytes.fromhex(v[tag]) + b'\x29'
                            break
                        else:
                            output += b'\x81' + bytes.fromhex(v[tag])

        # Actual text
        elif t == "\n":
            output += b"\x0A"
        else:
            for c in t:
                if c in PRINTABLE_CHARS or c == "\u3000":
                    output += c.encode("cp932")
                else:

                    if c in ijsonTblTags["TBL"].keys():
                        b = ijsonTblTags["TBL"][c].to_bytes(2, 'big')
                        output += b
                    else:
                        output += c.encode("cp932")


    return output

def calculate_word_sum(word, letter_space):
    word_sum = 0

    for letter in word:
        # Check if the letter is in the dictionary
        if letter in letter_values:
            # Add the value of the letter to the sum
            word_sum += letter_values[letter]
            # add the 1 pixel of space between word
            word_sum += letter_space  # story has +2 letter spacing
        else:
            # Handle the case where the letter is not in the dictionary
            print(f"Warning: Letter '{letter}' not found in the dictionary.")

    return word_sum


def wordwrap_column(text, wrap_length, space_length):

    # Wordwrap the text in the specified column of each row
    # Remove trailing white space
    text = text.rstrip()
    # Remove double white spaces
    text = " ".join(text.split())
    # Remove existing line breaks
    text = text.replace("\n", " ")
    wrapped_text = ""
    line = ""
    line_length = 0
    nb_lines = 0
    letter_space = 1

    multi_regex = (HEX_TAG + "|" + COMMON_TAG + r"|(\n)")
    tokens = [sh.split(" ") for sh in re.split(multi_regex, text) if sh is not None and sh != ""]
    tokens = [ele for ele in list(chain.from_iterable(tokens)) if ele != '']

    for word in tokens:

        if word in letter_values.keys():
            line_length += letter_values[word]
        else:
            line_length += calculate_word_sum(word, letter_space) - letter_space  # -2 remove the last letter spacing

        if line_length > wrap_length:
            # If so, add the current line to the wrapped text and start a new line
            wrapped_text += line.rstrip(" ") + "\n"  # removing trailing white space
            line = word + ' '
            line_length = calculate_word_sum(word, letter_space) + space_length  # for white spaces
            nb_lines += 1
        else:
            # Add the word to the current line
            line += word + " "
            # line_length += calculate_word_sum(word, letter_values)+17 #for white spaces
            line_length += space_length  # for white spaces

    # Add the remaining line to the wrapped text
    wrapped_text += line

    if nb_lines > 3:
        print("Cell has more than 3 lines after wordwrapping" + '\n')
        print(wrapped_text + "\n====================\n")

    return wrapped_text