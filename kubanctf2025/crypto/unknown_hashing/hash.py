import struct
import sys

def left_rotate(x, c):
    return ((x << c) | (x >> (32 - c))) & 0xFFFFFFFF

def mystery_hash(message):
    A = 0x67452301
    B = 0xefcdab89
    C = 0x98badcfe
    D = 0x10325476

    s = [7,12,17,22]*4 + [5,9,14,20]*4 + [4,11,16,23]*4 + [6,10,15,21]*4
    K = [int(abs(2**32 * __import__('math').sin(i + 1))) & 0xFFFFFFFF for i in range(64)]

    msg_bytes = bytearray(message, 'utf-8')
    orig_len_in_bits = (8 * len(msg_bytes)) & 0xFFFFFFFFFFFFFFFF
    msg_bytes.append(0x80)
    while (len(msg_bytes) % 64) != 56:
        msg_bytes.append(0)
    msg_bytes += struct.pack('<Q', orig_len_in_bits)

    for chunk_offset in range(0, len(msg_bytes), 64):
        chunk = msg_bytes[chunk_offset:chunk_offset + 64]
        M = list(struct.unpack('<16I', chunk))
        a, b, c, d = A, B, C, D

        for i in range(64):
            if 0 <= i <= 15:
                f = (b & c) | (~b & d)
                g = i
            elif 16 <= i <= 31:
                f = (d & b) | (~d & c)
                g = (5*i + 1) % 16
            elif 32 <= i <= 47:
                f = b ^ c ^ d
                g = (3*i + 5) % 16
            else:
                f = c ^ (b | ~d)
                g = (7*i) % 16
            temp = (a + f + K[i] + M[g]) & 0xFFFFFFFF
            a, d, c, b = d, c, b, (b + left_rotate(temp, s[i])) & 0xFFFFFFFF

        A = (A + a) & 0xFFFFFFFF
        B = (B + b) & 0xFFFFFFFF
        C = (C + c) & 0xFFFFFFFF
        D = (D + d) & 0xFFFFFFFF

    hash_bytes = struct.pack('<4I', A, B, C, D)
    mask = [3, 1, 7, 5, 9, 11, 13, 15, 14, 12, 10, 8, 6, 4, 2, 0]
    mixed = bytes([hash_bytes[m] for m in mask])
    mask2 = [0xAA, 0x55, 0x1A, 0xC3, 0x9F, 0x5E, 0x33, 0x77, 0x77, 0x33, 0x5E, 0x9F, 0xC3, 0x1A, 0x55, 0xAA]
    result = bytes([mixed[i] ^ mask2[i] for i in range(16)])
    return ''.join(['{:02x}'.format(x) for x in result])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <string>")
        sys.exit(1)
    input_string = sys.argv[1]
    print(mystery_hash(input_string))
