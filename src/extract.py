"""Structure-aware extraction of Christ Our Pascha from the 2017 PDF.

Classification is by font size + x-position, verified against the PDF's
InDesign layout:
  body 11pt @ x=76.5      block quote 10pt @ x>=82
  heading >=12pt          footnote 9pt (page foot)
  superscript ref <8pt    marginal paragraph number 10pt @ x<70, digits only

Marginal numbers must be split at SPAN level: PyMuPDF merges 3-digit
numbers into the following body line.
"""
import pymupdf, json, re

COL_SPLIT = 200.0   # page is 432pt wide
ENUM_RE = re.compile(r"^(?:[IVXL]{1,6}\.|[A-Z]\.|\d{1,2}[.)]|[a-z]\.)\s")

BODY_START, BODY_END = 16, 338
PART_DIVIDERS = {30: "Part One: The Faith of the Church",
                 134: "Part Two: The Prayer of the Church",
                 250: "Part Three: The Life of the Church"}


def classify(doc):
    out = []
    for pno in range(BODY_START, BODY_END):
        page = doc[pno]
        rows = []
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                keep = [s for s in l["spans"]
                        if s["text"].strip() and s["size"] >= 8.0]
                # superscript markers (<8pt digits) name the footnote that
                # carries a quote's attribution; record them, do not speak them
                marks = [int(m) for s in l["spans"] if s["size"] < 8.0
                         for m in re.findall(r"\d{1,4}", s["text"])]
                if keep:
                    rows.append((round(l["bbox"][1], 1), keep, marks))
        # Two-column appendix pages (the sin/virtue lists) read column by
        # column. Three horizontal bands distinguish them: the left column
        # sits at the left margin, the right column past COL_SPLIT, and
        # centred full-width lines (section headers, greetings) in between.
        # Using the right column's vertical extent instead would slice the
        # left column's list in half.
        key = lambda r: (r[0], r[1][0]["bbox"][0])
        xof = lambda r: r[1][0]["bbox"][0]
        left   = [r for r in rows if xof(r) < 100.0]
        centre = [r for r in rows if 100.0 <= xof(r) < COL_SPLIT]
        right  = [r for r in rows if xof(r) >= COL_SPLIT]
        two_col = (len(left) >= 8 and len(right) >= 8
                   and len(right) >= 0.3 * len(left))
        if two_col:
            colys = [r[0] for r in left + right]
            top, bot = min(colys), max(colys)
            rows = (sorted([c for c in centre if c[0] < top], key=key)
                    + sorted(left, key=key) + sorted(right, key=key)
                    + sorted([c for c in centre if c[0] >= top], key=key))
        else:
            rows.sort(key=key)

        kept = []
        for y0, spans, marks in rows:
            # split off a marginal paragraph number carried in the first span
            first = spans[0]
            if first["bbox"][0] < 70 and first["size"] <= 11.5 and y0 <= 600:
                ft = first["text"]
                if re.fullmatch(r"\d{1,4}\s*", ft):
                    kept.append(("PARANUM", ft.strip()))
                    spans = spans[1:]
                    if not spans:
                        continue
                else:
                    # one-off: number typeset into the body span (e.g. para 189)
                    m = re.match(r"(\d{1,4})[\t ]+(\S.*)$", ft, re.S)
                    if m:
                        kept.append(("PARANUM", m.group(1)))
                        first = dict(first); first["text"] = m.group(2)
                        spans = [first] + spans[1:]

            x0 = spans[0]["bbox"][0]
            size = max(s["size"] for s in spans)
            text = re.sub(r"[\t  ]+", " ", "".join(s["text"] for s in spans))
            text = text.strip()
            if not text:
                continue
            if marks:
                kept.append(("MARKS", marks))
            if y0 > 600 and re.fullmatch(r"[0-9ivxlcIVXLC]{1,6}", text):
                continue                                   # page number
            if size < 9.6:                                 # 9pt footnote text
                continue
            if size >= 11.8:
                kept.append(("HEADING", text))
            elif size >= 10.6:
                kept.append(("BODY", text))
            else:
                # 9.6-10.6pt is block-quote / prayer type. Do NOT gate on x0:
                # the appendix prayer sections are set at x=54-63 and were
                # being silently discarded. Footnotes are 9pt and already
                # excluded by the size test above.
                kept.append(("QUOTE", text))
        out.append((pno, kept))
    return out


def join_lines(chunks):
    """Merge lines into blocks. Paragraph numbers are accepted only when they
    continue the 1..1001 sequence; a non-sequential match is a citation
    numeral (e.g. the "1" of "1 Jn 4:19") and is folded back into the text."""
    blocks, state = [], dict(kind=None, buf=[], para=None, pending=None, expected=1)

    def flush():
        if state["buf"]:
            text = ""
            for i, ln in enumerate(state["buf"]):
                if i == 0:
                    text = ln
                elif text.endswith("­"):
                    text = text[:-1] + ln
                elif text.endswith("-"):
                    text = text + ln                # real compound hyphen: keep
                else:
                    text = text.rstrip() + " " + ln
            blocks.append(dict(kind=state["kind"], para=state["para"],
                               refs=sorted(set(state.get("marks", []))),
                               text=re.sub(r"\s+", " ", text).strip()))
        state["buf"], state["para"] = [], None
        state["marks"] = []

    for pno, kept in chunks:
        if pno in PART_DIVIDERS:
            flush(); state["kind"] = None
            blocks.append(dict(kind="PART", para=None, text=PART_DIVIDERS[pno]))
        for kind, text in kept:
            if kind == "MARKS":
                state.setdefault("marks", []).extend(text)
                continue
            if kind == "PARANUM":
                n = int(text)
                if n == state["expected"]:
                    flush(); state["kind"] = "BODY"; state["para"] = n
                    state["expected"] += 1
                else:
                    state["pending"] = text
                continue
            if state["pending"]:
                text = state["pending"] + " " + text
                state["pending"] = None
            if kind != state["kind"]:
                flush(); state["kind"] = kind
            elif kind == "HEADING" and ENUM_RE.match(text):
                flush(); state["kind"] = kind      # new heading, not a wrapped line
            state["buf"].append(text)
    flush()
    return [b for b in blocks if b["text"]]


if __name__ == "__main__":
    doc = pymupdf.open("ref/source.pdf")
    blocks = join_lines(classify(doc))
    json.dump(blocks, open("work/blocks.json", "w"), indent=1, ensure_ascii=False)
    kinds = {}
    for b in blocks:
        kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    words = sum(len(b["text"].split()) for b in blocks)
    paras = [b["para"] for b in blocks if b["para"]]
    print(f"blocks: {len(blocks)}  {kinds}")
    print(f"words:  {words:,}  (~{words/150/60:.1f} h at 150 wpm)")
    print(f"paragraph numbers: {len(paras)}  range {min(paras)}–{max(paras)}")
    missing = sorted(set(range(1, max(paras)+1)) - set(paras))
    print(f"missing paragraph numbers: {len(missing)} {missing[:20]}")
