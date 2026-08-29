# -*- coding: utf-8 -*-
"""Concatenate rendered units into chapter WAVs, applying inter-block pauses."""
import os, sys, json, argparse
import numpy as np, soundfile as sf
sys.path.insert(0, "src")
import chapters as chapmod
from render import PAUSE, SR

OUT = "work/chapters"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap-scale", type=float, default=1.0)
    a = ap.parse_args()
    U = json.load(open("work/units.json"))
    missing = [u["seq"] for u in U if not os.path.exists(u["path"])]
    if missing:
        raise SystemExit(f"{len(missing)} units not rendered: {missing[:12]}")

    chs = chapmod.build(U)
    # Write chapters.json here too: qa_all.py reads it as its source text,
    # and if only chapters.py wrote it, it would silently go stale whenever
    # normalization changed -- making QA diff new audio against old text.
    json.dump(chs, open("work/chapters.json", "w"), indent=1, ensure_ascii=False)
    os.makedirs(OUT, exist_ok=True)
    total = 0.0
    meta = []
    for c in chs:
        parts = []
        for b in c["blocks"]:
            audio, _ = sf.read(b["path"], dtype="float32")
            parts.append(audio)
            gap = PAUSE.get(b["kind"], PAUSE["para"]) * a.gap_scale
            parts.append(np.zeros(int(SR * gap), dtype="float32"))
        out = np.concatenate(parts)
        sf.write(f"{OUT}/{c['index']:03d}.wav", out, SR)
        total += len(out) / SR
        meta.append(dict(index=c["index"], title=c["title"],
                         seconds=len(out)/SR, units=len(c["blocks"])))
    json.dump(meta, open("work/chapter_meta.json", "w"), indent=1, ensure_ascii=False)
    print(f"assembled {len(chs)} chapters, {total/3600:.2f} h")
    for m in sorted(meta, key=lambda m: -m["seconds"])[:5]:
        print(f"   {m['seconds']/60:6.1f} min  {m['title'][:60]}")
