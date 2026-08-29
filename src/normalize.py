# -*- coding: utf-8 -*-
"""Turn extracted blocks into speech-ready text.

Handles: scripture citation expansion, roman numerals, bracketed glosses,
ellipses/dashes/quotes, residual soft hyphens, Psalm dual numbering, and
the one Greek phrase in the book.
"""
import re, json, os

BOOKS = {
 "Gn":"Genesis","Gen":"Genesis","Ex":"Exodus","Lv":"Leviticus","Lev":"Leviticus",
 "Nm":"Numbers","Dt":"Deuteronomy","Jos":"Joshua","Jgs":"Judges","Ru":"Ruth",
 "1 Sm":"First Samuel","1 Sam":"First Samuel","2 Sm":"Second Samuel","2 Sam":"Second Samuel",
 "1 Kgs":"First Kings","2 Kgs":"Second Kings","1 Chr":"First Chronicles","2 Chr":"Second Chronicles",
 "Ezr":"Ezra","Neh":"Nehemiah","Tb":"Tobit","Tob":"Tobit","Jdt":"Judith","Est":"Esther",
 "1 Mc":"First Maccabees","2 Mc":"Second Maccabees","Jb":"Job","Job":"Job","Ps":"Psalm",
 "Prv":"Proverbs","Eccl":"Ecclesiastes","Sg":"Song of Songs","Wis":"Wisdom","Sir":"Sirach",
 "Is":"Isaiah","Isa":"Isaiah","Jer":"Jeremiah","Lam":"Lamentations","Bar":"Baruch",
 "Ez":"Ezekiel","Ezek":"Ezekiel","Dn":"Daniel","Dan":"Daniel","Hos":"Hosea","Jl":"Joel",
 "Am":"Amos","Ob":"Obadiah","Jon":"Jonah","Mi":"Micah","Na":"Nahum","Hab":"Habakkuk",
 "Zep":"Zephaniah","Hg":"Haggai","Zec":"Zechariah","Mal":"Malachi",
 "Mt":"Matthew","Mk":"Mark","Lk":"Luke","Jn":"John","Acts":"Acts","Rom":"Romans",
 "1 Cor":"First Corinthians","2 Cor":"Second Corinthians","Gal":"Galatians",
 "Eph":"Ephesians","Phil":"Philippians","Col":"Colossians",
 "1 Thes":"First Thessalonians","2 Thes":"Second Thessalonians",
 "1 Tm":"First Timothy","1 Tim":"First Timothy","2 Tm":"Second Timothy","2 Tim":"Second Timothy",
 "Ti":"Titus","Phlm":"Philemon","Heb":"Hebrews","Jas":"James",
 "1 Pt":"First Peter","2 Pt":"Second Peter","1 Jn":"First John","2 Jn":"Second John",
 "3 Jn":"Third John","Jude":"Jude","Rev":"Revelation",
}
_BOOK_RE = "|".join(sorted((re.escape(k) for k in BOOKS), key=len, reverse=True))

ROMAN = {"I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7,"VIII":8,"IX":9,"X":10,
         "XI":11,"XII":12,"XIII":13,"XIV":14,"XV":15,"XVI":16}
ORD = {1:"One",2:"Two",3:"Three",4:"Four",5:"Five",6:"Six",7:"Seven",8:"Eight",
       9:"Nine",10:"Ten",11:"Eleven",12:"Twelve"}
ORDINAL = {2:"the Second",9:"the Ninth",13:"the Thirteenth",16:"the Sixteenth",
           23:"the Twenty-Third",6:"the Sixth",10:"the Tenth"}


# \u2011 is a NON-BREAKING hyphen, used in this PDF inside verse ranges.
_DASH  = r"[-\u2010\u2011\u2013]"
_VERSE = rf"(?::[\d\s,{_DASH[1:-1]}]*\d[a-z]?)?f{{0,2}}"   # ":16", ":5-6", ":15f", ":19b"
_BARE  = rf"\d+(?:{_DASH}\d+)?{_VERSE}"                     # continuation: "; 17:14"
# editorial notes that may trail a reference inside the same parentheses
_NOTE  = r"(?:\s*[;,]?\s*(?:RSV-CE|rsv-ce|emphasis added|et al\.?|LXX|lxx))*"


def drop_parenthetical_citations(s):
    """Remove parentheses containing ONLY scripture references.

    These are reference apparatus. Read aloud they interrupt the sentence,
    badly so for multi-reference chains. Parentheses carrying real content --
    "(Proclamation)", "(see Gn 4:1-16, the story about Cain and Abel)" --
    are left alone, as are citations that are part of a sentence's grammar.
    """
    full = "|".join(sorted({re.escape(v) for v in BOOKS.values()},
                           key=len, reverse=True))
    one = rf"(?:{_BOOK_RE}|{full})\s*\d+(?:{_DASH}\d+)?{_VERSE}"
    tail = rf"(?:{one}|{_BARE})"
    # \(\s* : the source has "( Jn 17:8" with a kerning space after the paren
    # sep    : refs are chained with ";" "," or "and"
    sep = r"(?:\s*[;,]\s*|\s+and\s+)"
    pat = re.compile(rf"\s*\(\s*(?:see\s+|cf\.?\s+)?{one}"
                     rf"(?:{sep}(?:see\s+|cf\.?\s+|also\s+)?{tail})*{_NOTE}\s*\)")
    s = pat.sub("", s)
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)
    s = re.sub(r"\(\s*\)", "", s)
    return re.sub(r"\s{2,}", " ", s)


def expand_citations(s, verbose=False):
    """(see Jn 3:16-18) -> (see John 3, 16 to 18)   [verbose: 'chapter 3, verses 16 to 18']"""
    def verses(v):
        v = v.replace("–", "-")
        v = re.sub(r"\s*-\s*", " to ", v)
        v = re.sub(r",\s*", " and ", v)
        return v

    def repl(m):
        book, ch, vs = BOOKS[m.group(1)], m.group(2), m.group(3)
        if verbose:
            plural = "verses" if re.search(r"[-,]", m.group(3)) else "verse"
            return f"{book} chapter {ch}, {plural} {verses(vs)}"
        return f"{book} {ch}, {verses(vs)}"

    s = re.sub(rf"\b({_BOOK_RE})\s+(\d+):([\d\s,\-–]*\d)", repl, s)
    # book names already spelled out in the source
    _full = "|".join(sorted({re.escape(v) for v in BOOKS.values()}, key=len, reverse=True))
    s = re.sub(rf"\b({_full})\s+(\d+):([\d\s,\-–]*\d)",
               lambda m: f"{m.group(1)} {m.group(2)}, {verses(m.group(3))}", s)
    # chained refs that omit the book, e.g. "2 Cor 7:9; 8:16"
    s = re.sub(r"(?<=[\s;])(\d+):(\d+)", r"\1, \2", s)
    # chapter-only refs: "Gn 1" inside a citation context
    s = re.sub(rf"\(\s*(see\s+)?({_BOOK_RE})\s+(\d+)\s*\)",
               lambda m: f"({m.group(1) or ''}{BOOKS[m.group(2)]} {m.group(3)})", s)
    return s


def normalize_inline(s):
    s = s.replace("­", "").replace("‑", "-")          # soft / nb hyphen
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = s.replace("ὁ ὠν", "ho On")                              # the one Greek phrase
    s = re.sub(r"\[(\d+)\]", r"", s)                            # stray dual numbering
    s = re.sub(r"\[([^\]]*)\]", r"\1", s)                       # keep editorial glosses
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = re.sub(r"\s*…\s*", " ... ", s)
    s = re.sub(r"\s*\.\s*\.\s*\.\s*", " ... ", s)
    s = re.sub(r"\s*—\s*", ", ", s)                             # em dash -> pause
    s = re.sub(r"(?<=\d)\s*–\s*(?=\d)", " to ", s)              # en dash in ranges
    s = s.replace("–", ", ")
    # named roman numerals
    s = re.sub(r"\b(John Paul|Paul|Pius|Leo|Benedict|Gregory|Urban|Clement|Innocent|Sixtus)\s+([IVXL]{1,6})\b",
               lambda m: f"{m.group(1)} {ORDINAL.get(ROMAN.get(m.group(2),0), m.group(2))}", s)
    s = re.sub(r"\b(Council|Chapter|Part|Section|Vatican)\s+([IVXL]{1,6})\b",
               lambda m: f"{m.group(1)} {ORD.get(ROMAN.get(m.group(2),0), m.group(2))}", s)
    s = re.sub(r'\brsv-ce\b', 'R S V Catholic Edition', s, flags=re.I)
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"\s+\)", ")", s)
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)   # en-dash -> ", " can leave " ,"
    s = re.sub(r"([,;:])\1+", r"\1", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def titlecase_heading(h):
    small = {"of","the","and","in","to","a","an","for","from","with","on","at",
             "by","as","or","nor","but","is","who","that","our"}
    if not h.isupper():
        return h
    out = []
    for i, w in enumerate(h.split()):
        lw = w.lower()
        out.append(w.capitalize() if (i == 0 or lw not in small) else lw)
    return " ".join(out)


_ENUM_RE = re.compile(r"^(?:(?P<rom>[IVXL]{1,6})|(?P<up>[A-Z])|(?P<num>\d{1,2})"
                      r"|(?P<low>[a-z]))(?P<close>[.)])\s+")

def heading_level(h):
    """Outline depth of a heading, from its printed enumerator.

    Returned separately from the spoken text: the label is stripped from
    narration (it is visual navigation), but chapterisation still needs it.
      1 roman "I."   2 letter "A."   3 number "1."   4 lower "a."   5 "1)"
    """
    m = _ENUM_RE.match(h.strip())
    if not m:
        return 0, ""
    g = m.groupdict()
    if g["rom"]:
        lvl = 1
    elif g["up"]:
        lvl = 2
    elif g["num"]:
        lvl = 5 if g["close"] == ")" else 3
    else:
        lvl = 4
    return lvl, m.group(0).strip()


def normalize_heading(h):
    """Read the heading's words, not its outline label."""
    # Strip BEFORE title-casing: title-casing "II." yields "Ii.", which no
    # longer matches the roman-numeral pattern, and it also leaves the next
    # word lowercased once the enumerator is gone.
    h = _ENUM_RE.sub("", h.strip())
    return titlecase_heading(h).strip()


def strip_dual_numbering(s):
    """Ps 41[42]:2 -> Ps 41:2. The bracketed Masoretic number is dropped;
    the Byzantine (Septuagint) number that the book prints first is kept."""
    return re.sub(r"(\d+)\[\d+\]", r"\1", s)


def fold_diacritics(s):
    for a, b in (("\u0119","e"),("\u00e1","a"),("\u00e9","e"),("\u00ed","i"),
                 ("\u00f3","o"),("\u00fa","u"),("\u0144","n"),("\u0142","l"),
                 ("\u017c","z"),("\u017a","z"),("\u0107","c"),("\u015b","s")):
        s = s.replace(a, b).replace(a.upper(), b.upper())
    return s


def normalize_block(b, verbose_citations=False, drop_citations=True,
                    number_paragraphs=True, attributions=None):
    t = fold_diacritics(strip_dual_numbering(b["text"]))
    if drop_citations:
        t = drop_parenthetical_citations(t)
    if b["kind"] in ("HEADING", "PART"):
        t = normalize_heading(t)
    t = expand_citations(t, verbose_citations)
    t = normalize_inline(t)
    # Speak the catechism's paragraph number before the paragraph. In a
    # 13-hour reference work this is how a listener knows where they are.
    if number_paragraphs and b["kind"] == "BODY" and b.get("para"):
        t = f"{b['para']}. {t}"
    # Speak the source after a block quote. Without it a quotation just stops,
    # with no indication of who is being quoted. 64 of the 163 quotes carry no
    # footnote (the Creed, the Anaphora, Scripture) and correctly get nothing.
    if attributions and b["kind"] == "QUOTE" and b.get("refs"):
        src = attributions.get(b["refs"][-1], "")
        if src:
            t = t.rstrip()
            if t and t[-1] not in ".!?\"'":
                t += "."
            src = src[0].upper() + src[1:]     # opens a sentence after the quote
            t = f"{t} {src}."
    return t


if __name__ == "__main__":
    B = json.load(open("work/blocks.json"))
    attribs = {}
    if os.path.exists("work/footnotes.json"):
        import attrib
        notes = {int(k): v for k, v in json.load(open("work/footnotes.json")).items()}
        attribs = {n: attrib.attribution(txt) for n, txt in notes.items()}
    out = []
    seen_part = set()
    for b in B:
        # the page-text repeat of a Part divider ("Part One THE FAITH OF...")
        if b["kind"] == "HEADING" and re.match(r"^Part (One|Two|Three)\b", b["text"], re.I):
            continue
        t = normalize_block(b, attributions=attribs)
        if t:
            lvl, enum = (heading_level(b["text"])
                         if b["kind"] == "HEADING" else (0, ""))
            title = f"{enum} {t}".strip() if enum else t
            out.append(dict(kind=b["kind"], para=b["para"], text=t,
                            level=lvl, title=title))
    json.dump(out, open("work/normalized.json", "w"), indent=1, ensure_ascii=False)
    words = sum(len(x["text"].split()) for x in out)
    print(f"{len(out)} blocks, {words:,} words")
    print("\n--- samples ---")
    for x in out:
        if x["para"] in (32, 224) or x["kind"] == "PART":
            print(f"[{x['kind']} {x['para']}] {x['text'][:280]}\n")
