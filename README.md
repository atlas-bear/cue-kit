# cue-kit

A tactical toolkit for turning videos into structured text. Download a video (URL or local file), extract frames, pull a timestamped transcript, and produce output shaped for the job at hand — a quick summary, a training document, lecture notes aligned to slides, or a clean transcript.

> Status: **alpha**. The `summary` and `transcript` modes work today; `training-doc` and `lecture-notes` are scaffolded and under active development.

## What it's for

- Watching a video so you don't have to.
- Converting recorded training videos into formatted, navigable docs.
- Capturing lecture-style content where someone narrates over slides — keeping the transcript aligned to each slide.
- Producing a clean, timestamped transcript for any video.

## Modes

| Mode | What it produces | Status |
|------|------------------|--------|
| `summary` | Frame timeline + transcript + key-moment notes (default) | working |
| `transcript` | Just a clean, timestamped transcript | working |
| `training-doc` | Structured doc with sections, steps, and key terms | scaffolded |
| `lecture-notes` | Transcript grouped under detected slides (with slide OCR) | scaffolded |

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

## License

MIT — see [LICENSE](LICENSE).
