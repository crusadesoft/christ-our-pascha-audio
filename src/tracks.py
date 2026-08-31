# -*- coding: utf-8 -*-
"""Group units into listenable tracks and cut them from the mastered audio.

Track boundaries are NOT the same as navigation marks. The book has 232
sections, but 31 of them run under a minute (some are 3 seconds) -- fine as
places to jump to, useless as files. Tracks merge the short ones and split the
overlong ones, while the reader keeps all 232 marks for navigation.

Cut from the MASTER so every track carries the same whole-book loudness
normalisation; encoding each independently would make the level drift.
"""
import json, os, sys, subprocess, argparse
import soundfile as sf
sys.path.insert(0, "src")
import chapters as chapmod
from render import PAUSE

def build_tracks(units, levels={1, 2, 3}, min_min=3.0, max_min=25.0):
    # per-unit global timing, identical to timeline.py
    t = 0.0
    timed = []
    for b in units:
        d = sf.info(b["path"]).duration
        gap = PAUSE.get(b["kind"], PAUSE["para"])
        timed.append(dict(b, _start=t, _dur=d + gap))
        t += d + gap
    total = t

    def is_head(b):
        return b["kind"] == "PART" or (
            b["kind"] == "HEADING" and
            (b.get("level") in levels or b["text"].lower() == "introduction"))

    groups, cur = [], None
    for b in timed:
        if is_head(b) or cur is None:
            cur = dict(title=b.get("title") or b["text"], units=[])
            groups.append(cur)
        cur["units"].append(b)
    for g in groups:
        g["start"] = g["units"][0]["_start"]
        g["secs"] = sum(u["_dur"] for u in g["units"])

    merged = []
    for g in groups:                       # fold short groups into the previous
        if merged and g["secs"] < min_min * 60:
            merged[-1]["units"] += g["units"]
            merged[-1]["secs"] += g["secs"]
        else:
            merged.append(dict(g))

    out = []
    for g in merged:                       # split long groups at an interior heading
        if g["secs"] <= max_min * 60:
            out.append(g); continue
        part, acc = None, 0.0
        for b in g["units"]:
            if part is None or (acc > max_min * 60 * 0.6 and b["kind"] == "HEADING"):
                part = dict(title=g["title"], units=[], start=b["_start"], secs=0.0)
                out.append(part); acc = 0.0
            part["units"].append(b); part["secs"] += b["_dur"]; acc += b["_dur"]
    for i, g in enumerate(out):
        g["index"] = i
        g["start"] = g["units"][0]["_start"]
        g["secs"] = sum(u["_dur"] for u in g["units"])
    return out, total

def main(src, outdir, bitrate, levels, min_min, max_min):
    U = json.load(open("work/units.json"))
    tracks, total = build_tracks(U, levels, min_min, max_min)
    os.makedirs(outdir, exist_ok=True)
    man = []
    for i, g in enumerate(tracks, 1):
        f = f"{g['index']:02d}.mp3"
        out = f"{outdir}/{f}"
        if not (os.path.exists(out) and os.path.getsize(out) > 1000):
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error",
                 "-ss", f"{g['start']:.3f}", "-t", f"{g['secs']:.3f}", "-i", src,
                 "-codec:a", "libmp3lame", "-b:a", bitrate, "-ar", "44100",
                 "-ac", "1", "-write_xing", "1",
                 "-metadata", f"title={g['title']}",
                 "-metadata", "album=Christ Our Pascha",
                 "-metadata", "artist=Synod of the Ukrainian Greek-Catholic Church",
                 "-metadata", f"track={g['index']+1}/{len(tracks)}",
                 out], check=True)
        man.append(dict(index=g["index"], title=g["title"], file=f,
                        start=round(g["start"], 3), seconds=round(g["secs"], 3),
                        bytes=os.path.getsize(out)))
        if i % 20 == 0 or i == len(tracks):
            print(f"  [{i}/{len(tracks)}] {sum(x['bytes'] for x in man)/1e6:.0f} MB",
                  flush=True)
    json.dump(man, open("work/tracks.json", "w"), indent=1, ensure_ascii=False)
    mb = sum(x["bytes"] for x in man) / 1e6
    print(f"\n{len(man)} tracks, {mb:.0f} MB, largest {max(x['bytes'] for x in man)/1e6:.1f} MB")
    print(f"total audio {total/3600:.2f} h")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="out/ChristOurPascha.m4b")
    ap.add_argument("--outdir", default="docs/audio")
    ap.add_argument("--bitrate", default="56k")
    ap.add_argument("--min-min", type=float, default=3.0)
    ap.add_argument("--max-min", type=float, default=25.0)
    a = ap.parse_args()
    main(a.src, a.outdir, a.bitrate, {1, 2, 3}, a.min_min, a.max_min)
