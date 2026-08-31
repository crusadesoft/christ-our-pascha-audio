# -*- coding: utf-8 -*-
"""Group normalized blocks into chapters for rendering and M4B markers.

A new chapter starts at every PART divider, every roman-numeral heading
(the 12 major divisions), and every top-level lettered subsection.
"""
import json, re

def _lvl(b):
    """Outline depth, from metadata. The spoken text no longer carries the
    printed enumerator, so it cannot be recovered by matching the text."""
    return b.get("level", 0)


def build(blocks):
    chapters, cur = [], None
    def start(title, level=0):
        nonlocal cur
        cur = dict(title=title, level=level, blocks=[])
        chapters.append(cur)

    start("Front Matter")
    for b in blocks:
        t = b["text"]
        if b["kind"] == "PART":
            start(t, 0)
        elif b["kind"] == "HEADING" and (_lvl(b) in (1, 2, 3, 5)
                                         or t.lower() == "introduction"):
            # chapter list shows the printed label; narration omits it
            start(re.sub(r"\s+", " ", b.get("title") or t), _lvl(b))
        elif cur is None:
            start("Front Matter")
        cur["blocks"].append(b)
    chapters = [c for c in chapters if c["blocks"]]
    for i, c in enumerate(chapters):
        c["index"] = i
        c["words"] = sum(len(b["text"].split()) for b in c["blocks"])
        c["est_sec"] = c["words"] / 150 * 60
    return chapters

if __name__ == "__main__":
    N = json.load(open("work/normalized.json"))
    ch = build(N)
    json.dump(ch, open("work/chapters.json", "w"), indent=1, ensure_ascii=False)
    total = sum(c["est_sec"] for c in ch)
    print(f"{len(ch)} chapters, est total {total/3600:.2f} h\n")
    for c in ch:
        print(f"  {c['index']:3d}  {c['est_sec']/60:6.1f} min  {c['title'][:70]}")
    big = [c for c in ch if c["est_sec"] > 45*60]
    print(f"\nchapters over 45 min: {len(big)}")
