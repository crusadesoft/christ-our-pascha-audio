# -*- coding: utf-8 -*-
"""Content-addressed render units.

One unit = one normalized block (paragraph, heading, quote, part divider).
A unit's identity is its text + voice + speed + the lexicon entries that
actually apply to it, so a pronunciation fix re-renders only the units
containing that word. Pauses are NOT baked into units; they are applied at
assembly, so pause tuning costs nothing.
"""
import hashlib, json, sys
sys.path.insert(0, "src")
import lexicon

UNIT_DIR = "work/units"

def unit_key(text, voice, speed):
    sig = lexicon.applicable(text)
    raw = f"{voice}|{speed}|{sig}|{text}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]

def voice_for(kind, body, quote):
    """Block quotes get their own voice so quotations are audibly marked."""
    return quote if kind == "QUOTE" else body


def build(blocks, body, speed, quote=None):
    """Attach a stable cache key + path to every block.

    The voice is part of the key, so changing only the quote voice
    re-renders only the quote units.
    """
    quote = quote or body
    out = []
    for i, b in enumerate(blocks):
        v = voice_for(b["kind"], body, quote)
        k = unit_key(b["text"], v, speed)
        out.append(dict(seq=i, kind=b["kind"], para=b["para"], voice=v,
                        level=b.get("level", 0), title=b.get("title", b["text"]),
                        text=b["text"], key=k, path=f"{UNIT_DIR}/{k}.wav"))
    return out

if __name__ == "__main__":
    import argparse, os, collections
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="body voice")
    ap.add_argument("--quote-voice", default=None,
                    help="voice for block quotes (default: same as body)")
    ap.add_argument("--speed", type=float, default=1.0)
    a = ap.parse_args()
    N = json.load(open("work/normalized.json"))
    U = build(N, a.voice, a.speed, a.quote_voice)
    os.makedirs(UNIT_DIR, exist_ok=True)
    json.dump(U, open("work/units.json", "w"), indent=1, ensure_ascii=False)
    have = sum(1 for u in U if os.path.exists(u["path"]))
    dup = len(U) - len({u["key"] for u in U})
    kinds = collections.Counter(u["kind"] for u in U)
    words = sum(len(u["text"].split()) for u in U)
    print(f"{len(U)} units  ({dup} identical-text duplicates share a render)")
    print(f"  kinds: {dict(kinds)}")
    import collections as _c
    print(f"  voices: {dict(_c.Counter(u['voice'] for u in U))}")
    print(f"  words: {words:,}   cached already: {have}")
    lex_touched = sum(1 for u in U if lexicon.applicable(u["text"]))
    print(f"  units affected by lexicon overrides: {lex_touched} "
          f"({lex_touched/len(U)*100:.0f}%)")
