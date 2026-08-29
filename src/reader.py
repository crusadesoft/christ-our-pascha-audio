# -*- coding: utf-8 -*-
"""Generate a self-contained local review page: transcript synced to audio."""
import json, html

import base64, pathlib
_cov = pathlib.Path("out/cover.jpg")
COVER_B64 = ("data:image/jpeg;base64," + base64.b64encode(_cov.read_bytes()).decode()
             if _cov.exists() else "")

T = json.load(open("work/timeline.json"))
cues = [[round(c["start"],2), round(c["end"],2), c["chapter"], c["para"] or 0,
         c["kind"][0], c["text"]] for c in T["cues"]]
chaps = [[c["index"], round(c["start"],2), c["title"]] for c in T["chapters"]]
data = json.dumps({"c": cues, "ch": chaps, "dur": round(T["total"],1)},
                  ensure_ascii=False, separators=(",", ":"))

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0d10">
<title>Christ Our Pascha - Review</title><style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0;overscroll-behavior-y:none}
body{font:16px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
 background:#14161a;color:#dfe3e8;height:100dvh;overflow:hidden;
 display:grid;grid-template-rows:1fr auto;grid-template-columns:310px 1fr;
 grid-template-areas:"side main" "player player"}
#scrim{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:8}
#side{grid-area:side;border-right:1px solid #232830;display:flex;flex-direction:column;
 background:#101216;z-index:9;min-height:0}
#side h1{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:#7d8794;
 margin:0;padding:14px 16px;border-bottom:1px solid #232830;display:flex;
 justify-content:space-between;align-items:center}
#closeCh{display:none;background:none;border:0;color:#98a2af;font-size:22px}
#chaps{overflow-y:auto;flex:1;-webkit-overflow-scrolling:touch}
.ch{padding:11px 16px;cursor:pointer;font-size:14px;color:#98a2af;
 border-left:3px solid transparent;min-height:44px;display:flex;align-items:center}
.ch:active{background:#1b2029}
.ch.on{background:#1b2029;color:#8ab4f8;border-left-color:#8ab4f8}
#main{grid-area:main;display:flex;flex-direction:column;min-width:0;min-height:0}
#bar{padding:8px 14px;border-bottom:1px solid #232830;background:#101216;display:flex;
 gap:8px;align-items:center;padding-top:max(8px,env(safe-area-inset-top))}
#burger{display:none;background:#1b1f26;border:1px solid #2d323b;color:#dfe3e8;
 border-radius:8px;font-size:17px;width:42px;height:38px;flex:none}
#q{flex:1;min-width:100px;background:#1b1f26;border:1px solid #2d323b;color:#dfe3e8;
 padding:9px 11px;border-radius:8px;font-size:16px}
#txt{overflow-y:auto;flex:1;padding:18px 22px;-webkit-overflow-scrolling:touch}
.p{margin:0 0 3px;padding:9px 11px;border-radius:7px;cursor:pointer;border-left:3px solid transparent}
.p:active{background:#1b1f26}
.p.on{background:#243044;border-left-color:#8ab4f8;color:#fff}
.p.H{color:#e8c07d;font-weight:600;margin-top:22px;font-size:17px}
.p.P{color:#7fd1b9;font-weight:700;font-size:19px;margin-top:28px}
.p.Q{color:#b8c0cc;font-style:italic;padding-left:22px;border-left:3px solid #333a45}
.num{color:#5a6472;font-size:12px;margin-right:8px;font-variant-numeric:tabular-nums}
.hit{background:#4a3f1a}
/* ---- player, modelled on a podcast/audiobook transport ---- */
#player{grid-area:player;position:relative;background:#0b0d10;border-top:1px solid #232830;
 display:grid;grid-template-columns:1fr minmax(260px,620px) 1fr;align-items:center;
 gap:12px;padding:10px 16px;padding-bottom:max(10px,env(safe-area-inset-bottom))}
#np{min-width:0;display:flex;align-items:center;gap:11px}
#art{height:50px;width:auto;object-fit:contain;border-radius:3px;flex:none;
 background:#1b1f26;box-shadow:0 2px 8px rgba(0,0,0,.55)}
#npText{min-width:0}
#npTitle{font-size:13px;font-weight:600;color:#e8ecf1;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis}
#npSub{font-size:11px;color:#7d8794;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#mid{display:flex;flex-direction:column;gap:5px;min-width:0}
#ctrls{display:flex;justify-content:center;align-items:center;gap:6px}
.tb{background:none;border:0;color:#c3cad3;cursor:pointer;border-radius:50%;
 width:38px;height:38px;font-size:13px;display:flex;align-items:center;justify-content:center}
.tb:hover{color:#fff;background:#1a1f27}
.tb:active{background:#242a34}
#play{background:#e8ecf1;color:#0b0d10;width:42px;height:42px;font-size:16px}
#play:hover{background:#fff;transform:scale(1.05)}
#seekRow{display:flex;align-items:center;gap:9px}
.tm{font-size:11px;color:#8b95a2;font-variant-numeric:tabular-nums;min-width:52px;flex:none}
.tm.r{text-align:right}
#seek{flex:1;-webkit-appearance:none;appearance:none;height:14px;background:none;cursor:pointer}
#seek::-webkit-slider-runnable-track{height:4px;border-radius:2px;
 background:linear-gradient(#8ab4f8,#8ab4f8) 0/var(--pct,0%) 100% no-repeat,#333a45}
#seek::-webkit-slider-thumb{-webkit-appearance:none;width:12px;height:12px;border-radius:50%;
 background:#fff;margin-top:-4px;opacity:0;transition:opacity .12s}
#seek:hover::-webkit-slider-thumb,#seek:active::-webkit-slider-thumb{opacity:1}
#seek::-moz-range-track{height:4px;border-radius:2px;background:#333a45}
#seek::-moz-range-progress{height:4px;border-radius:2px;background:#8ab4f8}
#right{display:flex;justify-content:flex-end;align-items:center;gap:6px}
#spd{background:#1b1f26;border:1px solid #2d323b;color:#dfe3e8;border-radius:14px;
 padding:5px 11px;font-size:12px;cursor:pointer;font-variant-numeric:tabular-nums}
#warn{padding:9px 16px;background:#5a2a2a;color:#ffd9d9;font-size:13px;border-bottom:1px solid #7a3a3a}
@media (max-width:820px){
 body{grid-template-columns:1fr;grid-template-areas:"main" "player"}
 #burger,#closeCh{display:block}
 #side{position:fixed;top:0;bottom:0;left:0;width:min(84vw,320px);
  transform:translateX(-102%);transition:transform .22s ease;box-shadow:0 0 28px #000}
 body.nav #side{transform:none}
 body.nav #scrim{display:block}
 #txt{padding:14px 15px;font-size:17px;line-height:1.7}
 .ch{padding:13px 16px;font-size:15px}
 #player{grid-template-columns:1fr;gap:7px;padding:9px 13px}
 #np{justify-content:center;gap:9px}
 #art{height:40px;width:auto}
 #npText{text-align:left}
 #right{position:absolute;right:12px;top:8px;z-index:2}
 #ctrls{gap:12px}
 .tb{width:44px;height:44px;font-size:14px}
 #play{width:50px;height:50px;font-size:18px}
}
</style></head><body>
<div id="scrim"></div>
<div id="side"><h1>Chapters<button id="closeCh">&times;</button></h1><div id="chaps"></div></div>
<div id="main">
 <div id="bar">
   <button id="burger" aria-label="Chapters">&#9776;</button>
   <input type="search" id="q" placeholder="Search the text...">
   <button class="tb" id="loadBtn" title="Pick the audio file manually"
     style="width:auto;padding:0 10px;display:none">Load audio…</button>
   <input type="file" id="f" accept="audio/*,.m4b,.m4a,.mp3" hidden>
 </div>
 <div id="warn" style="display:none"></div>
 <div id="txt"></div>
</div>
<div id="player">
  <div id="np"><img id="art" src="__COVER__" alt="">
    <div id="npText"><div id="npTitle">&nbsp;</div>
    <div id="npSub">Christ Our Pascha</div></div></div>
  <div id="mid">
    <div id="ctrls">
      <button class="tb" id="prev" title="Previous chapter">&#9198;</button>
      <button class="tb" id="b15" title="Back 15 seconds">&#8630;15</button>
      <button class="tb" id="play" title="Play">&#9654;</button>
      <button class="tb" id="f15" title="Forward 15 seconds">15&#8631;</button>
      <button class="tb" id="next" title="Next chapter">&#9197;</button>
    </div>
    <div id="seekRow">
      <span class="tm" id="cur">0:00:00</span>
      <input type="range" id="seek" min="0" max="1000" value="0" step="1" aria-label="Change progress">
      <span class="tm r" id="tot">0:00:00</span>
    </div>
  </div>
  <div id="right"><button id="spd">1&times;</button></div>
</div>
<audio id="a" preload="metadata" src="ChristOurPascha.m4b?v=__STAMP__"></audio>
<script>
const D=__DATA__, A=document.getElementById('a'), T=document.getElementById('txt');
const $=i=>document.getElementById(i);
let cur=-1, els=[], seeking=false;
const fmt=s=>{s=Math.max(0,s|0);return (s/3600|0)+':'+String(s%3600/60|0).padStart(2,'0')+':'+String(s%60).padStart(2,'0')};
const esc=s=>s.replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
let lastPara=null;
D.c.forEach((c,i)=>{const d=document.createElement('div');
 d.className='p '+c[4];
 // badge only where a paragraph begins, not on every sentence within it
 const showNum = c[3] && c[3]!==lastPara;
 if(c[3]) lastPara=c[3];
 let txt=esc(c[5]);
 // the spoken number ("32.") opens the paragraph; the badge already says it
 if(showNum) txt=txt.replace(new RegExp('^'+c[3]+'\\.\\s*'),'');
 d.innerHTML=(showNum?'<span class="num">'+c[3]+'</span>':'')+txt;
 d.onclick=()=>{A.currentTime=c[0];A.play()}; T.appendChild(d); els.push(d);});
const CH=$('chaps');
D.ch.forEach(c=>{const d=document.createElement('div');d.className='ch';d.dataset.c=c[0];
 d.textContent=c[2];
 d.onclick=()=>{A.currentTime=c[1];A.play();document.body.classList.remove('nav')};
 CH.appendChild(d)});
const nav=on=>document.body.classList.toggle('nav',on);
$('burger').onclick=()=>nav(!document.body.classList.contains('nav'));
$('closeCh').onclick=()=>nav(false); $('scrim').onclick=()=>nav(false);
$('loadBtn').onclick=()=>$('f').click();
$('f').onchange=e=>{A.src=URL.createObjectURL(e.target.files[0]);A.play()};
function checkSync(){const w=$('warn');
 if(!A.duration||!isFinite(A.duration)){w.style.display='none';return}
 const d=Math.abs(A.duration-D.dur);
 if(d>2){w.style.display='block';
  w.textContent='⚠ Audio is '+fmt(A.duration)+' but this transcript expects '+fmt(D.dur)
   +' ('+(d>60?Math.round(d/60)+' min':Math.round(d)+' s')+' apart). Re-master, then hard-reload.';}
 else w.style.display='none';}
A.addEventListener('loadedmetadata',()=>{checkSync();$('tot').textContent=fmt(A.duration);
 $('loadBtn').style.display='none'});
// only offer the manual file picker if the audio could not be fetched
function audioFailed(){
 $('loadBtn').style.display='';
 const w=$('warn'); w.style.display='block';
 w.textContent='\u26a0 Could not load ChristOurPascha.m4b from this server. '
  +'Use \u201cLoad audio\u2026\u201d to pick the file, or start serve.py from the out/ folder.';}
A.addEventListener('error',audioFailed);
addEventListener('load',()=>setTimeout(()=>{
 if(!A.duration||!isFinite(A.duration)) audioFailed();},4000));
A.addEventListener('durationchange',checkSync);
A.addEventListener('play',()=>$('play').innerHTML='&#10073;&#10073;');
A.addEventListener('pause',()=>$('play').innerHTML='&#9654;');
$('play').onclick=()=>A.paused?A.play():A.pause();
const jump=d=>A.currentTime=Math.max(0,Math.min(A.duration||1e9,A.currentTime+d));
$('b15').onclick=()=>jump(-15); $('f15').onclick=()=>jump(15);
function chapAt(t){let f=D.ch[0];for(const c of D.ch){if(c[1]<=t)f=c;else break}return f}
$('prev').onclick=()=>{const t=A.currentTime,c=chapAt(t);
 if(t-c[1]>3){A.currentTime=c[1]}else{const i=D.ch.indexOf(c);A.currentTime=D.ch[Math.max(0,i-1)][1]}};
$('next').onclick=()=>{const i=D.ch.indexOf(chapAt(A.currentTime));
 if(i<D.ch.length-1)A.currentTime=D.ch[i+1][1]};
const RS=[1,1.1,1.25,1.5,1.75,2,.85]; let ri=0;
$('spd').onclick=()=>{ri=(ri+1)%RS.length;A.playbackRate=RS[ri];
 $('spd').innerHTML=RS[ri]+'&times;'};
$('seek').addEventListener('input',e=>{seeking=true;
 $('cur').textContent=fmt(e.target.value/1000*(A.duration||0));
 e.target.style.setProperty('--pct',(e.target.value/10)+'%')});
$('seek').addEventListener('change',e=>{A.currentTime=e.target.value/1000*(A.duration||0);seeking=false});
A.addEventListener('timeupdate',()=>{
 const t=A.currentTime;
 if(!seeking&&A.duration){const v=t/A.duration*1000;
  $('seek').value=v; $('seek').style.setProperty('--pct',(v/10)+'%');}
 $('cur').textContent=fmt(t);
 let lo=0,hi=D.c.length-1,f=-1;
 while(lo<=hi){const m=(lo+hi)>>1; if(D.c[m][0]<=t){f=m;lo=m+1}else hi=m-1}
 if(f!==cur&&f>=0){ if(cur>=0)els[cur].classList.remove('on');
   els[f].classList.add('on'); cur=f;
   const box=T.getBoundingClientRect(), er=els[f].getBoundingClientRect();
   const tgt=T.scrollTop+(er.top-box.top)-(box.height/2)+(er.height/2);
   // smooth only for short hops (playback advancing). Browsers cap smooth-
   // scroll velocity, so a seek across a 400,000px column would crawl.
   T.scrollTo({top:tgt, behavior:Math.abs(tgt-T.scrollTop)>1800?'auto':'smooth'});
   const ci=D.c[f][2];
   [...CH.children].forEach(e=>e.classList.toggle('on',+e.dataset.c===ci));
   const ch=D.ch.find(x=>x[0]===ci);
   $('npTitle').textContent=ch?ch[2]:'';
   $('npSub').textContent='Christ Our Pascha'+(D.c[f][3]?'  ·  paragraph '+D.c[f][3]:'');
 }});
$('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();let n=0;
 els.forEach((el,i)=>{const hit=v&&D.c[i][5].toLowerCase().includes(v);
  el.classList.toggle('hit',!!hit); if(hit)n++;});
 if(v){const k=els.findIndex(el=>el.classList.contains('hit'));if(k>=0)els[k].scrollIntoView({block:'center'});}
 $('npSub').textContent=v?n+' matches':'Christ Our Pascha';});
addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;
 if(e.code==='Space'){e.preventDefault();A.paused?A.play():A.pause()}
 if(e.key==='ArrowLeft')jump(-15); if(e.key==='ArrowRight')jump(15);});
if('mediaSession' in navigator){navigator.mediaSession.setActionHandler('seekbackward',()=>jump(-15));
 navigator.mediaSession.setActionHandler('seekforward',()=>jump(15));}
</script></body></html>"""

html_out = (PAGE.replace("__COVER__", COVER_B64)
                .replace("__DATA__", data)
                .replace("__STAMP__", str(int(T["total"] * 100))))
open("out/review.html", "w").write(html_out)
import os
print(f"wrote out/review.html ({os.path.getsize('out/review.html')/1e6:.1f} MB, "
      f"{len(cues):,} cues)")
