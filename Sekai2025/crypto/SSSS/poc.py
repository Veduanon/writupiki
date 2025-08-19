#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket, ssl, time, re, sys

HOST = "ssss.chals.sekai.team"
PORT = 1337
ATTEMPTS = 2    # два независимых запуска челенджа
T = 20          # минимально допустимое t

# длинное десятичное или хексовое число (чтобы не спутать с "20", "1337" и т.п.)
re_dec_long = re.compile(rb'\b[0-9]{25,}\b')
re_hex_long = re.compile(rb'0x[0-9a-fA-F]{40,}\b')
# частые признаки запрета повторов
re_dupe_hint = re.compile(rb'(distinct|unique|different|no duplicates)', re.I)

def tls_connect(host, port, timeout=10):
    raw = socket.create_connection((host, port), timeout=timeout)
    raw.settimeout(1.0)
    ctx = ssl.create_default_context()
    # если самоподписанный сертификат — при необходимости ослабьте валидацию:
    # ctx.check_hostname = False
    # ctx.verify_mode = ssl.CERT_NONE
    return ctx.wrap_socket(raw, server_hostname=host)

def send_lines(sock, lines):
    data = b"".join([(s if isinstance(s, bytes) else str(s).encode()) + b"\n" for s in lines])
    sock.sendall(data)

def recv_transcript(sock, total_wait=15.0, idle_gap=1.2, max_bytes=2_000_000):
    buf = bytearray()
    start = time.time()
    last = start
    while True:
        if time.time() - start > total_wait:
            break
        try:
            chunk = sock.recv(4096)
            if not chunk:
                time.sleep(0.1)
                if time.time() - last > idle_gap:
                    break
                continue
            buf += chunk
            last = time.time()
            if len(buf) >= max_bytes:
                break
        except (ssl.SSLWantReadError, socket.timeout):
            if time.time() - last > idle_gap:
                break
        except Exception:
            break
    return bytes(buf)

def extract_long_numbers(blob):
    return re_dec_long.findall(blob) + re_hex_long.findall(blob)

def pick_secret_guess(blob):
    nums = extract_long_numbers(blob)
    return nums[-1] if nums else None

def one_session(xs):
    s = tls_connect(HOST, PORT)
    try:
        pre = recv_transcript(s, total_wait=1.5, idle_gap=0.5)

        # шлём t и все x (все x > 0, иначе упадём на assert 0 < x < p)
        send_lines(s, [T] + xs)

        tr = recv_transcript(s, total_wait=15.0, idle_gap=1.0)
        transcript = pre + tr

        # пытаемся угадать secret по «длинному» числу из вывода
        guess = pick_secret_guess(transcript)
        if not guess:
            # если сервер ничего «длинного» не печатает — пошлём 0 как заглушку
            # (это просто чтобы завершить протокол и увидеть реакцию)
            guess = b"0"

        s.sendall(guess + b"\n")
        fin = recv_transcript(s, total_wait=6.0, idle_gap=1.0)
        transcript += b"\n=== SENT SECRET ===\n" + guess + b"\n" + fin

        text_low = transcript.lower()
        ok = (b"ctf" in text_low) or (b"flag" in text_low) or (b"congrats" in text_low) or (b"success" in text_low)
        return (ok, transcript)
    finally:
        try: s.close()
        except: pass

def attempt():
    # Вариант A: все x = 1 (валидно: 0 < 1 < p)
    xsA = [1]*T
    ok, logA = one_session(xsA)
    sys.stdout.write("\n----- SESSION A TRANSCRIPT (trimmed) -----\n")
    sys.stdout.write(logA.decode('utf-8', 'ignore')[-5000:])
    sys.stdout.write("\n------------------------------------------\n")
    sys.stdout.flush()
    if ok:
        return True

    # Если сервер ругается на повторы — пробуем уникальные x: 1..T
    if re_dupe_hint.search(logA):
        xsB = list(range(1, T+1))  # все уникальны и > 0
        ok2, logB = one_session(xsB)
        sys.stdout.write("\n----- SESSION B TRANSCRIPT (trimmed) -----\n")
        sys.stdout.write(logB.decode('utf-8', 'ignore')[-5000:])
        sys.stdout.write("\n------------------------------------------\n")
        sys.stdout.flush()
        return ok2

    return False

def main():
    for i in range(1, ATTEMPTS+1):
        print(f"\n===== Попытка {i} / {ATTEMPTS} =====")
        if attempt():
            print("[+] Похоже, флаг получен. Останавливаюсь.")
            return
        print("[-] Неуспешно. Переходим к следующей попытке…")
        time.sleep(1.0)
    print("\n[×] Обе попытки не сработали. Смотри транскрипты выше — там точный формат вывода сервера.")

if __name__ == "__main__":
    main()
