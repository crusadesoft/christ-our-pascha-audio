# -*- coding: utf-8 -*-
"""Generate the static review site (GitHub Pages) from the built timeline."""
import json, html, os, argparse, base64, pathlib

OUT = "docs"
M4B_URL_DEFAULT = ""   # set to a GitHub Release asset URL once published

def load():
    """Playback tracks and navigation marks are separate: 78 listenable tracks,
    232 places to jump to."""
    T = json.load(open("work/timeline.json"))
    tracks = json.load(open("work/tracks.json"))
    tr = [{"i": t["index"], "t": t["title"], "f": t["file"],
           "s": round(t["start"], 3), "d": round(t["seconds"], 3)} for t in tracks]
    lv = {c["index"]: c.get("level", 0) for c in json.load(open("work/chapters.json"))}
    chapters = [{"i": c["index"], "t": c["title"], "s": round(c["start"], 3),
                 "l": lv.get(c["index"], 0)} for c in T["chapters"]]
    cues = [[round(c["start"], 2), c["chapter"], c["para"] or 0,
             c["kind"][0], c["text"]] for c in T["cues"]]
    return T, tr, chapters, cues


def write(path, body):
    pathlib.Path(f"{OUT}/{path}").write_text(body, encoding="utf-8")
    print(f"  {OUT}/{path}  ({os.path.getsize(f'{OUT}/{path}')/1024:.0f} KB)")


ICONS = None   # filled at build time from the lucide-static package

NAV = """<nav class="nav">
<span class="brand">__I_audio-lines__ Christ Our Pascha</span>
<a href="index.html"{a0}>__I_headphones__<span>Listen</span></a>
<a href="text.html"{a1}>__I_book-open__<span>Text</span></a>
<a href="about.html"{a2}>__I_info__<span>About</span></a>
</nav>"""

def nav(active):
    return NAV.format(**{f"a{i}": ' class="on"' if i == active else ""
                         for i in range(3)})

# Shared unlock. The payload is AES-GCM; the password derives the key, so
# stepping past the prompt in devtools yields nothing.
GATE = """<div id="gate"><div class="gatebox">
 __I_headphones__
 <h1>Christ Our Pascha</h1>
 <p>An audio edition prepared for review. Not yet public \u2014 enter the
 password you were given.</p>
 <div class="gaterow">
  <input type="password" id="pw" placeholder="Password" autocomplete="current-password">
  <button id="go">Open</button>
 </div>
 <div id="gerr"></div>
</div></div>
<script>
const GK='pascha_pw';
async function unlock(pw){
 const buf=await (await fetch('data.enc',{cache:'no-store'})).arrayBuffer();
 const b=new Uint8Array(buf);
 if(String.fromCharCode.apply(null,b.slice(0,5))!=='PSCH1')throw new Error('payload');
 const salt=b.slice(5,21), iv=b.slice(21,33), ct=b.slice(33);
 const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),
   'PBKDF2',false,['deriveKey']);
 const key=await crypto.subtle.deriveKey(
   {name:'PBKDF2',salt:salt,iterations:200000,hash:'SHA-256'},km,
   {name:'AES-GCM',length:256},false,['decrypt']);
 const packed=await crypto.subtle.decrypt({name:'AES-GCM',iv:iv},key,ct);
 const txt=await new Response(new Blob([packed]).stream()
   .pipeThrough(new DecompressionStream('gzip'))).text();
 return JSON.parse(txt);
}
function gateStart(onData){
 const g=document.getElementById('gate'), err=document.getElementById('gerr');
 const tryPw=async(pw,quiet)=>{
  try{ err.textContent=quiet?'':'Checking\u2026';
       const d=await unlock(pw);
       sessionStorage.setItem(GK,pw); g.remove(); onData(d); return true }
  catch(e){ if(!quiet)err.textContent='That password did not work.';
            sessionStorage.removeItem(GK); return false }
 };
 const saved=sessionStorage.getItem(GK);
 if(saved) tryPw(saved,true).then(ok=>{ if(!ok) document.getElementById('pw').focus() });
 else setTimeout(()=>document.getElementById('pw').focus(),80);
 document.getElementById('go').onclick=()=>tryPw(document.getElementById('pw').value,false);
 document.getElementById('pw').addEventListener('keydown',e=>{
   if(e.key==='Enter')tryPw(e.target.value,false)});
}
</script>"""


READER = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#13161c"><meta name="robots" content="noindex,nofollow">
<title>Christ Our Pascha \u2014 Listen</title>
<link rel="stylesheet" href="style.css"></head><body class="reader">
__NAV__
<div id="scrim"></div>
<div id="side">
 <div id="sideHead">Contents<button id="closeCh">__I_x__</button></div>
 <div id="chaps"></div></div>
<div id="main">
 <div id="bar">
   <button class="iconbtn" id="burger" aria-label="Contents">__I_menu__</button>
   <div class="searchwrap">__I_search__
     <input type="search" id="q" placeholder="Search the text\u2026"></div>
   <button class="iconbtn" id="link" title="Copy a link to this moment">
     __I_link-2__<span>Copy link</span></button>
   <button class="iconbtn" id="rss" title="Subscribe in a podcast app">
     __I_rss__<span>Feed</span></button>
 </div>
 <div id="warn" style="display:none"></div>
 <div id="txt"><div class="inner"></div></div>
</div>
<div id="player">
  <div id="np"><img id="art" src="cover.jpg" alt="">
    <div id="npText"><div id="npTitle">&nbsp;</div>
      <div id="npSub">Christ Our Pascha</div></div></div>
  <div id="mid">
    <div id="ctrls">
      <button class="tb" id="prev" title="Previous section">__I_skip-back__</button>
      <button class="tb skip" id="b15" title="Back 15 seconds">__I_rotate-ccw__<span class="lbl">15</span></button>
      <button class="tb" id="play" title="Play">__I_play__</button>
      <button class="tb skip" id="f15" title="Forward 15 seconds">__I_rotate-cw__<span class="lbl">15</span></button>
      <button class="tb" id="next" title="Next section">__I_skip-forward__</button>
    </div>
    <div id="seekRow"><span class="tm" id="cur">0:00:00</span>
      <input type="range" id="seek" min="0" max="1000" value="0" aria-label="Seek">
      <span class="tm r" id="tot">0:00:00</span></div>
  </div>
  <div id="right"><button id="spd">1&times;</button></div>
</div>
<div id="toast"></div>
<audio id="a" preload="metadata"></audio>
__GATE__
<script>
const $=i=>document.getElementById(i), A=$('a'), T=$('txt'), INNER=T.firstElementChild;
let D=null, cur=-1, els=[], trk=-1, seeking=false, TOTAL=0;
const fmt=s=>{s=Math.max(0,s|0);return (s/3600|0)+':'+String(s%3600/60|0).padStart(2,'0')+':'+String(s%60).padStart(2,'0')};
const esc=s=>s.replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
function toast(m){const t=$('toast');t.textContent=m;t.classList.add('show');
 clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),1700)}
gateStart(d=>{D=d;init()});
function init(){
 TOTAL=D.tr.reduce((a,t)=>a+t.d,0); $('tot').textContent=fmt(TOTAL);
 let lastPara=null;
 D.c.forEach((c,i)=>{const d=document.createElement('div');
  d.className='p '+c[3];
  const showNum=c[2]&&c[2]!==lastPara; if(c[2])lastPara=c[2];
  let tx=esc(c[4]); if(showNum)tx=tx.replace(new RegExp('^'+c[2]+'\\.\\s*'),'');
  d.innerHTML=(showNum?'<span class="num">'+c[2]+'</span>':'')+tx;
  d.onclick=()=>seekGlobal(c[0],true); INNER.appendChild(d); els.push(d)});
 const CH=$('chaps');
 D.ch.forEach(c=>{const d=document.createElement('div');
  d.className='ch l'+(c.l||0); d.dataset.c=c.i; d.textContent=c.t;
  d.onclick=()=>{seekGlobal(c.s,true);document.body.classList.remove('nav')};
  CH.appendChild(d)});
 applyHash() || loadTrack(0,0,false);
}
function trackAt(t){let f=D.tr[0];for(const x of D.tr){if(x.s<=t)f=x;else break}return f}
function chapterAt(t){let f=D.ch[0];for(const c of D.ch){if(c.s<=t)f=c;else break}return f}
function loadTrack(i,off,play){
 if(i!==trk){trk=i;A.src='audio/'+D.tr[i].f}
 const go=()=>{A.currentTime=Math.max(0,off);if(play)A.play()};
 if(A.readyState>=1)go(); else A.addEventListener('loadedmetadata',go,{once:true});
}
function seekGlobal(t,play){const x=trackAt(t);loadTrack(D.tr.indexOf(x),t-x.s,play!==false)}
function globalTime(){return trk<0?0:D.tr[trk].s+(A.currentTime||0)}
A.addEventListener('ended',()=>{if(trk<D.tr.length-1)loadTrack(trk+1,0,true)});
const IPLAY=__ICON_PLAY__, IPAUSE=__ICON_PAUSE__;
$('play').onclick=()=>A.paused?A.play():A.pause();
A.addEventListener('play',()=>$('play').innerHTML=IPAUSE);
A.addEventListener('pause',()=>$('play').innerHTML=IPLAY);
const jump=d=>seekGlobal(Math.max(0,Math.min(TOTAL-1,globalTime()+d)),!A.paused);
$('b15').onclick=()=>jump(-15); $('f15').onclick=()=>jump(15);
$('prev').onclick=()=>{const t=globalTime(),c=chapterAt(t),i=D.ch.indexOf(c);
 seekGlobal((t-c.s>3||i===0)?c.s:D.ch[i-1].s,!A.paused)};
$('next').onclick=()=>{const i=D.ch.indexOf(chapterAt(globalTime()));
 if(i<D.ch.length-1)seekGlobal(D.ch[i+1].s,!A.paused)};
const RS=[1,1.1,1.25,1.5,1.75,2,.85];let ri=0;
$('spd').onclick=()=>{ri=(ri+1)%RS.length;A.playbackRate=RS[ri];$('spd').innerHTML=RS[ri]+'&times;'};
$('seek').addEventListener('input',e=>{seeking=true;
 $('cur').textContent=fmt(e.target.value/1000*TOTAL);
 e.target.style.setProperty('--pct',(e.target.value/10)+'%')});
$('seek').addEventListener('change',e=>{seeking=false;
 seekGlobal(e.target.value/1000*TOTAL,!A.paused)});
let hashT=0;
function sync(){
 if(!D)return; const t=globalTime();
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
  $('npSub').textContent='Christ Our Pascha'+(D.c[f][2]?'  \u00b7  paragraph '+D.c[f][2]:'')}
 if(!A.paused&&Date.now()-hashT>3000){hashT=Date.now();
  history.replaceState(null,'','#t='+Math.round(t))}
}
A.addEventListener('timeupdate',sync);
A.addEventListener('seeked',sync);
A.addEventListener('loadeddata',sync);
$('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();let n=0;
 els.forEach((el,i)=>{const hit=v&&D.c[i][4].toLowerCase().includes(v);
  el.classList.toggle('hit',!!hit);if(hit)n++});
 if(v){const k=els.findIndex(el=>el.classList.contains('hit'));
  if(k>=0)els[k].scrollIntoView({block:'center'})}
 $('npSub').textContent=v?n+' matches':'Christ Our Pascha'});
$('link').onclick=()=>{const u=location.origin+location.pathname+'#t='+Math.round(globalTime());
 navigator.clipboard.writeText(u).then(()=>toast('Link copied \u2014 opens here'),()=>toast(u))};
function applyHash(){const h=location.hash;
 let m=h.match(/[#&]t=(\\d+(?:\\.\\d+)?)/); if(m){seekGlobal(parseFloat(m[1]),false);return true}
 m=h.match(/[#&]p=(\\d+)/);
 if(m){const p=+m[1],c=D.c.find(x=>x[2]===p); if(c){seekGlobal(c[0]+0.25,false);return true}}
 return false}
addEventListener('hashchange',applyHash);
const navT=on=>document.body.classList.toggle('nav',on);
$('burger').onclick=()=>navT(!document.body.classList.contains('nav'));
$('closeCh').onclick=()=>navT(false); $('scrim').onclick=()=>navT(false);
addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;
 if(e.code==='Space'){e.preventDefault();A.paused?A.play():A.pause()}
 if(e.key==='ArrowLeft')jump(-15);if(e.key==='ArrowRight')jump(15)});
if('mediaSession' in navigator){
 navigator.mediaSession.setActionHandler('seekbackward',()=>jump(-15));
 navigator.mediaSession.setActionHandler('seekforward',()=>jump(15));
 navigator.mediaSession.setActionHandler('previoustrack',()=>$('prev').click());
 navigator.mediaSession.setActionHandler('nexttrack',()=>$('next').click())}
</script></body></html>"""


ABOUT = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#13161c"><meta name="robots" content="noindex,nofollow">
<title>Christ Our Pascha \u2014 About this recording</title>
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
<p>Read from the English PDF published by the Ukrainian Catholic Church at
<a href="https://ukrcatholic.org/our-faith/our-spirituality/catechism-of-the-ukrainian-catholic-church">ukrcatholic.org</a>
(<a href="https://ukrcatholic.org/fileadmin/user_upload/PDFs/Our_Faith/Christ-our-Pascha-Catechism-of-the-Ukrainian-Catholic-Church-by-Comission-for-the-Catehism-z-lib.org_.pdf">direct
PDF</a>). No other text was used, and nothing was added.</p>
<table>
<tr><th>Work</th><td>Catechism of the Ukrainian Catholic Church: <em>Christ \u2013 Our Pascha</em></td></tr>
<tr><th>Edition</th><td>English, Kyiv\u2013Edmonton 2016; online corrected printing, Nov 2017</td></tr>
<tr><th>Copyright</th><td>\u00a9 2016 Synod of the Ukrainian Greek-Catholic Church<br>
\u00a9 2016 Commission for the Catechism of the UGCC</td></tr>
<tr><th>ISBN</th><td>978\u20130\u20139809309\u20132\u20134</td></tr>
<tr><th>Source file</th><td>3,430,406 bytes<br>
<code style="font-size:11px">SHA-256 82f3622b69d3432de04a3f1c2cd330892e61050280bfc1fd5ea584920c609bf0</code><br>
<span style="color:var(--muted)">verified byte-identical to the file served by
ukrcatholic.org</span></td></tr>
<tr><th>Cover icon</th><td>The Descent into Hades, Volodymyr Sviderski,
St. Josaphat Ukrainian Catholic Cathedral, Edmonton</td></tr>
</table>
<p style="font-size:14px;color:var(--muted)">The catechism text is published
freely online by the Church at the link above. This recording is a derivative
work made from it, offered for review and published only with the permission of
the rights holders. It is not for sale.</p>

<h2>Voices</h2>
<table>
<tr><th>Body text</th><td><code>am_michael</code> \u2014 Kokoro-82M</td></tr>
<tr><th>Quotations</th><td><code>bm_lewis</code> \u2014 Kokoro-82M, so quoted
sources are audibly distinct from the catechism's own voice</td></tr>
</table>

<h2>Editorial decisions</h2>
<table>
<tr><th>Paragraph numbers</th><td><strong>Spoken.</strong> All 1001 are read
before their paragraph, so a listener can track position and find a passage
again.</td></tr>
<tr><th>Heading labels</th><td><strong>Not spoken.</strong> \u201cA.\u201d,
\u201c1.\u201d, \u201ca.\u201d are visual outline aids; they remain in the
contents list for navigation.</td></tr>
<tr><th>Quotation sources</th><td><strong>Spoken</strong> after the quote, in
the quotation voice \u2014 e.g. <em>\u201cIrenaeus of Lyons in Against
Heresies.\u201d</em> Scholarly apparatus (Migne PG/PL columns, section numbers)
is omitted. 64 of 163 block quotes carry no footnote (the Creed, the Anaphora,
Scripture) and receive no attribution.</td></tr>
<tr><th>Scripture citations</th><td>Parenthetical references
<em>(see Jn 3:16)</em> are <strong>omitted</strong> \u2014 read aloud they
interrupt the sentence, and chains of four or five are unlistenable. Citations
that are part of a sentence's grammar are kept. Full references remain in the
transcript.</td></tr>
<tr><th>Footnotes</th><td>Omitted except where they supply a quotation's source.</td></tr>
<tr><th>Indexes</th><td>The Index of Citations and Subject Index are omitted.</td></tr>
</table>

<h2>How it was verified</h2>
<p>Two automated checks guard the recording. The first compares the extracted
text against the PDF itself, independently of the extraction, and requires
better than 99.9% word coverage with no missing run of eight words or more.
The second transcribes every track back to text and diffs it against the
script, to catch skipped or repeated audio.</p>
<table>
<tr><th>Text coverage</th><td>125,476 of 125,476 words \u2014 0.03% unmatched,
no missing runs</td></tr>
<tr><th>Paragraphs</th><td>1001 of 1001 recovered</td></tr>
<tr><th>Transcription</th><td>0.978 mean similarity across all chapters</td></tr>
<tr><th>Loudness</th><td>__LUFS__ LUFS integrated, __PEAK__ dBFS true peak</td></tr>
<tr><th>Duration</th><td>__DUR__ in __NTR__ tracks, __NCH__ navigable sections</td></tr>
</table>
<div class="note"><strong>What the checks cannot tell you.</strong> Neither
verifies that a word is <em>pronounced</em> correctly \u2014 only that it is
present. Pronunciation was hand-tuned for __NLEX__ terms (Pascha, Proskomide,
Theotokos, Sheptytsky and others). Remaining pronunciation errors are the most
likely defect, and the reason for this review.</div>

<h2>Listening in a podcast app</h2>
<p>The recording is also published as a podcast feed. Most podcast apps
(Apple Podcasts, Overcast, Pocket Casts, Podcast Addict) let you add a feed by
URL, and they handle offline download, resuming where you left off, and
playback speed better than any web page can.</p>
<p style="margin:14px 0"><code style="font-size:13px;user-select:all">__FEED__</code></p>
<p style="font-size:14px;color:var(--muted)">In most apps: look for
\u201cAdd a show by URL\u201d, \u201cAdd from URL\u201d, or
\u201cSubscribe by URL\u201d, and paste the address above. On the
<a href="index.html">Listen</a> page the <strong>Feed</strong> button copies it
for you.</p>
<div class="note"><strong>The feed is not password protected.</strong> Podcast
apps cannot decrypt the payload the website uses, so anyone given the feed
address can subscribe without the password. The episode addresses are not
guessable, but please share the feed URL only with reviewers.</div>

<h2>Reporting a problem</h2>
<p>On the <a href="index.html">Listen</a> page, press <strong>Copy link</strong>
at any moment to get a URL that opens at that exact point. That is the most
useful way to report a mispronunciation or a passage that reads wrongly.</p>
__DOWNLOAD__
</div></body></html>"""

TEXT = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#13161c"><meta name="robots" content="noindex,nofollow">
<title>Christ Our Pascha \u2014 Narration text</title>
<link rel="stylesheet" href="style.css">
<style>
.wrap{max-width:820px}
.th{color:var(--gold);font-weight:620;font-size:18px;margin:30px 0 10px}
.tp{color:var(--mint);font-weight:700;font-size:21px;margin:40px 0 12px;
 text-transform:uppercase;letter-spacing:.04em}
.tq{color:#b6bfcc;font-style:italic;margin:0 0 12px;padding-left:20px;
 border-left:3px solid var(--surface-3)}
.tb2{margin:0 0 13px}
.tn{color:var(--dim);font-size:11.5px;margin-right:9px;font-weight:600;
 font-variant-numeric:tabular-nums}
@media print{
 :root{--bg:#fff;--text:#000;--muted:#444;--dim:#777;--surface-3:#ccc}
 body{background:#fff;color:#000}.nav{display:none}
 .th,.tp{color:#000}.tq{color:#333}a{color:#000}}
</style></head><body>
__NAV__
<div class="wrap">
<h1>Narration text</h1>
<p class="lede">Exactly what is spoken, in order \u2014 including paragraph
numbers and quotation attributions, and excluding what was omitted.</p>
<div id="body"><p style="color:var(--dim)">Unlocking\u2026</p></div>
</div>
__GATE__
<script>
gateStart(d=>{
 const esc=s=>s.replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
 const out=[]; let lastPara=null, words=0, cur=null, curKind=null;
 // cues are sentences; regroup them back into blocks for reading
 for(const c of d.c){
  const kind=c[3], para=c[2];
  // group consecutive sentences back into blocks: quotes run several\n  // sentences long, headings and part titles are always their own\n  const isNew = cur===null || curKind!==kind || kind==='H' || kind==='P'\n                || (kind==='B' && para && para!==lastPara);
  if(isNew){ cur={kind:kind,para:para,parts:[]}; out.push(cur); curKind=kind }
  if(para) lastPara=para;
  cur.parts.push(c[4]); words+=c[4].split(/\\s+/).length;
 }
 const h=[];
 for(const b of out){
  let t=esc(b.parts.join(' '));
  if(b.kind==='P') h.push('<div class="tp">'+t+'</div>');
  else if(b.kind==='H') h.push('<div class="th">'+t+'</div>');
  else if(b.kind==='Q') h.push('<p class="tq">'+t+'</p>');
  else{ if(b.para){ t=t.replace(new RegExp('^'+b.para+'\\\\.\\\\s*'),'');
         h.push('<p class="tb2"><span class="tn">'+b.para+'</span>'+t+'</p>') }
        else h.push('<p class="tb2">'+t+'</p>') }
 }
 document.getElementById('body').innerHTML=h.join('\\n');
 document.querySelector('.lede').textContent+=' '+words.toLocaleString()+' words.';
});
</script></body></html>"""

def icons_into(text, ic):
    """Replace __I_name__ markers with inlined Lucide SVG."""
    for name, svg in ic.items():
        text = text.replace(f"__I_{name}__", svg)
    return text


def build(m4b_url, base=""):
    import icons as iconmod
    ic = iconmod.load()
    T, tracks, chapters, cues = load()
    total = sum(t["d"] for t in tracks)
    json.dump({"tr": tracks, "ch": chapters, "c": cues},
              open(f"{OUT}/data.json", "w"), ensure_ascii=False,
              separators=(",", ":"))
    print(f"  {OUT}/data.json  ({os.path.getsize(OUT+'/data.json')/1e6:.1f} MB)")

    gate = icons_into(GATE, ic)
    def page(tpl, active, **kw):
        out = tpl.replace("__NAV__", nav(active)).replace("__GATE__", gate)
        for k, v in kw.items():
            out = out.replace(k, v)
        return icons_into(out, ic)

    write("index.html", page(READER, 0,
          __ICON_PLAY__=json.dumps(ic["play"]),
          __ICON_PAUSE__=json.dumps(ic["pause"])))

    import subprocess, re
    lufs = peak = "\u2014"
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
        dl = ('<h2>Download</h2><p><a href="%s">Download all tracks</a></p>'
              % html.escape(m4b_url))
    write("about.html", page(ABOUT, 2,
          __LUFS__=lufs, __PEAK__=peak,
          __DUR__=f"{int(total//3600)} h {int(total%3600//60)} m",
          __NTR__=str(len(tracks)), __NCH__=str(len(chapters)),
          __NLEX__=str(len(lexicon.OVERRIDES)), __DOWNLOAD__=dl,
          __FEED__=(base.rstrip("/") + "/feed.xml") if base else "feed.xml"))

    write("text.html", page(TEXT, 1))
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "src")
    ap = argparse.ArgumentParser()
    ap.add_argument("--m4b-url", default=M4B_URL_DEFAULT,
                    help="download URL for the complete audio, if any")
    ap.add_argument("--base", default="",
                    help="public site URL, used for the printed feed address")
    a = ap.parse_args()
    build(a.m4b_url, a.base)
    print("\nsite built in docs/")
