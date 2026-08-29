# -*- coding: utf-8 -*-
"""Pronunciation overrides for Christ Our Pascha.

Kokoro/misaki phoneme notation (American English):
  ˈ primary stress   ˌ secondary stress   ᵊ syllabic schwa
  A=eɪ  I=aɪ  O=oʊ  W=aʊ  Y=ɔɪ  T=flapped t
  θ=th(thin)  ð=th(this)  ʃ=sh  ʒ=zh  ʧ=ch  ʤ=j  ŋ=ng  ɹ=r  j=y

Only words misaki/espeak gets WRONG are listed; verified-correct defaults
(Anaphora, Dormition, iconostasis, hesychasm, kenosis, Sheptytsky,
Josaphat, prosphora, chrism, myrrh, Ephrem, Cyril, Methodius, Chalcedon,
Cappadocia, Hades, Akathist, Paschal) are deliberately left alone.
"""

# word -> (phonemes, plain-English gloss)
OVERRIDES = {
    # ---- Greek / Byzantine liturgical ----
    "Pascha":            ("pˈɑskɑ",            "PAH-skah"),
    "Chrysostom":        ("kɹˈɪsəstəm",        "KRIS-us-tum"),
    "Chrismation":       ("kɹɪzmˈAʃən",        "kriz-MAY-shun"),
    "Proskomide":        ("pɹˌɑskɑmˈidi",      "pros-ko-MEE-dee"),
    "Theotokos":         ("θˌiəTˈOkɔs",        "thee-o-TOH-kos"),
    "epiklesis":         ("ˌɛpəklˈisɪs",       "eh-puh-KLEE-sis"),
    "epiclesis":         ("ˌɛpəklˈisɪs",       "eh-puh-KLEE-sis"),
    "kerygma":           ("kəɹˈɪɡmə",          "kuh-RIG-muh"),
    "catechumen":        ("kˌæTəkjˈumən",      "kat-uh-KYOO-men"),
    "catechumenate":     ("kˌæTəkjˈumənɪt",    "kat-uh-KYOO-muh-nit"),
    "troparion":         ("tɹoʊpˈɑɹiɑn",       "tro-PAH-ree-on"),
    "troparia":          ("tɹoʊpˈɑɹiə",        "tro-PAH-ree-uh"),
    "Emmanuel":          ("ɪmˈænjuˌɛl",        "ih-MAN-yoo-el"),
    "kontakion":         ("kɑntˈɑkiɑn",        "kon-TAH-kee-on"),
    "prokeimenon":       ("pɹəkˈimənɑn",       "pro-KEE-me-non"),
    "antimension":       ("ˌænTɪmˈɛnsiɑn",     "an-ti-MEN-see-on"),
    "theosis":           ("θiˈOsɪs",           "thee-OH-sis"),
    "Protoevangelium":   ("pɹˌOToˌivænʤˈɛliəm","proh-toh-ee-van-JEL-ee-um"),
    "Trisagion":         ("tɹɪsˈɑɡiɑn",        "tri-SAH-gee-on"),
    "Philokalia":        ("fˌɪloʊkɑlˈiə",      "fee-lo-kah-LEE-uh"),
    "Triodion":          ("tɹiˈOdiɑn",         "tree-OH-dee-on"),
    "Menaion":           ("mɪnˈAɑn",           "me-NAY-on"),
    "Typikon":           ("tˈipɪkɔn",          "TEE-pee-kon"),
    "Moleben":           ("mˈɔlɛbɛn",          "MOH-leh-ben"),
    "Antidoron":         ("ænTˈɪdəɹɑn",        "an-TID-oh-ron"),
    "Panakhyda":         ("pɑnɑkˈidɑ",         "pah-nah-KHEE-dah"),
    "Octoechos":         ("ˌɑktoʊˈEkɔs",       "ok-toh-EH-kos"),
    "Stichera":          ("stˈɪkəɹə",          "STIH-kheh-ruh"),
    "Pantocrator":       ("pænTˈɑkɹəTɔɹ",      "pan-TOK-ruh-tor"),
    "Hodegetria":        ("hˌOdɪɡˈEtɹiə",      "ho-de-GEH-tree-uh"),
    "Oranta":            ("oʊɹˈɑnTə",          "oh-RAHN-tuh"),
    "epitrachelion":     ("ˌɛpɪTɹəkˈiliɑn",    "eh-pee-tra-KHEE-lee-on"),
    "phelonion":         ("fɪlˈOniɑn",         "feh-LOH-nee-on"),
    "Cherubim":          ("ˈʧɛɹəbˌɪm",         "CHER-uh-bim"),
    "Seraphim":          ("ˈsɛɹəfˌɪm",         "SER-uh-fim"),

    # ---- Ukrainian / Slavonic ----
    "Kyiv":              ("kˈijɪv",            "KEE-yiv"),
    "Kyivan":            ("kˈijɪvən",          "KEE-yiv-un"),
    "Andrey":            ("ɑndɹˈA",            "ahn-DRAY"),
    "Sviatoslav":        ("svjˌɑtəslˈɑv",      "svyah-toh-SLAHV"),
    "Volodymyr":         ("vˌɔloʊdˈimɪɹ",      "vo-lo-DEE-mir"),
    "Pochaiv":           ("pəʧˈɑjɪv",          "po-CHAH-yiv"),
    "Slipyj":            ("slˈipij",           "SLEE-piy"),
    "Zarvanytsia":       ("zˌɑɹvɑnˈitsiə",     "zar-vah-NIT-sya"),
    "Rus":               ("ɹˈus",              "roos"),
    "Metropolitanate":   ("mˌɛtɹəpˈɑlətənˌAt", "met-ro-POL-i-tuh-nayt"),
    "Ilarion":           ("ˌilɑɹˈiɑn",         "ee-lah-REE-on"),
    "Lviv":              ("ləvˈiv",            "luh-VEEV"),
    "Halych":            ("hˈɑlɪʧ",            "HAH-lich"),

    # ---- Fathers, councils, saints ----
    "Irenaeus":          ("ˌIɹɪnˈiəs",         "eye-ruh-NEE-us"),
    "Athanasius":        ("ˌæθənˈAʃəs",        "ath-uh-NAY-shus"),
    "Symeon":            ("sˈɪmiɑn",           "SIM-ee-on"),
    "Maximus":           ("mˈæksəməs",         "MAK-si-mus"),
    "Constantinopolitan":("kˌɑnstænTˌɪnəpˈɑlətᵊn", "kon-stan-ti-no-POL-i-tun"),
    "Nicene":            ("nˈIsin",            "NYE-seen"),
    "Nazianzus":         ("nˌæziˈænzəs",       "naz-ee-AN-zus"),
    "Czestochowa":       ("ʧˌɛnstəkˈOvə",      "chen-sto-KHO-vah"),
    "apatheia":          ("əpˈæθiə",           "uh-PATH-ee-uh"),
    "Vyshhorod":         ("vˈɪʃhəɹɔd",         "VISH-ho-rod"),
    "Hoshiv":            ("hˈɔʃɪv",            "HO-shiv"),
    "Kholm":             ("kˈOlm",             "KHOLM"),
    "Univ":              ("ˈunɪv",             "OO-niv"),
    "Belz":              ("bˈɛlz",             "BELZ"),
    "Niceno":            ("nIsˈEnoʊ",          "nye-SEH-no"),
    "Josyf":             ("jˈOsɪf",            "YO-sif"),
    "Sluzhebnyk":        ("sluʒˈɛbnɪk",        "sloo-ZHEB-nik"),
}


def case_variants(word, phon):
    """misaki looks words up case-sensitively for short proper nouns, so
    register every casing that can occur in running text."""
    out = {word: phon, word.lower(): phon, word.capitalize(): phon}
    out[word.upper()] = phon
    return out


def install(pipeline):
    """Inject overrides into a KPipeline's misaki lexicon."""
    golds = pipeline.g2p.lexicon.golds
    n = 0
    for w, (phon, _gloss) in OVERRIDES.items():
        for k, v in case_variants(w, phon).items():
            golds[k] = v
        # plural / possessive forms of nouns
        for suf, add in ((("s",), "z"), (("'s", "’s"), "z")):
            for s in suf:
                golds[w + s] = phon + add
                golds[w.lower() + s] = phon + add
        n += 1
    return n


def applicable(text):
    """Override entries whose word actually occurs in `text`.

    Used to build a cache key: editing one entry invalidates only the units
    that contain that word, not the whole book.
    """
    import re
    low = text.lower()
    hits = []
    for w, (phon, _g) in OVERRIDES.items():
        wl = w.lower()
        if wl in low and re.search(r"\b" + re.escape(wl), low):
            hits.append(f"{wl}={phon}")
    return ";".join(sorted(hits))
