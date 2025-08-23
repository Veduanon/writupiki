from pathlib import Path
from Crypto.Cipher import AES
import re

# 64-байтный блок, который ты дал:
blob = bytes.fromhex(
    "e25200f6b7ddc6fc60aa0cea560ee002"
    "f77c5c566d706dcded3f2108b6208de2"
    "0537f965b812d76a97b0c40869411d23"
    "4b262816344012fb15c87df2f830c1b6"
)
c = [blob[i:i+16] for i in range(0,64,16)]  # c0..c3

ct = Path("decoded_from_text.bin").read_bytes()

def save_if_hit(name, pt):
    if b"MZ" in pt or b"CSC{" in pt:
        Path(f"{name}.bin").write_bytes(pt)
        off = pt.find(b"MZ")
        if off != -1:
            Path(f"{name}.exe").write_bytes(pt[off:])
    return (pt.find(b"MZ"), re.search(rb"CSC\{[^}]+\}", pt) is not None)

# AES-256-CTR: key = c0||c1, nonce/counter из c2 ИЛИ c3 (8+8)
for iv in [c[2], c[3]]:
    nonce, init = iv[:8], int.from_bytes(iv[8:], "big")
    pt = AES.new(c[0]+c[1], AES.MODE_CTR, nonce=nonce, initial_value=init).decrypt(ct)
    print("256-CTR c2:", save_if_hit("256ctr_c2", pt))
# попробуем и наоборот (ключ = c2||c3, nonce/counter из c0 или c1)
for iv in [c[0], c[1]]:
    nonce, init = iv[:8], int.from_bytes(iv[8:], "big")
    pt = AES.new(c[2]+c[3], AES.MODE_CTR, nonce=nonce, initial_value=init).decrypt(ct)
    print("256-CTR c0/1:", save_if_hit("256ctr_c01", pt))

# AES-128-CTR: ключ = один из c0..c3, nonce/counter = другой (8+8)
for ki in range(4):
    for vi in range(4):
        if vi == ki: continue
        nonce, init = c[vi][:8], int.from_bytes(c[vi][8:], "big")
        pt = AES.new(c[ki], AES.MODE_CTR, nonce=nonce, initial_value=init).decrypt(ct)
        save_if_hit(f"128ctr_k{ki}_v{vi}", pt)

# AES-128-OFB: ключ = c0..c3, iv = другой 16-байтный
for ki in range(4):
    for vi in range(4):
        if vi == ki: continue
        pt = AES.new(c[ki], AES.MODE_OFB, iv=c[vi]).decrypt(ct)
        save_if_hit(f"128ofb_k{ki}_v{vi}", pt)
