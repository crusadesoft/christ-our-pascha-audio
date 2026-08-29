# -*- coding: utf-8 -*-
"""Turn a footnote into a spoken attribution.

  "John of Damascus, An Exposition of the Orthodox Faith, 4, 13: PG 94, 1148."
    -> "John of Damascus in An Exposition of the Orthodox Faith"

Scholarly apparatus (Migne PG/PL columns, section numbers, dates) is dropped:
it is unlistenable and the reader has the full footnote in the transcript.
"""
import re

# sources with no personal author -- spoken as "the X"
WORKS = {
    "Catechism of the Catholic Church", "Floral Triodion", "Lenten Triodion",
    "Octoechos", "Trebnyk", "Liturgicon", "Arhieraticon", "Menaion",
    "Horologion", "Typikon", "Euchologion", "Sluzhebnyk", "Apostol",
    "Code of Canons of the Eastern Churches", "Code of Canon Law",
    "Divine Liturgy", "Great Canon", "Psalter",
}
# these open a corporate author rather than a person
CORPORATE = ("Vatican Council", "Council of", "Synod of", "Holy Synod",
             "Congregation for", "Pontifical", "Second Vatican")

def _strip_apparatus(t):
    t = re.sub(r"^\s*(?:See|Cf\.?|see|cf\.?)\s+", "", t)
    t = re.sub(r"\s*:\s*P[GL]\s.*$", "", t)          # ": PG 94, 1148."
    t = re.sub(r"\s*\([^)]*\d{3,4}[^)]*\)\s*\.?$", "", t)   # trailing (date)
    t = re.sub(r",\s*emphasis added\.?$", "", t, flags=re.I)
    t = re.sub(r"\.\s*English translation.*$", "", t, flags=re.I)
    return t.strip().rstrip(".").strip()

def _prefer_gloss(t):
    """Cyrillic titles carry an English gloss in brackets; speak the gloss."""
    if re.search(r"[Ѐ-ӿ]", t):
        m = re.search(r"\[([^\]]+)\]", t)
        if m:
            t = re.sub(r"[Ѐ-ӿ][^,\[]*\[[^\]]+\]", m.group(1), t)
    return re.sub(r"\s*\[([^\]]+)\]", r", \1", t)

def _is_ref(part):
    """A part that is only numbering, not a title."""
    p = part.strip().rstrip(".")
    return bool(re.fullmatch(r"[\dIVXLivxl]+(?:[-,]\s*[\dIVXLivxl]+)*", p)) or not p

_ROMAN = {"I":"One","II":"Two","III":"Three","IV":"Four","V":"Five","VI":"Six",
          "VII":"Seven","VIII":"Eight","IX":"Nine","X":"Ten","XI":"Eleven",
          "XII":"Twelve","XIII":"Thirteen","XIV":"Fourteen","XV":"Fifteen",
          "XVI":"Sixteen","XX":"Twenty"}

def _spell_romans(t):
    """"Session V" is voiced as the letter "vee" unless spelled out."""
    return re.sub(r"(?<![A-Za-z])([IVXL]{1,5})(?![A-Za-z])",
                  lambda m: _ROMAN.get(m.group(1), m.group(1)), t)


def attribution(note):
    if not note:
        return ""
    t = _prefer_gloss(_strip_apparatus(note))
    if not t:
        return ""
    parts = [p.strip() for p in t.split(",")]
    head = parts[0]

    for w in WORKS:                                  # author-less source
        if head.lower().startswith(w.lower()):
            return _spell_romans("the " + head)
    if head.startswith(CORPORATE):
        rest = [p for p in parts[1:] if not _is_ref(p)]
        return _spell_romans(head + (", " + rest[0] if rest else ""))

    # "Ilarion, Metropolitan of Kyiv, Confession of Faith" -- author spans two parts
    ai = 1
    if len(parts) > 2 and re.match(r"^(?:Metropolitan|Patriarch|Bishop|Archbishop|"
                                   r"Pope|Saint|St\.?|Blessed|Father)\b", parts[1]):
        head = head + ", " + parts[1]
        ai = 2
    work = next((p for p in parts[ai:] if not _is_ref(p)), "")
    work = re.sub(r"\b(Homily|Oration|Sermon|Letter|Canon)(\d)", r"\1 \2", work)
    if not work:
        return _spell_romans(head)
    return _spell_romans(f"{head} in {work}")
