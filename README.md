# Christ Our Pascha — audiobook pipeline

Turns the UGCC catechism *Christ Our Pascha* (2016/2017 online edition, 368 pp)
into a chaptered M4B audiobook, plus a synced-transcript review page.

The source PDF and cover are **not** in this repo (see `.gitignore`).
The PDF is published freely by the Ukrainian Catholic Church:

- <https://ukrcatholic.org/our-faith/our-spirituality/catechism-of-the-ukrainian-catholic-church>
- Direct PDF (3,430,406 bytes, SHA-256 `82f3622b69d3432de04a3f1c2cd330892e61050280bfc1fd5ea584920c609bf0`)

Save it as `ref/source.pdf` and the cover as `ref/cover.jpg`. `verify_text.py`
checks the extraction against that exact file; a different printing would
shift the page ranges in `extract.py`.

## Pipeline

```
ref/source.pdf
  → extract.py       structure-aware text extraction (font size + x-position)
  → verify_text.py   GATE: prove the text covers the PDF   ← run before rendering
  → footnotes.py     recover the 589-note apparatus
  → normalize.py     speech normalization (+ attrib.py for quote sources)
  → units.py         content-addressed render units
  → render_units.py  Kokoro TTS, resumable
  → assemble.py      units → 232 chapters, with pauses
  → qa_all.py        GATE: transcribe and diff against the text
  → timeline.py      exact cue timings   → .srt / .vtt
  → reader.py        review page          → out/review.html
  → master.py        loudness + M4B with chapters and cover
```

## Running it

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv kokoro soundfile "misaki[en]" faster-whisper \
    numpy pymupdf espeakng-loader phonemizer-fork
brew install ffmpeg poppler espeak-ng

.venv/bin/python src/extract.py
.venv/bin/python src/verify_text.py --normalized work/blocks.json   # must PASS
.venv/bin/python src/footnotes.py
.venv/bin/python src/normalize.py
.venv/bin/python src/units.py --voice am_michael --quote-voice bm_lewis
.venv/bin/python src/render_units.py --voice am_michael --workers 1 --threads 6
.venv/bin/python src/assemble.py
.venv/bin/python src/qa_all.py --model base --workers 3
.venv/bin/python src/timeline.py && .venv/bin/python src/reader.py
.venv/bin/python src/master.py --out out/ChristOurPascha.m4b
```

Review page (needs HTTP Range for seeking — the stock `http.server` will not do):

```bash
.venv/bin/python src/serve.py 8777 out    # prints a LAN URL for phones
```

## Editorial decisions

- Paragraph numbers (1–1001) are **spoken**; in a 13-hour reference work they
  are the only way to know where you are.
- Heading enumerators ("A.", "1.") are **not** spoken but are kept in chapter
  titles for navigation.
- Block quotes use a second voice (`bm_lewis`) and close with their source,
  e.g. *"Irenaeus of Lyons in Against Heresies"*. 64 of 163 quotes carry no
  footnote (Creed, Anaphora, Scripture) and correctly get none.
- Parenthetical scripture citations are dropped; grammatical ones are kept.
- Footnote apparatus, Index of Citations, and Subject Index are omitted.

## Things that bit, and why the code looks like it does

- **Verify text against the PDF, not against itself.** The audio QA compares
  rendered audio to the *extracted* text, so extraction losses are invisible to
  it. `verify_text.py` exists because 507 words of appendix prayers went missing
  and nothing noticed.
- **PyMuPDF merges 3-digit marginal numbers into the body line** ("224The good
  deed…"), so paragraph numbers must be split at span level.
- **This PDF hyphenates with U+00AD.** A *hard* hyphen at a line end is a real
  compound hyphen and must be kept, or "God-with-us" becomes "Godwith-us".
- **Two-column appendix pages** must be read column-by-column, banded
  horizontally; banding by the right column's vertical extent splits the left
  column's list in half.
- **Chunking must preserve order.** Emitting a long sentence's fragments before
  flushing the pending buffer makes the narration jump ahead and double back.
- **`nice` on Apple Silicon** relocates a process to the efficiency cores; it
  cut throughput ~4x. Kokoro is essentially sequential — thread count barely
  matters (1.91x at 2 threads, 2.11x at 11).
- **ffmpeg `loudnorm` overshoots its true-peak target** by ~2 dB on a 14-hour
  stream. `alimiter` caps *sample* peak, not true peak. The final trim is what
  actually lands it in spec.
- **Keep derived files in sync.** `assemble.py` writes `chapters.json` because
  QA reads it; when only `chapters.py` wrote it, QA silently diffed new audio
  against stale text.

## The review site (GitHub Pages)

`docs/` is a self-contained static site. Enable Pages on the repo with
**Source: main branch, /docs folder**.

```
docs/
  index.html    reader: 78 audio tracks, 232 navigation marks, deep links
  text.html     the complete narration text, print-styled
  about.html    colophon: AI disclosure, sources, editorial decisions, checks
  audio/*.mp3   78 tracks, ~351 MB, largest 8.9 MB
  data.json     tracks + navigation marks + 5,863 timed cues
  tracks.json   track manifest
  feed.xml      podcast RSS
```

Rebuild after any change to the audio or text:

```bash
.venv/bin/python src/tracks.py                       # cut tracks from the master
.venv/bin/python src/site.py                         # pages + data.json
.venv/bin/python src/feed.py --base https://USER.github.io/REPO
```

### Why tracks and navigation marks differ

The book has 232 sections, but 31 run under a minute and the shortest is
2.4 seconds — fine as places to jump to, useless as files. Tracks merge
sections under 3 minutes and split those over 25, giving 78 files of
3.0–21.1 minutes. The reader maps global time to track + offset, so all 232
marks stay available for navigation and deep links.

### Deep links

`#t=3600` opens at a timestamp; `#p=224` opens at a paragraph. The URL
updates while playing, and **Copy link** puts the current moment on the
clipboard — the intended way to report a mispronunciation.

### Repository size

The audio is ~351 MB committed directly. That is inside GitHub's 1 GB soft
limit but makes clones slow. Git LFS is *not* a fix — Pages does not serve
LFS objects. If the repo needs to stay small, host `audio/` elsewhere and
point `data.json`/`feed.xml` at it.

Pages bandwidth is a 100 GB/month soft limit — roughly 250 complete listens.

## Icons

Lucide, inlined at build time from the `lucide-static` npm package so the site
makes no external requests:

```bash
cd vendor && npm install lucide-static
```

`src/icons.py` pulls the 19 used icons and rewrites their `class` to `ic`.
Note the package ships `class="lucide lucide-NAME"` already — inserting a
second `class` attribute silently does nothing, because browsers keep only
the first.

## Password gate

GitHub Pages is static, so there is no server to check a password. Rather than
hiding the UI behind a JavaScript `if` — which anyone can step past — the
payload itself is encrypted:

- `data.json` (transcript, tracks, timings) → **AES-256-GCM**, key derived by
  **PBKDF2-SHA256, 200,000 iterations** over the password → `docs/data.enc`
- audio files are renamed to unguessable hex; the names exist **only inside
  the encrypted payload**
- `work/tracks.json` holds the manifest and is never published

```bash
.venv/bin/python src/gate.py --password "the-password"
```

The mapping in `work/audio_names.json` keeps filenames stable across rebuilds
so existing links keep working.

**What this is and isn't.** It stops a passer-by: without the password there is
no transcript and no way to discover the audio URLs. It is *not* a security
boundary — anyone with the password can share the decrypted contents or the
file URLs, and those URLs stay valid afterwards. Rotate the password by
re-running `gate.py`; delete `work/audio_names.json` first if the old URLs
should stop working.
