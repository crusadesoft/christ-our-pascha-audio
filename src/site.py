# -*- coding: utf-8 -*-
"""Generate the static review site (GitHub Pages) from the built timeline."""
import json, html, os, argparse, base64, pathlib

OUT = "docs"
M4B_URL_DEFAULT = ""   # set to a GitHub Release asset URL once published

def load():
    """Playback tracks and navigation marks are separate: 78 listenable tracks,
    232 places to jump to."""
    T = json.load(open("work/timeline.json"))
    tracks = json.load(open(f"{OUT}/tracks.json"))
    tr = [{"i": t["index"], "t": t["title"], "f": t["file"],
           "s": round(t["start"], 3), "d": round(t["seconds"], 3)} for t in tracks]
    chapters = [{"i": c["index"], "t": c["title"], "s": round(c["start"], 3)}
                for c in T["chapters"]]
    cues = [[round(c["start"], 2), c["chapter"], c["para"] or 0,
             c["kind"][0], c["text"]] for c in T["cues"]]
    return T, tr, chapters, cues


NAV = """<div class="nav"><span class="brand">Christ Our Pascha</span>
<a href="index.html"{a0}>Listen</a><a href="text.html"{a1}>Text</a>
<a href="about.html"{a2}>About</a></div>"""

def nav(active):
    return NAV.format(**{f"a{i}": ' class="on"' if i == active else ""
                         for i in range(3)})

def write(path, body):
    pathlib.Path(f"{OUT}/{path}").write_text(body, encoding="utf-8")
    print(f"  {OUT}/{path}  ({os.path.getsize(f'{OUT}/{path}')/1024:.0f} KB)")


# ---------------------------------------------------------------- reader ----
READER = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0d10">
<title>Christ Our Pascha — Listen</title>
<link rel="stylesheet" href="style.css">
<style>
body{height:100dvh;overflow:hidden;display:grid;
 grid-template-rows:auto 1fr auto;grid-template-columns:310px 1fr;
 grid-template-areas:"nav nav" "side main" "player player"}
.nav{grid-area:nav}
#scrim{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:8}
#side{grid-area:side;border-right:1px solid #232830;display:flex;flex-direction:column;
 background:#101216;z-index:9;min-height:0}
#side h1{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:#7d8794;
 margin:0;padding:13px 16px;border-bottom:1px solid #232830;display:flex;
 justify-content:space-between;align-items:center}
#closeCh{display:none;background:none;border:0;color:#98a2af;font-size:22px}
#chaps{overflow-y:auto;flex:1;-webkit-overflow-scrolling:touch}
.ch{padding:11px 16px;cursor:pointer;font-size:14px;color:#98a2af;
 border-left:3px solid transparent;min-height:44px;display:flex;align-items:center}
.ch:active{background:#1b2029}
.ch.on{background:#1b2029;color:#8ab4f8;border-left-color:#8ab4f8}
#main{grid-area:main;display:flex;flex-direction:column;min-width:0;min-height:0}
#bar{padding:8px 14px;border-bottom:1px solid #232830;background:#101216;
 display:flex;gap:8px;align-items:center}
#burger{display:none;background:#1b1f26;border:1px solid #2d323b;color:#dfe3e8;
 border-radius:8px;font-size:17px;width:42px;height:38px;flex:none}
#q{flex:1;min-width:100px;background:#1b1f26;border:1px solid #2d323b;color:#dfe3e8;
 padding:9px 11px;border-radius:8px;font-size:16px}
#link{background:#1b1f26;border:1px solid #2d323b;color:#dfe3e8;border-radius:8px;
 padding:9px 11px;font-size:12px;cursor:pointer;flex:none}
#txt{overflow-y:auto;flex:1;padding:18px 22px}
.p{margin:0 0 3px;padding:9px 11px;border-radius:7px;cursor:pointer;border-left:3px solid transparent}
.p:active{background:#1b1f26}
.p.on{background:#243044;border-left-color:#8ab4f8;color:#fff}
.p.H{color:#e8c07d;font-weight:600;margin-top:22px;font-size:17px}
.p.P{color:#7fd1b9;font-weight:700;font-size:19px;margin-top:28px}
.p.Q{color:#b8c0cc;font-style:italic;padding-left:22px;border-left:3px solid #333a45}
.num{color:#5a6472;font-size:12px;margin-right:8px;font-variant-numeric:tabular-nums}
.hit{background:#4a3f1a}
#player{grid-area:player;position:relative;background:#0b0d10;border-top:1px solid #232830;
 display:grid;grid-template-columns:1fr minmax(260px,620px) 1fr;align-items:center;
 gap:12px;padding:10px 16px;padding-bottom:max(10px,env(safe-area-inset-bottom))}
#np{min-width:0;display:flex;align-items:center;gap:11px}
#art{height:50px;width:auto;border-radius:3px;flex:none;background:#1b1f26;
 box-shadow:0 2px 8px rgba(0,0,0,.55)}
#npText{min-width:0}
#npTitle{font-size:13px;font-weight:600;color:#e8ecf1;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis}
#npSub{font-size:11px;color:#7d8794;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#mid{display:flex;flex-direction:column;gap:5px;min-width:0}
#ctrls{display:flex;justify-content:center;align-items:center;gap:6px}
.tb{background:none;border:0;color:#c3cad3;cursor:pointer;border-radius:50%;
 width:38px;height:38px;font-size:13px;display:flex;align-items:center;justify-content:center}
.tb:hover{color:#fff;background:#1a1f27}
#play{background:#e8ecf1;color:#0b0d10;width:42px;height:42px;font-size:16px}
#seekRow{display:flex;align-items:center;gap:9px}
.tm{font-size:11px;color:#8b95a2;font-variant-numeric:tabular-nums;min-width:56px;flex:none}
.tm.r{text-align:right}
#seek{flex:1;-webkit-appearance:none;appearance:none;height:14px;background:none;cursor:pointer}
#seek::-webkit-slider-runnable-track{height:4px;border-radius:2px;
 background:linear-gradient(#8ab4f8,#8ab4f8) 0/var(--pct,0%) 100% no-repeat,#333a45}
#seek::-webkit-slider-thumb{-webkit-appearance:none;width:12px;height:12px;border-radius:50%;
 background:#fff;margin-top:-4px;opacity:0}
#seek:hover::-webkit-slider-thumb,#seek:active::-webkit-slider-thumb{opacity:1}
#right{display:flex;justify-content:flex-end;align-items:center;gap:6px}
#spd{background:#1b1f26;border:1px solid #2d323b;color:#dfe3e8;border-radius:14px;
 padding:5px 11px;font-size:12px;cursor:pointer}
#toast{position:fixed;left:50%;bottom:110px;transform:translateX(-50%);background:#243044;
 color:#fff;padding:9px 16px;border-radius:20px;font-size:13px;opacity:0;
 transition:opacity .2s;pointer-events:none;z-index:20}
#toast.show{opacity:1}
@media (max-width:820px){
 body{grid-template-columns:1fr;grid-template-areas:"nav" "main" "player"}
 #burger,#closeCh{display:block}
 #side{position:fixed;top:0;bottom:0;left:0;width:min(84vw,320px);
  transform:translateX(-102%);transition:transform .22s ease;box-shadow:0 0 28px #000}
 body.nav #side{transform:none}
 body.nav #scrim{display:block}
 #txt{padding:14px 15px;font-size:17px;line-height:1.7}
 #player{grid-template-columns:1fr;gap:7px;padding:9px 13px}
 #np{justify-content:center;gap:9px}
 #art{height:40px}
 #right{position:absolute;right:12px;top:8px;z-index:2}
 .tb{width:44px;height:44px}#play{width:50px;height:50px;font-size:18px}
}
</style></head><body>
__NAV__
<div id="scrim"></div>
<div id="side"><h1>Chapters<button id="closeCh">&times;</button></h1><div id="chaps"></div></div>
<div id="main">
 <div id="bar">
   <button id="burger" aria-label="Chapters">&#9776;</button>
   <input type="search" id="q" placeholder="Search the text...">
   <button id="link" title="Copy a link to this moment">Copy link</button>
 </div>
 <div id="txt"><p style="color:#7d8794">Loading…</p></div>
</div>
<div id="player">
  <div id="np"><img id="art" src="cover.jpg" alt="">
    <div id="npText"><div id="npTitle">&nbsp;</div><div id="npSub">Christ Our Pascha</div></div></div>
  <div id="mid">
    <div id="ctrls">
      <button class="tb" id="prev" title="Previous chapter">&#9198;</button>
      <button class="tb" id="b15" title="Back 15 seconds">&#8630;15</button>
      <button class="tb" id="play" title="Play">&#9654;</button>
      <button class="tb" id="f15" title="Forward 15 seconds">15&#8631;</button>
      <button class="tb" id="next" title="Next chapter">&#9197;</button>
    </div>
    <div id="seekRow"><span class="tm" id="cur">0:00:00</span>
      <input type="range" id="seek" min="0" max="1000" value="0" aria-label="Seek">
      <span class="tm r" id="tot">0:00:00</span></div>
  </div>
  <div id="right"><button id="spd">1&times;</button></div>
</div>
<div id="toast"></div>
<audio id="a" preload="metadata"></audio>
<script>
const $=i=>document.getElementById(i), A=$('a'), T=$('txt');
let D=null, cur=-1, els=[], trk=-1, seeking=false, TOTAL=0;
const fmt=s=>{s=Math.max(0,s|0);return (s/3600|0)+':'+String(s%3600/60|0).padStart(2,'0')+':'+String(s%60).padStart(2,'0')};
const esc=s=>s.replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
function toast(m){const t=$('toast');t.textContent=m;t.classList.add('show');
 clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),1600)}

fetch('data.json').then(r=>r.json()).then(d=>{D=d;init()})
 .catch(()=>{T.innerHTML='<p style="color:#e88">Could not load data.json.</p>'});

function init(){
 TOTAL=D.tr.reduce((a,t)=>a+t.d,0);
 $('tot').textContent=fmt(TOTAL);
 T.innerHTML=''; let lastPara=null;
 D.c.forEach((c,i)=>{const d=document.createElement('div');
  d.className='p '+c[3];
  const showNum=c[2]&&c[2]!==lastPara; if(c[2])lastPara=c[2];
  let tx=esc(c[4]); if(showNum)tx=tx.replace(new RegExp('^'+c[2]+'\\\\.\\\\s*'),'');
  d.innerHTML=(showNum?'<span class="num">'+c[2]+'</span>':'')+tx;
  d.onclick=()=>seekGlobal(c[0],true); T.appendChild(d); els.push(d)});
 const CH=$('chaps');
 D.ch.forEach(c=>{const d=document.createElement('div');d.className='ch';d.dataset.c=c.i;
  d.textContent=c.t; d.onclick=()=>{seekGlobal(c.s,true);document.body.classList.remove('nav')};
  CH.appendChild(d)});
 applyHash() || loadTrack(0,0,false);
}
function trackAt(t){let f=D.tr[0];for(const x of D.tr){if(x.s<=t)f=x;else break}return f}
function chapterAt(t){let f=D.ch[0];for(const c of D.ch){if(c.s<=t)f=c;else break}return f}
function loadTrack(i,off,play){
 if(i!==trk){trk=i;A.src='audio/'+D.tr[i].f;}
 const go=()=>{A.currentTime=Math.max(0,off); if(play)A.play()};
 if(A.readyState>=1)go(); else A.addEventListener('loadedmetadata',go,{once:true});
}
function seekGlobal(t,play){const x=trackAt(t);
 loadTrack(D.tr.indexOf(x), t-x.s, play!==false)}
function globalTime(){return trk<0?0:D.tr[trk].s+(A.currentTime||0)}
A.addEventListener('ended',()=>{if(trk<D.tr.length-1)loadTrack(trk+1,0,true)});
$('play').onclick=()=>A.paused?A.play():A.pause();
A.addEventListener('play',()=>$('play').innerHTML='&#10073;&#10073;');
A.addEventListener('pause',()=>$('play').innerHTML='&#9654;');
const jump=d=>seekGlobal(Math.max(0,Math.min(TOTAL-1,globalTime()+d)),!A.paused);
$('b15').onclick=()=>jump(-15); $('f15').onclick=()=>jump(15);
$('prev').onclick=()=>{const t=globalTime(),c=chapterAt(t);
 const i=D.ch.indexOf(c); seekGlobal((t-c.s>3||i===0)?c.s:D.ch[i-1].s,!A.paused)};
$('next').onclick=()=>{const i=D.ch.indexOf(chapterAt(globalTime()));
 if(i<D.ch.length-1)seekGlobal(D.ch[i+1].s,!A.paused)};
const RS=[1,1.1,1.25,1.5,1.75,2,.85];let ri=0;
$('spd').onclick=()=>{ri=(ri+1)%RS.length;A.playbackRate=RS[ri];$('spd').innerHTML=RS[ri]+'&times;'};
$('seek').addEventListener('input',e=>{seeking=true;
 $('cur').textContent=fmt(e.target.value/1000*TOTAL);
 e.target.style.setProperty('--pct',(e.target.value/10)+'%')});
$('seek').addEventListener('change',e=>{seeking=false;seekGlobal(e.target.value/1000*TOTAL,!A.paused)});
let hashT=0;
function sync(){
 const t=globalTime();
 if(!seeking){const v=t/TOTAL*1000;$('seek').value=v;$('seek').style.setProperty('--pct',(v/10)+'%')}
 $('cur').textContent=fmt(t);
 let lo=0,hi=D.c.length-1,f=-1;
 while(lo<=hi){const m=(lo+hi)>>1;if(D.c[m][0]<=t){f=m;lo=m+1}else hi=m-1}
 if(f!==cur&&f>=0){if(cur>=0)els[cur].classList.remove('on');
  els[f].classList.add('on');cur=f;
  const box=T.getBoundingClientRect(),er=els[f].getBoundingClientRect();
  const tgt=T.scrollTop+(er.top-box.top)-box.height/2+er.height/2;
  T.scrollTo({top:tgt,behavior:Math.abs(tgt-T.scrollTop)>1800?'auto':'smooth'});
  const ci=D.c[f][1];
  [...$('chaps').children].forEach(e=>e.classList.toggle('on',+e.dataset.c===ci));
  const ch=D.ch.find(x=>x.i===ci);
  $('npTitle').textContent=ch?ch.t:'';
  $('npSub').textContent='Christ Our Pascha'+(D.c[f][2]?'  \\u00b7  paragraph '+D.c[f][2]:'');}
 if(!A.paused && Date.now()-hashT>3000){hashT=Date.now();
  history.replaceState(null,'','#t='+Math.round(t))}
}
A.addEventListener('timeupdate',sync);
// a seek while paused fires no timeupdate, so a deep link would land in the
// right place but leave the previous paragraph highlighted
A.addEventListener('seeked',sync);
A.addEventListener('loadeddata',sync);
$('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();let n=0;
 els.forEach((el,i)=>{const hit=v&&D.c[i][4].toLowerCase().includes(v);
  el.classList.toggle('hit',!!hit);if(hit)n++});
 if(v){const k=els.findIndex(el=>el.classList.contains('hit'));if(k>=0)els[k].scrollIntoView({block:'center'})}
 $('npSub').textContent=v?n+' matches':'Christ Our Pascha'});
$('link').onclick=()=>{const u=location.origin+location.pathname+'#t='+Math.round(globalTime());
 navigator.clipboard.writeText(u).then(()=>toast('Link copied — opens at this moment'),
  ()=>toast(u))};
function applyHash(){const h=location.hash;
 let m=h.match(/[#&]t=(\\d+(?:\\.\\d+)?)/); if(m){seekGlobal(parseFloat(m[1]),false);return true}
 m=h.match(/[#&]p=(\\d+)/);
 // nudge past the boundary: seeking to a cue's exact start can snap to an
 // earlier audio frame, leaving the PREVIOUS paragraph current
 if(m){const p=+m[1];const c=D.c.find(x=>x[2]===p); if(c){seekGlobal(c[0]+0.25,false);return true}}
 return false}
addEventListener('hashchange',applyHash);
const nav=on=>document.body.classList.toggle('nav',on);
$('burger').onclick=()=>nav(!document.body.classList.contains('nav'));
$('closeCh').onclick=()=>nav(false); $('scrim').onclick=()=>nav(false);
addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;
 if(e.code==='Space'){e.preventDefault();A.paused?A.play():A.pause()}
 if(e.key==='ArrowLeft')jump(-15);if(e.key==='ArrowRight')jump(15)});
if('mediaSession' in navigator){
 navigator.mediaSession.setActionHandler('seekbackward',()=>jump(-15));
 navigator.mediaSession.setActionHandler('seekforward',()=>jump(15));
 navigator.mediaSession.setActionHandler('previoustrack',()=>$('prev').click());
 navigator.mediaSession.setActionHandler('nexttrack',()=>$('next').click());}
</script></body></html>"""


# ------------------------------------------------------------- about/text ----
ABOUT = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Christ Our Pascha — About this recording</title>
<link rel="stylesheet" href="style.css"></head><body>
__NAV__
<div class="wrap">
<h1>About this recording</h1>
<p class="lede">An audio edition of <em>Christ Our Pascha: Catechism of the
Ukrainian Catholic Church</em>, prepared for review.</p>

<div class="note"><strong>This narration is synthetic.</strong> Every word is
spoken by a text-to-speech model, not by a human reader. No claim is made that
it carries the authority, care, or interpretive judgement of a human narrator,
and it has not been reviewed word-by-word against the printed text by ear.
It is offered as a working draft for evaluation.</div>

<h2>Source text</h2>
<table>
<tr><th>Work</th><td>Catechism of the Ukrainian Catholic Church: <em>Christ – Our Pascha</em></td></tr>
<tr><th>Edition</th><td>English, Kyiv–Edmonton 2016; online corrected printing, Nov 2017</td></tr>
<tr><th>Copyright</th><td>© 2016 Synod of the Ukrainian Greek-Catholic Church<br>
© 2016 Commission for the Catechism of the UGCC</td></tr>
<tr><th>ISBN</th><td>978–0–9809309–2–4</td></tr>
<tr><th>Cover icon</th><td>The Descent into Hades, Volodymyr Sviderski,
St. Josaphat Ukrainian Catholic Cathedral, Edmonton</td></tr>
</table>
<p style="font-size:14px;color:#98a2af">This recording is derived from a
copyrighted work and is published only with the permission of the rights
holders. It is not for sale.</p>

<h2>Voices</h2>
<table>
<tr><th>Body text</th><td><code>am_michael</code> — Kokoro-82M</td></tr>
<tr><th>Block quotations</th><td><code>bm_lewis</code> — Kokoro-82M, so quoted
sources are audibly distinct from the catechism's own voice</td></tr>
</table>

<h2>Editorial decisions</h2>
<table>
<tr><th>Paragraph numbers</th><td><strong>Spoken.</strong> All 1001 are read
aloud before their paragraph, so a listener can track position and find a
passage again.</td></tr>
<tr><th>Heading labels</th><td><strong>Not spoken.</strong> "A.", "1.", "a."
are visual outline aids; they remain in the chapter list for navigation.</td></tr>
<tr><th>Quotation sources</th><td><strong>Spoken</strong> after the quote, in
the quotation voice — e.g. <em>"Irenaeus of Lyons in Against Heresies."</em>
Scholarly apparatus (Migne PG/PL columns, section numbers) is omitted. 64 of
163 block quotes carry no footnote (the Creed, the Anaphora, Scripture) and
receive no attribution.</td></tr>
<tr><th>Scripture citations</th><td>Parenthetical references
<em>(see Jn 3:16)</em> are <strong>omitted</strong> — read aloud they interrupt
the sentence, and chains of four or five are unlistenable. Citations that are
part of a sentence's grammar are kept. The full references remain in the
transcript.</td></tr>
<tr><th>Footnotes</th><td>Omitted from the audio except where they supply a
quotation's source.</td></tr>
<tr><th>Indexes</th><td>The Index of Citations and Subject Index are omitted.</td></tr>
</table>

<h2>How it was verified</h2>
<p>Two automated checks guard the recording. The first compares the extracted
text against the PDF itself, independently of the extraction, and requires
better than 99.9% word coverage with no missing run of eight words or more.
The second transcribes every chapter back to text and diffs it against the
script, to catch skipped or repeated audio.</p>
<table>
<tr><th>Text coverage</th><td>125,476 of 125,476 words — 0.03% unmatched,
no missing runs</td></tr>
<tr><th>Paragraphs recovered</th><td>1001 of 1001</td></tr>
<tr><th>Transcription similarity</th><td>0.978 mean across all chapters</td></tr>
<tr><th>Loudness</th><td>__LUFS__ LUFS integrated, __PEAK__ dBFS true peak</td></tr>
<tr><th>Duration</th><td>__DUR__ across __NCH__ chapters</td></tr>
</table>
<p style="font-size:14px;color:#98a2af">Neither check can tell whether a word
is <em>pronounced</em> correctly — only whether it is present. Pronunciation of
proper names was hand-tuned for __NLEX__ terms (Pascha, Proskomide, Theotokos,
Sheptytsky, and others); errors that remain are the most likely defect.</p>

<h2>Reporting a problem</h2>
<p>On the <a href="index.html">Listen</a> page, press <strong>Copy link</strong>
at any moment to get a URL that opens at that exact point. That is the most
useful way to report a mispronunciation or a passage that reads wrongly.</p>
__DOWNLOAD__
</div></body></html>"""

TEXT = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Christ Our Pascha — Narration text</title>
<link rel="stylesheet" href="style.css">
<style>
.wrap{max-width:820px}
.h{color:#e8c07d;font-weight:600;font-size:18px;margin:26px 0 8px}
.pt{color:#7fd1b9;font-weight:700;font-size:21px;margin:34px 0 10px}
.q{color:#b8c0cc;font-style:italic;margin:0 0 10px;padding-left:20px;
 border-left:3px solid #333a45}
.b{margin:0 0 11px}
.n{color:#5a6472;font-size:12px;margin-right:8px;font-variant-numeric:tabular-nums}
@media print{body{background:#fff;color:#000}.nav{display:none}
 .h,.pt{color:#000}.q{color:#333;border-color:#ccc}.n{color:#888}a{color:#000}}
</style></head><body>
__NAV__
<div class="wrap">
<h1>Narration text</h1>
<p class="lede">Exactly what is spoken, in order — including paragraph numbers
and quotation attributions, and excluding what was omitted. __WORDS__ words.</p>
__BODY__
</div></body></html>"""


def build(m4b_url):
    T, tracks, chapters, cues = load()
    total = sum(t["d"] for t in tracks)
    json.dump({"tr": tracks, "ch": chapters, "c": cues},
              open(f"{OUT}/data.json", "w"), ensure_ascii=False,
              separators=(",", ":"))
    print(f"  {OUT}/data.json  ({os.path.getsize(OUT+'/data.json')/1e6:.1f} MB)")

    write("index.html", READER.replace("__NAV__", nav(0)))

    # about
    import subprocess, re
    lufs = peak = "—"
    try:
        v = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i",
                            "out/ChristOurPascha.m4b", "-af", "ebur128=peak=true",
                            "-f", "null", "-"], capture_output=True, text=True)
        tail = v.stderr[v.stderr.rfind("Summary:"):]
        lufs = re.search(r"I:\s*(-?[\d.]+)", tail).group(1)
        peak = re.search(r"Peak:\s*(-?[\d.]+)", tail).group(1)
    except Exception:
        pass
    import lexicon
    dl = ""
    if m4b_url:
        dl = ('<h2>Download</h2><p><a href="%s">Download the complete audiobook '
              '(M4B, ~395 MB)</a> for offline listening in any audiobook app. '
              'It carries the same 232 chapter marks.</p>' % html.escape(m4b_url))
    about = (ABOUT.replace("__NAV__", nav(2))
                  .replace("__LUFS__", lufs).replace("__PEAK__", peak)
                  .replace("__DUR__", f"{int(total//3600)} h {int(total%3600//60)} m")
                  .replace("__NCH__", str(len(chapters)))
                  .replace("__NLEX__", str(len(lexicon.OVERRIDES)))
                  .replace("__DOWNLOAD__", dl))
    write("about.html", about)

    # printable narration text
    N = json.load(open("work/normalized.json"))
    out, words, lastp = [], 0, None
    for b in N:
        t = html.escape(b["text"]); words += len(b["text"].split())
        k = b["kind"]
        if k == "PART":
            out.append(f'<div class="pt">{t}</div>')
        elif k == "HEADING":
            out.append(f'<div class="h">{t}</div>')
        elif k == "QUOTE":
            out.append(f'<p class="q">{t}</p>')
        else:
            p = b.get("para")
            if p and p != lastp:
                lastp = p
                t = re.sub(rf"^{p}\.\s*", "", t)
                out.append(f'<p class="b"><span class="n">{p}</span>{t}</p>')
            else:
                out.append(f'<p class="b">{t}</p>')
    write("text.html", TEXT.replace("__NAV__", nav(1))
                           .replace("__WORDS__", f"{words:,}")
                           .replace("__BODY__", "\n".join(out)))

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")
    ap = argparse.ArgumentParser()
    ap.add_argument("--m4b-url", default=M4B_URL_DEFAULT,
                    help="GitHub Release asset URL for the full M4B")
    a = ap.parse_args()
    build(a.m4b_url)
    print("\nsite built in docs/")
