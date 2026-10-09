# cue-kit

![Terminal session showing cue-kit producing a video report with frame timeline and transcript](https://raw.githubusercontent.com/atlas-bear/cue-kit/main/assets/cue-kit-terminal.png "Screenshot of cue-kit")

[![CI](https://github.com/atlas-bear/cue-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/atlas-bear/cue-kit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/cue-kit.svg)](https://pypi.org/project/cue-kit/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange.svg)](#modes)
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-46aef7.svg)](https://github.com/astral-sh/ruff)
[![GitHub Stars](https://img.shields.io/github/stars/atlas-bear/cue-kit?style=social)](https://github.com/atlas-bear/cue-kit/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/atlas-bear/cue-kit)](https://github.com/atlas-bear/cue-kit/issues)

A tactical toolkit for turning video into structured, usable text. Feed it a URL or local file and get extracted frames, a timestamped transcript, and output tailored to your goal — from quick summaries and intel briefs to training docs, lecture notes, or clean transcripts.

LLMs like Claude can read pages, run code, and browse repos — but they can’t truly watch video. Drop in a YouTube link and they’re left guessing from titles or relying on incomplete transcripts that miss the visuals.

cue-kit fixes that. It converts video into frames plus a synchronized transcript that LLMs can actually process. With the bundled Claude Code skill, `/cue-kit <url> <question>` becomes a one-liner: Claude analyzes every frame, follows the transcript, and answers based on what’s really happening — on screen and in audio, not guesswork.

> Status: **alpha**. The `summary`, `transcript`, and `lecture-notes` modes work today; `training-doc` is scaffolded and under active development.

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
| `summary` | Source metadata, frame timeline, and timestamped transcript (default) | working |
| `transcript` | Just a clean, timestamped transcript | working |
| `training-doc` | Raw frames + transcript + a suggested LLM prompt; downstream model produces the formatted doc | scaffolded |
| `lecture-notes` | One image per detected slide with the narration spoken while it was on screen; optional OCR of slide text | working |

## Install

cue-kit runs on **macOS, Linux, and Windows** with Python 3.10+. It shells out to two system tools, `ffmpeg` (a full build, including `ffprobe` and the `libmp3lame` encoder — all standard packages qualify) and `yt-dlp`.

**macOS** (Homebrew):

```bash
brew install ffmpeg yt-dlp
```

**Linux** (Debian/Ubuntu):

```bash
sudo apt install ffmpeg
python3 -m pip install --user yt-dlp
```

**Windows** (PowerShell):

```powershell
winget install Gyan.FFmpeg yt-dlp.yt-dlp
```

Open a new terminal afterwards so the updated `PATH` is picked up.

Then install cue-kit itself:

```bash
pip install cue-kit                 # latest release from PyPI
# or pin a specific release straight from GitHub:
pip install "git+https://github.com/atlas-bear/cue-kit@v0.3.0"
```

[`pipx`](https://pipx.pypa.io/) (`pipx install cue-kit`) keeps it in an isolated environment and is the tidiest option for a CLI.

> `yt-dlp` breaks periodically as video sites change. If URL downloads start failing, update it first (`brew upgrade yt-dlp`, `pip install -U yt-dlp`, or `winget upgrade yt-dlp.yt-dlp`).

For development from a clone:

```bash
git clone https://github.com/atlas-bear/cue-kit.git
cd cue-kit
pip install -e '.[dev]'
```

Optional slide OCR for `lecture-notes --ocr` needs the `[ocr]` extra plus the `tesseract` binary:

```bash
pip install 'cue-kit[ocr]'
# macOS: brew install tesseract
# Linux: sudo apt install tesseract-ocr
# Windows: winget install UB-Mannheim.TesseractOCR
```

## Configure

A Whisper API key is only needed for videos without native captions (most local files). cue-kit reads keys from, in order: process environment, the user config file, then `./.env`.

| OS | Config file |
|----|-------------|
| macOS / Linux | `~/.config/cue-kit/.env` |
| Windows | `%APPDATA%\cue-kit\.env` |

```bash
# macOS / Linux
mkdir -p ~/.config/cue-kit
cp .env.example ~/.config/cue-kit/.env
chmod 600 ~/.config/cue-kit/.env
```

```powershell
# Windows
New-Item -ItemType Directory -Force "$env:APPDATA\cue-kit"
Copy-Item .env.example "$env:APPDATA\cue-kit\.env"
```

cue-kit prefers **Groq** (`whisper-large-v3` — cheaper, faster) and falls back to **OpenAI** (`whisper-1`). Set whichever you have.

## Data handling: what leaves your machine

- **Local files with `--no-whisper`:** nothing. All processing (frame extraction, caption parsing) happens locally.
- **URLs:** `yt-dlp` contacts the hosting site to download the video and any captions.
- **Whisper fallback:** only when no captions are available *and* an API key is configured, cue-kit extracts the audio track (mono, 16 kHz) and uploads it to Groq or OpenAI for transcription. Video frames are never uploaded by cue-kit.
- **Working files** (video, frames, audio) stay in the working directory on disk until you delete them.

For sensitive material, pass `--no-whisper` to guarantee no audio leaves the machine. Downstream, whatever reads cue-kit's output (for example, an LLM reading the frames) is governed by that tool's own data policy.

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

Output goes to `--out-dir` if specified, otherwise a fresh temp directory. The working directory is printed at the start and end of the run. `cue-kit --version` prints the installed version.

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
| `--slide-tolerance X` | `0.003` | `lecture-notes`: how much on-screen change is ignored when deciding the picture is holding still. Raise it (e.g. `0.01`) for webcam insets or cursor movement; lower it if separate slides get merged. |
| `--ocr` | off | `lecture-notes`: OCR each slide image and include the slide text. Needs the `[ocr]` extra and `tesseract`. |

From the Claude Code skill, the same flags work alongside a question:

```
/cue-kit https://youtu.be/<id> --start 0:00 --end 0:30 what hook did they open with?
```

## How it works

1. **Source.** A URL (anything `yt-dlp` supports — YouTube, Loom, TikTok, X, Instagram, hundreds more) or a local file (`.mp4`, `.mov`, `.mkv`, `.webm`, plus a few others — full list in `download.VIDEO_EXTS`).
2. **Download.** `yt-dlp` fetches into a temp working directory; local files are probed in place, no copy.
3. **Frames.** `ffmpeg` extracts at an auto-scaled rate. The frame budget is duration-aware — up to 30s gets one frame per second (minimum 12, limited by the 2 fps cap), 30-60s gets 40, 1-3 min gets 60, and anything longer gets 80 (the default `--max-frames`; raise it to 100 for long videos). `--start`/`--end` ranges get a denser budget. Hard caps: 2 fps, 100 frames. JPEGs at 512px wide by default; bump with `--resolution 1024` to read on-screen text.
4. **Transcript.** First try: `yt-dlp` pulls native captions (manual or auto-generated) — free, fast, and good enough for most public videos. Fallback: extract a mono 16 kHz mp3 and ship it to Whisper — Groq's `whisper-large-v3` (preferred — cheaper and faster) or OpenAI's `whisper-1`.
5. **Output.** The mode renderer prints frame paths with `t=MM:SS` markers and a timestamped transcript. From the skill, Claude `Read`s each frame in parallel — JPEGs render directly as images in its context — and answers grounded in what's actually on screen and in the audio.
6. **Working directory.** Printed at the end of the run. Not auto-cleaned today (see Roadmap) — `rm -rf` it manually when you're done with follow-ups.

## Lecture notes: how slide detection works

`lecture-notes` finds the stretches where the picture holds still for at least a second (ffmpeg's `freezedetect` filter). Each one is treated as a slide, and fades, animations and transitions are the gaps between them. For each slide it saves one image from the *end* of the still stretch, so bullet-by-bullet builds show up completed. Adjacent slides that barely differ, such as a moving cursor or a finished build, are merged. Every transcript line is then filed under the slide that was on screen when it was spoken.

It works best on **screen-recorded slides**: Zoom or Teams shares, PowerPoint or Keynote recordings, webinar exports. Expect these limits:

- **Software walkthroughs and screencasts** produce one entry per distinct screen state, which can be many more entries than a slide deck would.
- **Camera-filmed talks** (a phone in the audience, a moving stage camera) never hold still, so no slides are found. cue-kit warns and returns a single entry; use `summary` mode instead.
- **Webcam insets** can split a slide into two. Raise `--slide-tolerance` to `0.01` if you see near-duplicates.

## Architecture

```
cue_kit/
├── cli.py             # arg parsing, mode dispatch
├── config.py          # env / .env loading, per-OS config dir
├── errors.py          # CueKitError (user-facing failures)
├── pipeline.py        # download → frames → transcript orchestrator
├── download.py        # yt-dlp wrapper, local file resolver
├── frames.py          # ffmpeg frame extraction, auto-fps budgeting
├── transcribe.py      # WebVTT parsing, dedup, range filtering
├── whisper.py         # Groq / OpenAI Whisper API clients (stdlib only)
├── slides.py          # slide detection, slide OCR, narration grouping (lecture-notes)
└── modes/
    ├── summary.py
    ├── transcript.py
    ├── training_doc.py
    └── lecture_notes.py
```

The pipeline is mode-agnostic: it always produces a `PipelineResult` (frames, transcript segments, metadata). Each mode is a renderer that turns that shared payload into its own output shape.

## Use as a Claude Code skill

`skill/SKILL.md` is a thin wrapper that lets Claude Code drive cue-kit. Copy (or symlink) the `skill/` directory to `~/.claude/skills/cue-kit/` (or a project's `.claude/skills/cue-kit/`) and Claude can invoke `/cue-kit` with the same modes. The `cue-kit` CLI must be installed and on `PATH`.

## Roadmap

- [ ] `training-doc` mode: section detection, step extraction, glossary
- [ ] Optional vision-model captioning of frames (alternative to OCR)
- [ ] Output formatters: PDF, DOCX
- [ ] Zero-config install: detect missing `ffmpeg` / `yt-dlp` and print the exact `brew` / `apt` / `winget` command for the current OS
- [ ] Skill-driven cleanup of the temp working directory after a run with no follow-ups

## Inspiration & Related Work

- [claude-video](https://github.com/bradautomates/claude-video) — explores enabling Claude to work directly with video inputs  
- OpenAI Whisper — a widely used foundation for speech-to-text transcription  
- Google Video AI — a broader take on extracting structured information from video  
- LangChain — tooling for building structured workflows around LLMs  
- NotebookLM — an example of turning raw content into structured, usable knowledge  

cue-kit builds on similar ideas but focuses on turning video into structured, task-ready outputs for downstream use.

## Contributing & security

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and the release process, [CHANGELOG.md](CHANGELOG.md) for version history, and [SECURITY.md](SECURITY.md) to report a vulnerability privately.

## License

Copyright © 2025–2026 AB//LABS.

cue-kit is **dual-licensed**:

- **AGPLv3** for open-source use — see [LICENSE](LICENSE). Anyone running a modified version as a network service must release their changes under the same license.
- **Commercial license** available for proprietary use, private modifications, or any case where the AGPL's terms don't fit. A starting-point template lives at [COMMERCIAL-LICENSE-TEMPLATE.md](COMMERCIAL-LICENSE-TEMPLATE.md). Contact AB//LABS through the [GitHub organization](https://github.com/atlas-bear).

The Claude Code skill wrapper in [`skill/`](skill/) is separately licensed under the **MIT License** so it can be copied freely into your own Claude Code setup; it contains no cue-kit program code and only invokes the installed CLI.
