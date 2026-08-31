# -*- coding: utf-8 -*-
"""Generate a podcast RSS feed for the tracks.

Podcast apps are the natural client for long chaptered audio: they handle
offline download, resume position, and playback speed without any of it
being built here.
"""
import json, html, argparse, os
from email.utils import format_datetime
from datetime import datetime, timezone, timedelta

ITEM = """  <item>
   <title>{title}</title>
   <itunes:episode>{num}</itunes:episode>
   <itunes:title>{title}</itunes:title>
   <guid isPermaLink="false">{base}/audio/{file}</guid>
   <pubDate>{pub}</pubDate>
   <enclosure url="{base}/audio/{file}" length="{bytes}" type="audio/mpeg"/>
   <itunes:duration>{dur}</itunes:duration>
   <link>{base}/index.html#t={start}</link>
   <description>{desc}</description>
  </item>"""

def hms(sec):
    sec = int(sec)
    return f"{sec//3600:d}:{sec%3600//60:02d}:{sec%60:02d}"

def build(base, out="docs/feed.xml", start_date="2026-01-01"):
    tracks = json.load(open("work/tracks.json"))
    base = base.rstrip("/")
    d0 = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    items = []
    for t in tracks:
        # one nominal day apart, in order, so apps sort correctly
        pub = format_datetime(d0 + timedelta(days=t["index"]))
        desc = (f"Section of Christ Our Pascha, the Catechism of the Ukrainian "
                f"Catholic Church. Synthetic narration; see the About page.")
        items.append(ITEM.format(
            title=html.escape(t["title"]), num=t["index"] + 1, base=base,
            file=t["file"], bytes=t["bytes"], pub=pub,
            dur=hms(t["seconds"]), start=int(t["start"]),
            desc=html.escape(desc)))
    total = sum(t["seconds"] for t in tracks)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom">
 <channel>
  <title>Christ Our Pascha — Catechism of the Ukrainian Catholic Church</title>
  <link>{base}/</link>
  <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
  <language>en-us</language>
  <itunes:author>Synod of the Ukrainian Greek-Catholic Church</itunes:author>
  <copyright>© 2016 Synod of the Ukrainian Greek-Catholic Church</copyright>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>serial</itunes:type>
  <itunes:category text="Religion &amp; Spirituality"><itunes:category text="Christianity"/></itunes:category>
  <itunes:image href="{base}/cover.jpg"/>
  <image><url>{base}/cover.jpg</url><title>Christ Our Pascha</title><link>{base}/</link></image>
  <description>An audio edition of Christ Our Pascha, the Catechism of the
  Ukrainian Catholic Church (Kyiv-Edmonton, 2016), in {len(tracks)} parts
  totalling {total/3600:.1f} hours. The narration is synthetic speech, not a
  human reader; see the About page for what that means and what was omitted.
  Published by permission of the rights holders.</description>
  <itunes:summary>Audio edition of the UGCC catechism Christ Our Pascha.
  Synthetic narration. {len(tracks)} parts, {total/3600:.1f} hours.</itunes:summary>
{chr(10).join(items)}
 </channel>
</rss>
"""
    open(out, "w", encoding="utf-8").write(xml)
    print(f"  {out}  ({len(tracks)} items, {os.path.getsize(out)/1024:.0f} KB)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True,
                    help="public site URL, e.g. https://user.github.io/repo")
    a = ap.parse_args()
    build(a.base)
