# -*- coding: utf-8 -*-
"""Build an exact timeline of the audiobook and emit subtitle files.

Timings are derived from the real duration of every rendered unit plus the
pauses assembly inserts -- not from speech recognition -- so unit boundaries
are exact. Within a long unit, sentence cues are apportioned by character
count, which is approximate but ample for scrubbing.
"""
import json, os, re, sys
import soundfile as sf
sys.path.insert(0, "src")
import chapters as chapmod
from render import PAUSE, sentences

def build():
    U = json.load(open("work/units.json"))
    chs = chapmod.build(U)
    t = 0.0
    cues, chapter_marks = [], []
    for c in chs:
        chapter_marks.append(dict(index=c["index"], title=c["title"],
                                  level=c.get("level", 0), start=t))
        for b in c["blocks"]:
            dur = sf.info(b["path"]).duration
            gap = PAUSE.get(b["kind"], PAUSE["para"])
            sents = sentences(b["text"]) or [b["text"]]
            # "32." opens a numbered paragraph and the splitter treats it as
            # its own sentence; fold it into the next so cues aren't stranded
            if len(sents) > 1 and re.fullmatch(r"\d{1,4}\.", sents[0].strip()):
                sents = [sents[0] + " " + sents[1]] + sents[2:]
            total = sum(len(s) for s in sents) or 1
            st = t
            for s in sents:
                span = dur * len(s) / total
                cues.append(dict(start=round(st, 3), end=round(st + span, 3),
                                 text=s, kind=b["kind"], para=b["para"],
                                 chapter=c["index"], seq=b["seq"]))
                st += span
            t += dur + gap
    return chapter_marks, cues, t

def ts(sec, comma=True):
    h = int(sec // 3600); m = int(sec % 3600 // 60)
    s = sec % 60
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)):03d}"

if __name__ == "__main__":
    marks, cues, total = build()
    json.dump(dict(total=total, chapters=marks, cues=cues),
              open("work/timeline.json", "w"), ensure_ascii=False)
    with open("out/ChristOurPascha.srt", "w") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n")
    with open("out/ChristOurPascha.vtt", "w") as f:
        f.write("WEBVTT\n\n")
        for c in cues:
            f.write(f"{ts(c['start'],False)} --> {ts(c['end'],False)}\n{c['text']}\n\n")
    print(f"timeline: {len(cues):,} cues across {len(marks)} chapters, "
          f"{total/3600:.2f} h")
    print(f"  out/ChristOurPascha.srt")
    print(f"  out/ChristOurPascha.vtt")
