"""Render a body -> QUOTE -> body passage with a contrasting quote voice."""
import sys, json, argparse
import numpy as np, soundfile as sf
sys.path.insert(0, "src")
from render import make_pipeline, render_blocks, SR, silence

ap = argparse.ArgumentParser()
ap.add_argument("--body", default="am_michael")
ap.add_argument("--quotes", default="bm_george,bm_fable,af_heart,bf_emma,am_onyx")
ap.add_argument("--index", type=int, default=95)
a = ap.parse_args()

N = json.load(open("work/normalized.json"))
seq = N[a.index:a.index+3]
pipe = make_pipeline()
for qv in a.quotes.split(","):
    parts = []
    for b in seq:
        v = qv if b["kind"] == "QUOTE" else a.body
        parts.append(render_blocks(pipe, [b], v))
    sf.write(f"out/quote_{qv}.wav", np.concatenate(parts), SR)
    print(f"  wrote out/quote_{qv}.wav  (body={a.body}, quote={qv})")
