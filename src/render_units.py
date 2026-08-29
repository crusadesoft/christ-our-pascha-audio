# -*- coding: utf-8 -*-
"""Render every uncached unit to WAV, in parallel. Resumable by content hash."""
import os, sys, json, time, argparse, gc
import multiprocessing as mp

SR = 24000

def _init(voice, speed, threads):
    global _P, _V, _S
    import torch
    torch.set_num_threads(threads)
    sys.path.insert(0, "src")
    from render import make_pipeline
    _P = make_pipeline(); _V = voice; _S = speed

def _work(u):
    import numpy as np, soundfile as sf
    sys.path.insert(0, "src")
    from render import chunks
    if os.path.exists(u["path"]) and os.path.getsize(u["path"]) > 800:
        return u["seq"], 0.0, 0.0, True, None
    t0 = time.time()
    try:
        parts = []
        for ch in chunks(u["text"]):
            for _, _, a in _P(ch, voice=u.get("voice", _V), speed=_S):
                parts.append(a if isinstance(a, np.ndarray) else a.numpy())
        if not parts:
            return u["seq"], 0.0, time.time()-t0, False, "empty"
        audio = np.concatenate(parts)
        tmp = u["path"] + ".tmp.wav"          # keep .wav: soundfile infers
        sf.write(tmp, audio, SR)                 # the format from the extension
        os.replace(tmp, u["path"])
        dur = len(audio) / SR
        del parts, audio
        gc.collect()
        return u["seq"], dur, time.time()-t0, False, None
    except Exception as e:
        return u["seq"], 0.0, time.time()-t0, False, repr(e)[:200]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--units", default="work/units.json")
    ap.add_argument("--recycle", type=int, default=40,
                    help="restart the worker every N units to bound memory")
    a = ap.parse_args()

    U = json.load(open(a.units))
    os.makedirs("work/units", exist_ok=True)
    seen, todo = set(), []
    for u in U:                                  # dedupe identical-text units
        if u["key"] in seen:
            continue
        seen.add(u["key"]); todo.append(u)
    todo.sort(key=lambda u: u["seq"])            # document order: spreads the
    # large units across the run instead of piling them all at the start, and
    # makes partial output contiguous and playable from the beginning
    print(f"{len(U)} units, {len(todo)} distinct; rendering", flush=True)

    mp.set_start_method("spawn", force=True)
    t0, audio_s, n_new, errs = time.time(), 0.0, 0, []
    with mp.Pool(a.workers, initializer=_init,
                 initargs=(a.voice, a.speed, a.threads),
                 maxtasksperchild=a.recycle) as pool:
        for i, (seq, dur, el, cached, err) in enumerate(
                pool.imap_unordered(_work, todo, chunksize=1), 1):
            if err:
                errs.append((seq, err))
            audio_s += dur
            if not cached:
                n_new += 1
            if i % 25 == 0 or i == len(todo) or err:
                w = time.time() - t0
                eta = (len(todo)-i) / max(i/w, 1e-9) / 60
                print(f"[{i:4d}/{len(todo)}] audio {audio_s/3600:5.2f}h "
                      f"wall {w/60:5.1f}m ({audio_s/max(w,1e-9):5.1f}x) "
                      f"eta {eta:4.1f}m" + (f"  ERR seq{seq}: {err}" if err else ""),
                      flush=True)
    print(f"\nrendered {n_new} new units, {audio_s/3600:.2f} h speech "
          f"in {(time.time()-t0)/60:.1f} min, {len(errs)} errors")
    for s, e in errs[:15]:
        print(f"   seq {s}: {e}")
