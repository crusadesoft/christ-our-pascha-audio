# -*- coding: utf-8 -*-
"""Extract the footnote apparatus: number -> source text.

Footnotes are 9pt, set at the foot of the page, each opening with its number
in ~5.25pt. The body extractor drops them (they are unlistenable as-is); this
recovers them so quote attributions can be spoken.
"""
import pymupdf, re, json, sys
sys.path.insert(0, "src")
from extract import BODY_START, BODY_END

def extract(path="ref/source.pdf"):
    doc = pymupdf.open(path)
    notes = {}
    for pno in range(BODY_START, BODY_END):
        rows = []
        for b in doc[pno].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [s for s in l["spans"] if s["text"].strip()]
                if not spans:
                    continue
                rows.append((round(l["bbox"][1], 1), spans))
        rows.sort(key=lambda r: r[0])
        cur = None
        for y0, spans in rows:
            sizes = [s["size"] for s in spans]
            # a footnote line: 9pt body, possibly opening with a tiny number
            if not any(8.5 <= s <= 9.4 for s in sizes):
                continue
            first = spans[0]
            m = re.fullmatch(r"\s*(\d{1,4})\s*", first["text"])
            if m and first["size"] < 8.0:
                cur = int(m.group(1))
                notes[cur] = "".join(s["text"] for s in spans[1:]).strip()
            elif cur is not None:
                add = "".join(s["text"] for s in spans)
                prev = notes[cur]
                # soft hyphen at a line break joins the word ("Gaudi\xad" + "um")
                if prev.endswith("\xad"):
                    notes[cur] = prev[:-1] + add.lstrip()
                elif prev.endswith("-"):
                    notes[cur] = prev + add.lstrip()
                else:
                    notes[cur] = (prev + " " + add).strip()
    return {k: re.sub(r"\s+", " ", v.replace("\xad", "")) for k, v in notes.items()}

if __name__ == "__main__":
    n = extract()
    json.dump(n, open("work/footnotes.json", "w"), indent=1, ensure_ascii=False)
    ks = sorted(n)
    print(f"footnotes: {len(n)}  range {min(ks)}-{max(ks)}")
    print(f"missing in range: {len(set(range(min(ks),max(ks)+1)) - set(ks))}")
    print("\nsamples:")
    for k in ks[:14]:
        print(f"  {k:4d}  {n[k][:96]}")
