#!/usr/bin/env python3

import sys

KEY_MAP = {
    0x04: 'a', 0x05: 'b', 0x06: 'c', 0x07: 'd', 0x08: 'e', 0x09: 'f',
    0x0A: 'g', 0x0B: 'h', 0x0C: 'i', 0x0D: 'j', 0x0E: 'k', 0x0F: 'l',
    0x10: 'm', 0x11: 'n', 0x12: 'o', 0x13: 'p', 0x14: 'q', 0x15: 'r',
    0x16: 's', 0x17: 't', 0x18: 'u', 0x19: 'v', 0x1A: 'w', 0x1B: 'x',
    0x1C: 'y', 0x1D: 'z',
    0x1E: '1', 0x1F: '2', 0x20: '3', 0x21: '4', 0x22: '5',
    0x23: '6', 0x24: '7', 0x25: '8', 0x26: '9', 0x27: '0',
    0x28: '\n', 0x2C: ' ', 0x2D: '-', 0x2E: '=', 0x2F: '[',
    0x30: ']', 0x31: '\\', 0x33: ';', 0x34: "'", 0x35: '`',
    0x36: ',', 0x37: '.', 0x38: '/', 0x39: '[CAPSLOCK]',
    0x3A: '[F1]', 0x3B: '[F2]', 0x3C: '[F3]', 0x3D: '[F4]',
    0x3E: '[F5]', 0x3F: '[F6]', 0x40: '[F7]', 0x41: '[F8]',
    0x42: '[F9]', 0x43: '[F10]', 0x44: '[F11]', 0x45: '[F12]',
    0x46: '[PRINTSCREEN]', 0x47: '[SCROLLLOCK]', 0x48: '[PAUSE]',
    0x49: '[INSERT]', 0x4A: '[HOME]', 0x4B: '[PAGEUP]',
    0x4C: '[DELETE]', 0x4D: '[END]', 0x4E: '[PAGEDOWN]',
    0x4F: '[RIGHT]', 0x50: '[LEFT]', 0x51: '[DOWN]', 0x52: '[UP]'
}

SHIFT_MAP = {
    'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F',
    'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L',
    'm': 'M', 'n': 'N', 'o': 'O', 'p': 'P', 'q': 'Q', 'r': 'R',
    's': 'S', 't': 'T', 'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X',
    'y': 'Y', 'z': 'Z', '1': '!', '2': '@', '3': '#', '4': '$',
    '5': '%', '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', '`': '~', ',': '<', '.': '>', '/': '?'
}

MOD_LSHIFT = 0x02
MOD_RSHIFT = 0x20

def decode_hid_report(report: bytes) -> str:
    if len(report) != 8:
        return ""
    
    modifier = report[0]
    pressed_keys = report[2:]
    shift_active = bool(modifier & (MOD_LSHIFT | MOD_RSHIFT))
    
    output = []
    for code in pressed_keys:
        if code == 0:
            continue
        if code in KEY_MAP:
            char = KEY_MAP[code]
            output.append(SHIFT_MAP.get(char, char) if shift_active else char)
        else:
            output.append(f"[UNK:{code:02X}]")
    
    return "".join(output)

def main():
    if len(sys.argv) != 2:
        print("Usage: python hid2ascii.py hid.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        with open(file_path, 'r') as file:
            decoded_string = []
            for line in file:
                line = line.strip()
                if len(line) != 16:
                    continue
                try:
                    report = bytes.fromhex(line)
                    decoded_string.append(decode_hid_report(report))
                except ValueError:
                    continue
            print("".join(decoded_string), end="")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
