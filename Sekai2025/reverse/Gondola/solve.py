# solve_gondola.py
# Python 3.10+
# Работает локально: собирает память из chal.lua, вытаскивает таргеты и константы,
# проверяет SHA-256 найденного кандидата. Трансформация оставлена «точкой расширения».

import re, struct, codecs, hashlib, sys
from typing import Tuple

GOAL_SHA = "204d015073f84763c0ff865d0fc4e046f882e2ade6afcf7bcb56904a6b96eb38".lower()
LUA_PATH = "chal.lua"

# -------- utils: 64-bit арифметика --------
MASK64 = (1<<64) - 1
def u64(x:int)->int: return x & MASK64
def rotl(x:int, r:int)->int:
    r &= 63
    return ((x<<r) & MASK64) | (x>>(64-r))
def rotr(x:int, r:int)->int:
    r &= 63
    return (x>>r) | ((x<<(64-r)) & MASK64)

# -------- сборка памяти из chal.lua --------
def build_memory_from_lua(path=LUA_PATH, size=200000) -> bytes:
    text = open(path, "r", encoding="utf-8", errors="replace").read()
    mem = bytearray(size)
    # собираем ВСЕ rt.store.string(MEMORY_LIST[0], <addr>, "<bytes>")
    for m in re.finditer(r'rt\.store\.string\(MEMORY_LIST\[0\],\s*(\d+),\s*"(.+?)"\)', text, re.S):
        addr = int(m.group(1))
        esc  = m.group(2)
        # превращаем \xHH / \n / \" и т.д. в реальные байты
        bs = codecs.decode(esc, 'unicode_escape').encode('latin1', 'ignore')
        mem[addr:addr+len(bs)] = bs
    return bytes(mem)

# -------- вытаскиваем константы и таргеты --------
def load_consts_and_targets(mem: bytes):
    # константы раундов: 8×u64 @4352..4415 (LE)
    C = struct.unpack("<QQQQQQQQ", mem[4352:4416])
    # таргеты проверки: 8×u64 @4416..4479 (LE)
    T = struct.unpack("<QQQQQQQQ", mem[4416:4480])
    # дополнительные «соли» из функции (используются в ветках): @4384, @4400, @4408 и т.п.
    seed_4384 = struct.unpack("<Q", mem[4384:4392])[0]
    seed_4400 = struct.unpack("<Q", mem[4400:4408])[0]
    seed_4408 = struct.unpack("<Q", mem[4408:4416])[0]
    return C, T, (seed_4384, seed_4400, seed_4408)

# -------- точная трансформация для окна 8 байт --------
def transform_window(x_le_u64: int, idx: int, C: Tuple[int,...], seeds: Tuple[int,int,int]) -> int:
    """
    x_le_u64 — это 8 байт окна (little-endian) из слайдинга по входу,
    idx — номер окна (0..7), C — 8 раундовых констант @4352..4415,
    seeds — (seed_4384, seed_4400, seed_4408) @4384, @4400, @4408.
    ВНИМАНИЕ: из-за того, что присланный chal.lua урезан троеточиями,
    здесь стоит заглушка (пример «похожей» нетривиальной мешалки).
    ЗАМЕНИ на точный код из FUNC_LIST[78], как только будет полный файл.
    """
    s4384, s4400, s4408 = seeds
    k = C[idx % 8]
    r = (13 + 7*idx) & 63

    v = u64(x_le_u64 ^ k)
    v = u64(rotl(v, r) * u64(0x9E3779B97F4A7C15 + 0x5851F42D4C957F2D*idx))
    v ^= rotr(v, 17) ^ rotl(v, 41)

    # в оригинале ещё участвуют значения @4384 (байт-свап), @4400, @4408 с множителями -511
    v ^= rotl(u64(s4384), (idx*11+5) & 63)
    v = u64(v * (0xC2B2AE3D27D4EB4F ^ (k>>3)))
    v ^= rotr(v, 7) ^ rotl(v, 57)
    v = u64(v + u64(s4400 * -511))
    v = u64(v ^ u64(s4408 * -511))
    return v

# -------- склейка 8 окон (шагаем на +4 байта) и проверка с таргетами --------
def check_candidate(inner_bytes: bytes, C, T, seeds) -> bool:
    # Внутренний ввод — это та самая «строка без SEKAI{ }», которую ждёт бинарь.
    # В функции читаются 8 перекрывающихся окон по 8 байт с шагом +4 (см. loc_15 += 4).
    # Сопоставляем каждое окно с соответствующим T[idx].
    assert len(inner_bytes) >= 8 + 7*4, "мало байт для 8 окон"
    ok = True
    for i in range(8):
        off = 16 + i*4   # в lua было loc_15 = loc_0 + 16; далее +4 каждый шаг
        block = inner_bytes[off:off+8]
        if len(block) < 8:
            return False
        x = int.from_bytes(block, "little")
        y = transform_window(x, i, C, seeds)
        if y != T[i]:
            ok = False
            break
    return ok

# -------- основной раннер --------
def main():
    mem = build_memory_from_lua(LUA_PATH)
    C, T, seeds = load_consts_and_targets(mem)

    print("[*] Round consts (C1..C8):")
    for i,c in enumerate(C,1):
        print(f"  C{i} = 0x{c:016x}")
    print("[*] Targets (T0..T7) @4416:")
    for i,t in enumerate(T):
        print(f"  T{i} = 0x{t:016x}")

    # Тут нужно либо:
    #  1) точно реализовать transform_window, либо
    #  2) выписать вход из chal.lua, выполнив lua с принтами,
    #  3) или решить систему в z3 (когда есть точная формула).
    #
    # Я оставлю каркас для проверки SHA — как только получишь 'inner' (строку внутри SEKAI{...}),
    # вставь её сюда и проверь.

    # Пример: inner = b"..."  # 32..40 байт, в зависимости от реального ввода
    # if check_candidate(inner, C, T, seeds):
    #     flag = f"SEKAI{{{inner.decode('ascii')}}}"
    #     s = hashlib.sha256(flag.encode()).hexdigest()
    #     print("[+] FLAG:", flag)
    #     print("[+] SHA256:", s, "(OK)" if s==GOAL_SHA else "(mismatch)")

    print("\n[!] Трансформация сейчас заглушка. Нужен полный chal.lua без «…», чтобы я перенёс точные ветки ::continue_at_9..5 и т.п.")
    print("    Как только будет полный текст, я вставлю их в transform_window и верну финальный флаг с проверкой SHA.")

if __name__ == "__main__":
    main()
