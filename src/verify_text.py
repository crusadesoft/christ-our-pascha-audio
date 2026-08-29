# -*- coding: utf-8 -*-
"""Gate: prove the extracted text covers the source PDF, before synthesis.

This is the check that was missing. The audio QA (qa_all.py) compares the
rendered audio against the EXTRACTED text, so anything the extractor drops
is invisible to it -- both sides share the same loss. This stage compares
extracted text against the PDF itself.

Two independent checks:
  1. Coverage  - a multiset diff, so it is order-independent and catches
                 dropped words even if reading order changed.
  2. Sequence  - contiguous runs present in the PDF but absent from the
                 output in order, which catches structural skips.

Exits non-zero if either check breaches its threshold, so it can gate a run.
"""
import pymupdf, json, re, sys, difflib, collections, argparse
sys.path.insert(0, "src")
from extract import BODY_START, BODY_END

def words(s):
    s = s.replace("\xad", "").replace(" ", " ").replace(" ", " ")
    return re.sub(r"[^a-zA-Z0-9]+", " ", s).lower().split()

def pdf_reference(path):
    """Every word the PDF prints as body-level type, independent of extract.py.

    Mirrors three realities of this document so the comparison is meaningful:
      * small-caps headings are set as a large initial + ~8.4pt remainder,
        so size is judged per LINE (max span), not per span;
      * line-break hyphenation uses U+00AD, so lines are joined before
        tokenising, or every hyphenated word yields two bogus fragments;
      * footnotes (9pt), page numbers and marginal numbers are excluded.
    """
    doc = pymupdf.open(path)
    out = []
    for pno in range(BODY_START, BODY_END):
        page_lines = []
        for b in doc[pno].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [s for s in l["spans"]
                         if s["text"].strip() and s["size"] >= 8.0]
                if not spans:
                    continue
                if max(s["size"] for s in spans) < 9.6:
                    continue                           # footnote body
                y0 = l["bbox"][1]
                txt = "".join(s["text"] for s in spans)
                bare = txt.strip()
                if y0 > 600 and re.fullmatch(r"[0-9ivxlcIVXLC]{1,6}", bare):
                    continue                           # page number
                if spans[0]["bbox"][0] < 70 and spans[0]["size"] <= 11.5:
                    if re.fullmatch(r"\d{1,4}", bare):
                        continue                       # marginal paragraph number
                    # PyMuPDF merges 3-digit marginal numbers into the body
                    # line ("224The good deed..."); strip the number so the
                    # reference matches what a correct extractor produces.
                    txt = re.sub(r"^\s*\d{1,4}(?=[\t ]|[A-Z])", " ", txt, count=1)
                page_lines.append((l["bbox"][1], spans[0]["bbox"][0], txt))

        # Two-column appendix pages read column-by-column, split into three
        # horizontal bands (left margin / centred full-width / right column).
        # NOTE: this mirrors extract.py, so ORDERING on these two pages is not
        # independently verified -- it was checked against the printed page by
        # hand. The coverage check above is fully independent and is the gate
        # that matters for dropped text.
        left   = [r for r in page_lines if r[1] < 100.0]
        centre = [r for r in page_lines if 100.0 <= r[1] < 200.0]
        right  = [r for r in page_lines if r[1] >= 200.0]
        if len(left) >= 8 and len(right) >= 8 and len(right) >= 0.3 * len(left):
            colys = [r[0] for r in left + right]
            top = min(colys)
            page_lines = (sorted([c for c in centre if c[0] < top])
                          + sorted(left) + sorted(right)
                          + sorted([c for c in centre if c[0] >= top]))
        else:
            page_lines.sort()
        page_lines = [t for _, _, t in page_lines]

        joined = ""
        for ln in page_lines:
            if joined.endswith("\xad"):
                joined = joined[:-1] + ln
            else:
                joined = joined + " " + ln
        out += words(joined)
    return out


def main(pdf, normalized, max_missing_pct, max_run):
    ref = pdf_reference(pdf)
    got = []
    for x in json.load(open(normalized)):
        got += words(x["text"])

    # 1. coverage (order-independent)
    cr, cg = collections.Counter(ref), collections.Counter(got)
    missing = cr - cg
    n_missing = sum(missing.values())
    pct = n_missing / len(ref) * 100

    # 2. sequence: contiguous runs of reference text absent in order
    sm = difflib.SequenceMatcher(None, ref, got, autojunk=False)
    runs = [(i2 - i1, " ".join(ref[i1:i2]))
            for tag, i1, i2, j1, j2 in sm.get_opcodes()
            if tag in ("delete", "replace") and (i2 - i1) >= 8]
    worst = max((n for n, _ in runs), default=0)

    print(f"PDF reference words : {len(ref):,}")
    print(f"extracted words     : {len(got):,}")
    print(f"coverage misses     : {n_missing:,} words ({pct:.3f}%)")
    print(f"contiguous runs >=8 : {len(runs)}  (longest {worst} words)")
    if missing:
        print("\n  most-missed tokens:")
        for w, c in missing.most_common(10):
            print(f"    {c:4d}x  {w}")
    if runs:
        print("\n  longest missing runs:")
        for n, t in sorted(runs, reverse=True)[:6]:
            print(f"    [{n:4d}] {t[:96]}")

    ok = pct <= max_missing_pct and worst <= max_run
    print(f"\nRESULT: {'PASS' if ok else 'FAIL'} "
          f"(limits: <={max_missing_pct}% missing, <={max_run}-word runs)")
    return 0 if ok else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="ref/source.pdf")
    ap.add_argument("--normalized", default="work/blocks.json")
    ap.add_argument("--max-missing-pct", type=float, default=0.10)
    ap.add_argument("--max-run", type=int, default=20)
    a = ap.parse_args()
    sys.exit(main(a.pdf, a.normalized, a.max_missing_pct, a.max_run))
