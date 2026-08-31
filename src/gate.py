# -*- coding: utf-8 -*-
"""Password-gate the site's content.

GitHub Pages is static -- there is no server to check a password. So instead
of hiding the UI behind a JavaScript `if`, which anyone can step past, the
payload itself is encrypted:

  * data.json (transcript, track list, timings) -> AES-256-GCM, key from
    PBKDF2-SHA256 over the password.
  * audio files are renamed to unguessable hex; their names exist ONLY inside
    the encrypted payload.

Without the password you get an opaque blob and no way to find the audio.
This is a deterrent, not a security boundary: anyone who has the password can
share the decrypted contents or the file URLs, and the URLs stay valid.
"""
import json, os, secrets, hashlib, argparse, shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITER = 200_000

def derive(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITER, 32)

def encrypt_payload(obj, password, out="docs/data.enc"):
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    key = derive(password, salt)
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
    import gzip
    packed = gzip.compress(raw, 6)
    ct = AESGCM(key).encrypt(nonce, packed, None)
    with open(out, "wb") as f:
        f.write(b"PSCH1")            # magic
        f.write(salt); f.write(nonce); f.write(ct)
    return dict(bytes=os.path.getsize(out), raw=len(raw), packed=len(packed))

def rename_audio(audiodir="docs/audio", mapfile="work/audio_names.json"):
    """Give every track an unguessable name; keep the mapping stable across
    rebuilds so old links do not rot."""
    m = json.load(open(mapfile)) if os.path.exists(mapfile) else {}
    tracks = json.load(open("work/tracks.json"))
    changed = 0
    for t in tracks:
        key = f"{t['index']:02d}"
        if key not in m:
            m[key] = secrets.token_hex(8) + ".mp3"
        src_old = f"{audiodir}/{t['file']}"
        dst = f"{audiodir}/{m[key]}"
        if os.path.exists(src_old) and src_old != dst:
            shutil.move(src_old, dst); changed += 1
        t["file"] = m[key]
    json.dump(m, open(mapfile, "w"), indent=1)
    json.dump(tracks, open("work/tracks.json", "w"), indent=1, ensure_ascii=False)
    return changed, len(tracks)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--password", required=True)
    a = ap.parse_args()
    ch, n = rename_audio()
    print(f"audio: {n} tracks, {ch} renamed to unguessable names")
    data = json.load(open("docs/data.json"))
    tracks = json.load(open("work/tracks.json"))
    bymap = {t["index"]: t["file"] for t in tracks}
    for t in data["tr"]:
        t["f"] = bymap[t["i"]]
    info = encrypt_payload(data, a.password)
    os.remove("docs/data.json")
    print(f"data.enc: {info['bytes']/1e6:.2f} MB "
          f"(from {info['raw']/1e6:.2f} MB json, gzip {info['packed']/1e6:.2f} MB)")
    print(f"PBKDF2-SHA256 {ITER:,} iterations, AES-256-GCM")
