import re
import struct
from itertools import chain

from ndx_tools.utils.fileio import FileIO

COMMON_TAG = r"(<[\w/]+:?\w+>)"
HEX_TAG = r"(\{[0-9A-F]{2}\})"
ASCII_REPL = {
    0x3C: [0x3C, 0x6C, 0x74, 0x3E], # <lt>
    0x3E: [0x3C, 0x67, 0x74, 0x3E], # <gt>
    0x7B: [0x3C, 0x6C, 0x62, 0x3E], # <lb>
    0x7D: [0x3C, 0x72, 0x62, 0x3E], # <rb>
}

EXTRAS = {
    0xFAB1: "﨑"
}

NAMES = {
    "ARC": "Arche",
    "BER": "Beryl",
    "CLE": "Cless",
    "CST": "Chester",
    "DIO": "Dio",
    "HIS": "Hisui",
    "INE": "Ines",
    "KLA": "Klarth",
    "KOH": "Kohaku",
    "KUL": "Couleur",
    "KUN": "Kunzite",
    "MEL": "Mel",
    "MIN": "Mint",
    "RND": "Rondoline",
    "RND_P": "Rody",
    "SIN": "Shing",
    "SUZ": "Suzu",
}
ICONS = {
    0x01: "CIRCLE",
    0x02: "CROSS",
    0x03: "TRIANGLE",
    0x04: "SQUARE",
    0x05: "L",
    0x06: "R",
    0x07: "SELECT",
    0x08: "START",
    0x10: "DPAD",
    0x11: "DPAD_U",
    0x12: "DPAD_D",
    0x13: "DPAD_L",
    0x14: "DPAD_R",
    0x15: "DPAD_LR",
    0x16: "DPAD_UD",
    0x20: "STICK",
    0x21: "STICK_U",
    0x22: "STICK_D",
    0x23: "STICK_R",
    0x24: "STICK_L",
    0x25: "STICK_LR",
    0x30: "ATTACK_BTN",
    0x31: "ARTES_BTN",
    0x32: "GUARD_BTN",
    0x33: "MENU_BTN",
    0x34: "TARGET_BTN",
    0x35: "OVERDRIVE_BTN",
    0x36: "PAUSE_BTN",
    0x37: "MODE_BTN",
    0x38: "MOVE",
    0x39: "MOVE2",
    0x3A: "MOVE_U",
    0x3B: "MOVE_D",
    0x3C: "MOVE_LR",
    0x3D: "SHORTCUT",
    0x3E: "SHORTCUT_U",
    0x3F: "SHORTCUT_R",
    0x40: "SHORTCUT_D",
    0x41: "SHORTCUT_L",
    0x42: "MOVE_L",
    0x43: "MOVE_R",
    0x44: "SHORTCUT_LR",
}
COLORS = {
    0x00: "Black",
    0x01: "Blue",
    0x02: "Red",
    0x03: "Purple",
    0x04: "Green",
    0x05: "Cyan",
    0x06: "Yellow",
    0x07: "White",
    0x08: "Grey",
    0x09: "DarkBlue",
    0x0A: "DarkLightBlue",
    0x0B: "DarkWhite",
    0x0C: "DarkLime",
    0x0D: "DarkGreen",
    0x0E: "DarkCyan",
    0x0F: "DarkYellow",
    0x10: "DarkGrey",
    0x7F: "AsOutline",
    0x80: "BlackOutline",
    0x81: "BlueOutline",
    0x82: "RedOutline",
    0x83: "PurpleOutline",
    0x84: "GreenOutline",
    0x85: "CyanOutline",
    0x86: "YellowOutline",
    0x87: "WhiteOutline",
    0x88: "GreyOutline",
    0x89: "DarkBlueOutline",
    0x8A: "DarkLightBlueOutline",
    0x8B: "DarkWhiteOutline",
    0x8C: "DarkLimeOutline",
    0x8D: "DarkGreenOutline",
    0x8E: "DarkCyanOutline",
    0x8F: "DarkYellowOutline",
    0x90: "DarkGreyOutline",
    0xFF: "NoOutline"
}

IEXTRAS = { v: k.to_bytes(length=2) for k, v in EXTRAS.items() }

ITAGS = { v: b"\x04(" + k.encode() + b")" for k, v in NAMES.items() }
ITAGS |= { v: b"\x0B" + k.to_bytes() for k, v in ICONS.items() }
ITAGS |= { v: b"\x01" + k.to_bytes() for k, v in COLORS.items() }
ITAGS |= {
    "lt": b"\x3C",
    "gt": b"\x3E",
    "lb": b"\x7B",
    "rb": b"\x7D",
}

def consume_param_buf(buf: bytes | bytearray, pos: int) -> tuple[str, int]:
    if buf[pos] != 0x28:  # '('
        raise ValueError("Tried to read tag param without parentheses")

    pos += 1
    start = pos

    end = buf.find(b')', start)
    if end == -1:
        raise ValueError("Unclosed tag parameter")

    val = buf[start:end].decode("ascii")

    return val, end + 1

def bytes_to_text_len(src: FileIO | bytes, offset: int = -1) -> tuple[int, str]:
    if type(src) is bytes:
        buf = src
        pos = 0
    elif type(src) is FileIO:
        buf = src.get_buffer()
        pos = src.tell()
    else:
        raise ValueError("???")

    finalText = []
    byte_run = bytearray()

    if (offset > -1):
        pos = offset

    start = pos

    def flush_run():
        if byte_run:
            finalText.append(byte_run.decode("cp932"))
            byte_run.clear()

    while pos < len(buf):
        b = buf[pos]
        pos += 1

        if b < 0x20:
            flush_run()

        match b:
            # Reached NUL terminator
            case 0x00:
                break
            # Color
            case 0x01:
                if buf[pos] == 0x28: # '(
                    val_str, pos = consume_param_buf(buf, pos)
                    val = int(val_str)
                else:
                    val = buf[pos]
                    pos += 1

                finalText.append("<" + COLORS.get(val, f"color:{val:X}") + ">")
            # Name
            case 0x04:
                # For some reason a skit uses 04 in an invalid way
                # as it seems unintended we don't dump it in that case
                if buf[pos] == 0x28: # '('
                    val, pos = consume_param_buf(buf, pos)
                    finalText.append("<" + NAMES.get(val, val) + ">")
            # Audio
            case 0x09:
                val, pos = consume_param_buf(buf, pos)
                finalText.append(f"<audio:{val}>")
            # Linebreak
            case 0x0A:
                finalText.append("\n")
            # Icons
            case 0x0B:
                if buf[pos] == 0x28: # '(
                    val_str, pos = consume_param_buf(buf, pos)
                    val = int(val_str)
                else:
                    val = buf[pos]
                    pos += 1

                finalText.append("<" + ICONS.get(val, f"icon:{val:X}") + ">")
            # Bubble
            case 0x0C:
                finalText.append("<Bubble>")
            # Furigana
            case 0x0D:
                val, pos = consume_param_buf(buf, pos)
                finalText.append(f"<furigana:{val}>")
            # Reserved chars
            case _  if b in ASCII_REPL:
                byte_run.extend(ASCII_REPL[b])
            # ASCII
            case _  if b < 0x80:
                byte_run.append(b)
            # SJIS
            case _ if 0x7F < b < 0xA0 or 0xDF < b < 0xFD:
                byte_run.append(b)
                byte_run.append(buf[pos])
                pos += 1
            # SJIS (half-width)
            case _ if 0xA0 < b < 0xDF:
                byte_run.append(b)
            # ?????
            case _:
                flush_run()
                b2 = b << 0x8 | buf[pos]
                pos += 1
                finalText.append(EXTRAS.get(b2, "{" + f"{b2:04X}" + "}"))

    flush_run()

    if (offset < 0) and type(src) is FileIO:
        src.seek(pos)

    return pos-start, "".join(finalText)


def bytes_to_text(src: FileIO | bytes, offset: int = -1) -> str:
    return bytes_to_text_len(src, offset)[1]


def text_to_bytes(text: str):
    multi_regex = (HEX_TAG + "|" + COMMON_TAG + r"|(\n)")
    tokens = [sh for sh in re.split(multi_regex, text) if sh]
    output = []

    for t in tokens:
        # Hex literals
        if re.match(HEX_TAG, t):
            output.append(struct.pack("B", int(t[1:3], 16)))

        # Tags
        elif re.match(COMMON_TAG, t):
            tag, param, *_ = t[1:-1].split(":") + [None]

            if tag == "icon":
                output.append(b'\x0B(' + struct.pack('B', int(param)) + b')')

            elif tag == "audio":
                output.append(b'\x09(' + param.encode() + b')')

            elif tag == "Bubble":
                output.append(b'\x0C')

            else:
                if tag in ITAGS:
                    output.append(ITAGS[tag])
                else:
                    raise ValueError

        # Actual text
        else:
            for c in t:
                output.append(IEXTRAS.get(c, c.encode("cp932")))

    return b''.join(output)

# def calculate_word_sum(word, letter_space):
#     word_sum = 0

#     for letter in word:
#         # Check if the letter is in the dictionary
#         if letter in letter_values:
#             # Add the value of the letter to the sum
#             word_sum += letter_values[letter]
#             # add the 1 pixel of space between word
#             word_sum += letter_space  # story has +2 letter spacing
#         else:
#             # Handle the case where the letter is not in the dictionary
#             print(f"Warning: Letter '{letter}' not found in the dictionary.")

#     return word_sum


# def wordwrap_column(text, wrap_length, space_length):

#     # Wordwrap the text in the specified column of each row
#     # Remove trailing white space
#     text = text.rstrip()
#     # Remove double white spaces
#     text = " ".join(text.split())
#     # Remove existing line breaks
#     text = text.replace("\n", " ")
#     wrapped_text = ""
#     line = ""
#     line_length = 0
#     nb_lines = 0
#     letter_space = 1

#     multi_regex = (HEX_TAG + "|" + COMMON_TAG + r"|(\n)")
#     tokens = [sh.split(" ") for sh in re.split(multi_regex, text) if sh is not None and sh != ""]
#     tokens = [ele for ele in list(chain.from_iterable(tokens)) if ele != '']

#     for word in tokens:

#         if word in letter_values.keys():
#             line_length += letter_values[word]
#         else:
#             line_length += calculate_word_sum(word, letter_space) - letter_space  # -2 remove the last letter spacing

#         if line_length > wrap_length:
#             # If so, add the current line to the wrapped text and start a new line
#             wrapped_text += line.rstrip(" ") + "\n"  # removing trailing white space
#             line = word + ' '
#             line_length = calculate_word_sum(word, letter_space) + space_length  # for white spaces
#             nb_lines += 1
#         else:
#             # Add the word to the current line
#             line += word + " "
#             # line_length += calculate_word_sum(word, letter_values)+17 #for white spaces
#             line_length += space_length  # for white spaces

#     # Add the remaining line to the wrapped text
#     wrapped_text += line

#     if nb_lines > 3:
#         print("Cell has more than 3 lines after wordwrapping" + '\n')
#         print(wrapped_text + "\n====================\n")

#     return wrapped_text
