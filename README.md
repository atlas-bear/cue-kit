# cue-kit

![Alt text](https://github.com/user-attachments/assets/9c78f406-be76-494c-82ff-32c450aed745 "Screenshot of cue-kit")

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-46aef7.svg)](https://github.com/astral-sh/ruff)
[![GitHub Stars](https://img.shields.io/github/stars/atlas-bear/cue-kit?style=social)](https://github.com/atlas-bear/cue-kit/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/atlas-bear/cue-kit)](https://github.com/atlas-bear/cue-kit/issues)

A tactical toolkit for turning videos into structured text. Download a video (URL or local file), extract frames, pull a timestamped transcript, and produce output shaped for the job at hand — a quick summary, an intel brief, a training document, lecture notes aligned to slides, or a clean transcript.

> Status: **alpha**. The `summary` and `transcript` modes work today; `training-doc` and `lecture-notes` are scaffolded and under active development.

## Why this exists

Claude can read a webpage, run a script, browse a repo. Out of the box, it can't watch a video — paste a YouTube URL and it has to guess from the title or work off a transcript that misses everything visual.

cue-kit closes that gap. Hand it a URL or a local file and it produces frames plus a timestamped transcript that an LLM can actually consume. Pair it with the bundled Claude Code skill and `/cue-kit <url> <question>` is a one-liner: Claude `Read`s every frame, sees the transcript, and answers grounded in what's actually on screen and in the audio — not the title, not a guess.

## What it's for

- Watching a video so you don't have to.
- Converting recorded training videos into formatted, navigable docs.
- Capturing lecture-style content where someone narrates over slides — keeping the transcript aligned to each slide.
- Producing a clean, timestamped transcript for any video.

## Common workflows

**Analyzing someone else's content.** Paste a viral YouTube link and ask `what hook did they open with?` — cue-kit pulls the opening frames and the first lines of transcript, and Claude breaks down the structure. Same playbook for ad creative, podcast intros, competitor launches: anywhere the *how* matters as much as the *what*.

**Diagnosing a bug from a screen recording.** Someone sends a `.mov` of something broken. Run it through cue-kit with the question `what's going wrong?` and Claude finds the frame where the issue appears, describes what's on screen, and often catches the cause without you ever opening the file.

**Summarizing a long video.** Most videos don't deserve 20 minutes of attention. Hand cue-kit the URL with `--mode summary` (the default) and you get the structure, the key moments, and what was actually said and shown. Faster than watching at 2x.

## Modes

| Mode | What it produces | Status |
|------|------------------|--------|
| `summary` | Frame timeline + transcript + key-moment notes (default) | working |
| `transcript` | Just a clean, timestamped transcript | working |
| `training-doc` | Raw frames + transcript + a suggested LLM prompt; downstream model produces the formatted doc | scaffolded |
| `lecture-notes` | Transcript grouped under detected slides; falls back to ungrouped transcript while slide detection is stubbed | scaffolded |

## Install

Requires Python 3.10+, `ffmpeg`, and `yt-dlp`. macOS via Homebrew:

```bash
brew install ffmpeg yt-dlp
```

Linux:

```bash
sudo apt install ffmpeg
pip install --user yt-dlp
```

Then install cue-kit itself:

```bash
git clone https://github.com/<your-handle>/cue-kit.git
cd cue-kit
pip install -e .
```

For slide-OCR (`lecture-notes` mode):

```bash
pip install -e '.[ocr]'
# plus: brew install tesseract  (or apt install tesseract-ocr)
```

## Configure

Copy `.env.example` to `~/.config/cue-kit/.env` and fill in a Whisper API key (only needed for videos without native captions):

```bash
mkdir -p ~/.config/cue-kit
cp .env.example ~/.config/cue-kit/.env
chmod 600 ~/.config/cue-kit/.env
```

cue-kit prefers **Groq** (`whisper-large-v3` — cheaper, faster) and falls back to **OpenAI** (`whisper-1`). Set whichever you have.

## Quick start

```bash
# Default: summary of a YouTube video
cue-kit https://youtu.be/<id>

# Just a transcript
cue-kit https://youtu.be/<id> --mode transcript

# Training video → structured doc
cue-kit ./onboarding-screencast.mp4 --mode training-doc

# Lecture with slides → transcript grouped under each detected slide
cue-kit ./talk.mp4 --mode lecture-notes

# Focus on a specific section
cue-kit https://youtu.be/<id> --start 2:15 --end 5:00
```

Output goes to `--out-dir` if specified, otherwise a temp directory printed at the end of the run.

## CLI flags

| Flag | Default | What it does |
|------|---------|--------------|
| `--mode {summary,transcript,training-doc,lecture-notes}` | `summary` | Output shape |
| `--start T` / `--end T` | none | Focus on a section. Accepts `SS`, `MM:SS`, or `HH:MM:SS`. Triggers a denser frame budget. |
| `--max-frames N` | `80` | Cap on frame count. Hard ceiling 100. |
| `--resolution W` | `512` | Frame width in pixels. Bump to `1024` if Claude needs to read on-screen text. |
| `--fps F` | auto | Override the auto-scaled fps. Capped at `2.0`. |
| `--out-dir PATH` | tmp | Working directory. Defaults to a fresh temp dir. |
| `--no-whisper` | off | Disable the Whisper fallback. Frames-only if no native captions. |
| `--whisper {groq,openai}` | auto | Force a backend. Default: prefer Groq, fall back to OpenAI. |

From the Claude Code skill, the same flags work alongside a question:

```
/cue-kit https://youtu.be/<id> --start 0:00 --end 0:30 what hook did they open with?
```

## How it works

1. **Source.** A URL (anything `yt-dlp` supports — YouTube, Loom, TikTok, X, Instagram, hundreds more) or a local file (`.mp4`, `.mov`, `.mkv`, `.webm`, plus a few others — full list in `download.VIDEO_EXTS`).
2. **Download.** `yt-dlp` fetches into a temp working directory; local files are probed in place, no copy.
3. **Frames.** `ffmpeg` extracts at an auto-scaled rate. The frame budget is duration-aware — ≤30s gets ~30 frames, 30-60s gets ~40, 1-3min gets ~60, 3-10min gets ~80, longer gets 100 sparsely. Hard caps: 2 fps, 100 frames. JPEGs at 512px wide by default; bump with `--resolution 1024` to read on-screen text.
4. **Transcript.** First try: `yt-dlp` pulls native captions (manual or auto-generated) — free, fast, and good enough for most public videos. Fallback: extract a mono 16 kHz mp3 and ship it to Whisper — Groq's `whisper-large-v3` (preferred — cheaper and faster) or OpenAI's `whisper-1`.
5. **Output.** The mode renderer prints frame paths with `t=MM:SS` markers and a timestamped transcript. From the skill, Claude `Read`s each frame in parallel — JPEGs render directly as images in its context — and answers grounded in what's actually on screen and in the audio.
6. **Working directory.** Printed at the end of the run. Not auto-cleaned today (see Roadmap) — `rm -rf` it manually when you're done with follow-ups.

## Architecture

```
cue_kit/
├── cli.py             # arg parsing, mode dispatch
├── config.py          # env / .env loading
├── pipeline.py        # download → frames → transcript orchestrator
├── download.py        # yt-dlp wrapper, local file resolver
├── frames.py          # ffmpeg frame extraction, auto-fps budgeting
├── transcribe.py      # WebVTT parsing, dedup, range filtering
├── whisper.py         # Groq / OpenAI Whisper API clients (stdlib only)
├── slides.py          # scene-change detection + slide OCR (lecture-notes)
└── modes/
    ├── summary.py
    ├── transcript.py
    ├── training_doc.py
    └── lecture_notes.py
```

The pipeline is mode-agnostic: it always produces `(frames, transcript_segments, metadata)`. Each mode is a renderer that turns that shared payload into its own output shape.

## Use as a Claude Code skill

`skill/SKILL.md` is a thin wrapper that lets Claude Code drive cue-kit. Symlink or copy it into your skills directory and Claude can invoke `/cue-kit` with the same modes.

## Roadmap

- [ ] `training-doc` mode: section detection, step extraction, glossary
- [ ] `lecture-notes` mode: scene-change keyframe selection, OCR over slides, transcript grouping
- [ ] Optional vision-model captioning of frames (alternative to OCR)
- [ ] Output formatters: PDF, DOCX
- [ ] Windows install path
- [ ] Zero-config install: bootstrap `ffmpeg` and `yt-dlp` via `brew` on macOS first run; print exact `apt` / `winget` commands on Linux and Windows
- [ ] Skill-driven cleanup of the temp working directory after a run with no follow-ups

## License

cue-kit is **dual-licensed**:

- **AGPLv3** for open-source use — see [LICENSE](LICENSE). Anyone running a modified version as a network service must release their changes under the same license.
- **Commercial license** available for proprietary use, private modifications, or any case where the AGPL's terms don't fit. Contact [ryan.clontz@atlasbear.co](mailto:ryan.clontz@atlasbear.co). A starting-point template lives at [COMMERCIAL-LICENSE-TEMPLATE.md](COMMERCIAL-LICENSE-TEMPLATE.md).

Copyright © 2026 Ryan Clontz.
