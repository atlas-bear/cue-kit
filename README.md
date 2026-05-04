# cue-kit

![Alt text](https://github.com/user-attachments/assets/9c78f406-be76-494c-82ff-32c450aed745 "Screenshot of cue-kit")

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-46aef7.svg)](https://github.com/astral-sh/ruff)
[![GitHub Stars](https://img.shields.io/github/stars/atlas-bear/cue-kit?style=social)](https://github.com/atlas-bear/cue-kit/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/atlas-bear/cue-kit)](https://github.com/atlas-bear/cue-kit/issues)

A tactical toolkit for turning video into structured, usable text. Feed it a URL or local file and get extracted frames, a timestamped transcript, and output tailored to your goal — from quick summaries and intel briefs to training docs, lecture notes, or clean transcripts.

LLMs like Claude can read pages, run code, and browse repos — but they can’t truly watch video. Drop in a YouTube link and they’re left guessing from titles or relying on incomplete transcripts that miss the visuals.

cue-kit fixes that. It converts video into frames plus a synchronized transcript that LLMs can actually process. With the bundled Claude Code skill, `/cue-kit <url> <question>` becomes a one-liner: Claude analyzes every frame, follows the transcript, and answers based on what’s really happening — on screen and in audio, not guesswork.

> Status: **alpha**. The `summary` and `transcript` modes work today; `training-doc` and `lecture-notes` are scaffolded and under active development.

## What it's for

- Watching a video so you don't have to.
- Converting recorded training videos into formatted, navigable docs.
- Capturing lecture-style content where someone narrates over slides — keeping the transcript aligned to each slide.
- Producing a clean, timestamped transcript for any video.

## Common workflows

**Tracking suspicious vessel behavior.** 
Feed in AIS playback clips or screen recordings of vessel movement. Cue-kit isolates key segments—course changes, loitering patterns, or AIS gaps—and surfaces the exact moments where behavior deviates from norms. Instead of scrubbing timelines manually, you get a quick breakdown of when and how a vessel started acting suspiciously.

**Analyzing port activity from video feeds.** 
Drop in CCTV or drone footage from port areas and ask what changed over time. Cue-kit extracts key frames and summarizes activity patterns—unusual docking sequences, unexpected cargo handling, or irregular vessel arrivals. Useful for quickly spotting anomalies without reviewing hours of footage.

**Extracting insights from incident recordings.** 
After an onboard incident or near miss, upload bridge recordings or monitoring footage. Cue-kit identifies critical moments leading up to the event, highlights what was visible on instruments or surroundings, and reconstructs a timeline of what likely happened—helping with faster post-incident analysis.

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

## Inspiration & Related Work

- [claude-video](https://github.com/bradautomates/claude-video) — explores enabling Claude to work directly with video inputs  
- OpenAI Whisper — a widely used foundation for speech-to-text transcription  
- Google Video AI — a broader take on extracting structured information from video  
- LangChain — tooling for building structured workflows around LLMs  
- NotebookLM — an example of turning raw content into structured, usable knowledge  

cue-kit builds on similar ideas but focuses on turning video into structured, task-ready outputs for downstream use.

## License

cue-kit is **dual-licensed**:

- **AGPLv3** for open-source use — see [LICENSE](LICENSE). Anyone running a modified version as a network service must release their changes under the same license.
- **Commercial license** available for proprietary use, private modifications, or any case where the AGPL's terms don't fit. A starting-point template lives at [COMMERCIAL-LICENSE-TEMPLATE.md](COMMERCIAL-LICENSE-TEMPLATE.md).
