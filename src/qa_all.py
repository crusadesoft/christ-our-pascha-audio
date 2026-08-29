# -*- coding: utf-8 -*-
"""Transcribe every rendered chapter and diff against its source text.

Catches the TTS failure modes that matter: skipped sentences, repeated
spans, and truncation. Whisper's own orthography (savior/saviour, "st"
for "saint", digits for number words) is normalized away first so it
does not masquerade as a defect.
"""
import os, sys, json, re, time, difflib, argparse
import multiprocessing as mp

CH_DIR = "work/chapters"

# Whisper spelling/format differences that are not TTS defects
_EQUIV = [
 (r"\bst\b", "saint"), (r"\bsavior\b", "saviour"), (r"\bhonor", "honour"),
 (r"\bfulfillment\b", "fulfilment"), (r"\blabor", "labour"),
 (r"\bneighbor", "neighbour"), (r"\bcenter\b", "centre"),
 (r"\bdefense\b", "defence"), (r"\bpractise\b", "practice"),
 (r"\binflamed\b", "enflamed"), (r"\bjudgement\b", "judgment"),
]
_NUM = {"one":"1","two":"2","three":"3","four":"4","five":"5","six":"6",
        "seven":"7","eight":"8","nine":"9","ten":"10","eleven":"11",
        "twelve":"12","first":"1","second":"2","third":"3"}

def canon(s):
    s = s.lower()
    for pat, rep in _EQUIV:
        s = re.sub(pat, rep, s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    toks = [_NUM.get(t, t) for t in s.split()]
    return [t for t in toks if t]

def analyse(src, hyp):
    """Report only spans genuinely absent from the other side. difflib will
    code a transposition as delete+insert of the same words; those are
    alignment artifacts, not dropped or hallucinated audio."""
    a, b = canon(src), canon(hyp)
    astr, bstr = " ".join(a), " ".join(b)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    gaps = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "delete" and (i2 - i1) >= 5:
            span = " ".join(a[i1:i2])
            if span not in bstr:                 # truly unspoken
                gaps.append(("skip", i1, span[:120]))
        elif tag == "insert" and (j2 - j1) >= 8:
            span = " ".join(b[j1:j2])
            if span not in astr:                 # truly not in the source
                gaps.append(("extra", j1, span[:120]))
    return sm.ratio(), len(a), gaps

def _init(model_size):
    global _M
    from faster_whisper import WhisperModel
    _M = WhisperModel(model_size, device="cpu", compute_type="int8")

def _work(idx):
    wav = f"{CH_DIR}/{idx:03d}.wav"
    ch = json.load(open("work/chapters.json"))[idx]
    src = " ".join(b["text"] for b in ch["blocks"])
    t0 = time.time()
    segs, _ = _M.transcribe(wav, language="en", beam_size=1,
                            condition_on_previous_text=False)
    hyp = " ".join(s.text for s in segs)
    ratio, n, gaps = analyse(src, hyp)
    return dict(index=idx, title=ch["title"], words=n, ratio=ratio,
                gaps=gaps, sec=time.time() - t0)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="base")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    chs = json.load(open("work/chapters.json"))
    todo = [c["index"] for c in chs
            if os.path.exists(f"{CH_DIR}/{c['index']:03d}.wav")]
    if a.limit:
        todo = todo[:a.limit]
    print(f"QA on {len(todo)} chapters with whisper-{a.model}")
    mp.set_start_method("spawn", force=True)
    res, t0 = [], time.time()
    with mp.Pool(a.workers, initializer=_init, initargs=(a.model,)) as pool:
        for i, r in enumerate(pool.imap_unordered(_work, todo), 1):
            res.append(r)
            flag = "  <-- REVIEW" if (r["ratio"] < 0.93 or r["gaps"]) else ""
            print(f"[{i:3d}/{len(todo)}] ch{r['index']:03d} sim={r['ratio']:.4f} "
                  f"gaps={len(r['gaps'])} {r['sec']:5.1f}s{flag}", flush=True)
    res.sort(key=lambda r: r["index"])
    json.dump(res, open("work/qa_report.json", "w"), indent=1)
    bad = [r for r in res if r["ratio"] < 0.93 or r["gaps"]]
    print(f"\n{len(res)} chapters checked in {(time.time()-t0)/60:.1f} min")
    print(f"mean similarity {sum(r['ratio'] for r in res)/len(res):.4f}")
    print(f"flagged for review: {len(bad)}")
    for r in bad[:25]:
        print(f"  ch{r['index']:03d} sim={r['ratio']:.4f} {r['title'][:48]}")
        for kind, pos, txt in r["gaps"][:3]:
            print(f"        {kind}: {txt}")
