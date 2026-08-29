# Christ Our Pascha — audiobook pipeline

Turns the UGCC catechism *Christ Our Pascha* (2016/2017 online edition, 368 pp)
into a chaptered M4B audiobook, plus a synced-transcript review page.

Personal-use build. The source PDF and cover are **not** in this repo
(see `.gitignore`); put them at `ref/source.pdf` and `ref/cover.jpg`.

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
