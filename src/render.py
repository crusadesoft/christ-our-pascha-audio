# -*- coding: utf-8 -*-
"""Render normalized blocks to audio with Kokoro."""
import sys, re, json, time
import numpy as np, soundfile as sf
sys.path.insert(0, "src")
import lexicon

SR = 24000
MAX_CHARS = 380
PAUSE = {"sent": 0.00, "para": 0.45, "HEADING": 0.75, "PART": 1.40, "QUOTE": 0.35}

_ABBR = r"(?<!\bSt)(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bvs)(?<!\bcf)(?<!\bi\.e)(?<!\be\.g)"

def sentences(text):
    parts = re.split(rf'{_ABBR}(?<=[.!?])["\')\]]*\s+(?=[A-Z"\'(])', text)
    return [p.strip() for p in parts if p.strip()]

def chunks(text, limit=MAX_CHARS):
    """Split text into synthesis-sized pieces, preserving order exactly.

    A sentence longer than `limit` is broken at commas. Its fragments must
    not be emitted before the buffer of already-accumulated sentences, or
    the audio plays the long sentence first and the earlier text after it.
    """
    out, cur = [], ""

    def flush():
        nonlocal cur
        if cur:
            out.append(cur)
            cur = ""

    for s in sentences(text):
        if len(s) > limit:
            flush()                                # order: pending text first
            while len(s) > limit:                  # then split at a comma,
                cut = s.rfind(", ", 0, limit)      # else a word boundary --
                if cut > limit // 2:               # never mid-word
                    cut += 1
                else:
                    cut = s.rfind(" ", 0, limit)
                    if cut <= 0:
                        cut = limit
                out.append(s[:cut].strip())
                s = s[cut:].strip()
            if not s:
                continue
        if not cur:
            cur = s
        elif len(cur) + 1 + len(s) <= limit:
            cur += " " + s
        else:
            flush(); cur = s
    flush()
    return out

def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)

def make_pipeline(voice_lang="a"):
    from kokoro import KPipeline
    p = KPipeline(lang_code=voice_lang)
    lexicon.install(p)
    return p

def render_blocks(pipe, blocks, voice, speed=1.0):
    audio = []
    for b in blocks:
        for ch in chunks(b["text"]):
            for _, _, a in pipe(ch, voice=voice, speed=speed):
                audio.append(a if isinstance(a, np.ndarray) else a.numpy())
        audio.append(silence(PAUSE.get(b["kind"], PAUSE["para"])))
    return np.concatenate(audio) if audio else silence(0.1)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", default="am_michael,bm_george,am_fenrir,bm_lewis")
    ap.add_argument("--speed", type=float, default=1.0)
    args = ap.parse_args()

    N = json.load(open("work/normalized.json"))
    # sample: the opening of the Introduction + a dense-vocabulary passage
    intro = [b for b in N if b["para"] in (1, 2)]
    hard = [b for b in N if b["para"] in (224,)]
    idx = next(i for i, b in enumerate(N) if b["para"] == 480)
    litur = N[idx:idx+2]
    sample = intro + hard + litur
    print("sample blocks:", [(b["kind"], b["para"]) for b in sample])
    print("words:", sum(len(b["text"].split()) for b in sample))

    pipe = make_pipeline()
    for v in args.voices.split(","):
        t0 = time.time()
        a = render_blocks(pipe, sample, v, args.speed)
        sf.write(f"out/sample_{v}.wav", a, SR)
        print(f"  {v:12s} {len(a)/SR:6.1f}s audio in {time.time()-t0:5.1f}s "
              f"({len(a)/SR/(time.time()-t0):.1f}x)")
