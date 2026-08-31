# -*- coding: utf-8 -*-
"""Inline Lucide icons.

Pulled from the `lucide-static` npm package at build time and inlined, so the
site has no runtime dependency and no external requests. `currentColor` means
they inherit text colour.
"""
import os, re, json

SRC = "vendor/node_modules/lucide-static/icons"
NEEDED = ["menu", "x", "search", "link-2", "play", "pause", "skip-back",
          "skip-forward", "rotate-ccw", "rotate-cw", "gauge", "book-open",
          "info", "headphones", "rss", "download", "audio-lines",
          "chevron-right", "list-music"]

def load():
    out = {}
    for n in NEEDED:
        p = f"{SRC}/{n}.svg"
        if not os.path.exists(p):
            continue
        svg = open(p).read()
        svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)      # licence comment
        svg = re.sub(r"\s+", " ", svg).strip()                # collapse first
        svg = re.sub(r'\s(width|height)="24"', "", svg)       # size from CSS
        # the package ships class="lucide lucide-NAME"; replace it rather than
        # adding a second class attribute (browsers keep only the first)
        if re.search(r'<svg[^>]*\sclass="', svg):
            svg = re.sub(r'(<svg[^>]*?)\sclass="[^"]*"', r'\1 class="ic"', svg, count=1)
        else:
            svg = svg.replace("<svg", '<svg class="ic"', 1)
        out[n] = svg
    return out


if __name__ == "__main__":
    ic = load()
    print(f"{len(ic)} icons, {sum(len(v) for v in ic.values())/1024:.1f} KB total")
    print(" ", list(ic)[:8], "...")
