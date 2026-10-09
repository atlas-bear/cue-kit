---
name: cue-kit
description: Watch a video (URL or local path) and produce structured text — summary, transcript, training doc, or lecture notes. Wraps the cue-kit CLI; downloads with yt-dlp, extracts frames with ffmpeg, transcribes via captions or Whisper API.
argument-hint: "<video-url-or-path> [--mode summary|transcript|training-doc|lecture-notes] [question]"
allowed-tools: Bash, Read, AskUserQuestion
license: MIT
user-invocable: true
---

# /cue-kit — produce structured text from a video

This skill wraps the `cue-kit` CLI. Pick the right `--mode` for the user's intent, run the CLI, then `Read` each emitted frame path so you can see the video, and answer.

## Modes

- **`summary`** *(default)* — full report with frame timeline + transcript. Use when the user asks "what's in this video?" or any open-ended question.
- **`transcript`** — clean timestamped transcript only. Use when they want the spoken content, no frames.
- **`training-doc`** — structured training document scaffold. Use for recorded screencasts / onboarding / how-to videos. After running, format the raw output into the polished doc shape described in the CLI output.
- **`lecture-notes`** — one image per detected slide, with the narration spoken while it was on screen. Use for screen-recorded talks, lectures, and webinars where someone narrates over slides. Not for camera-filmed talks (use `summary`).

## How to invoke

**Step 1 — pick a mode.** Match the user's intent to the table above. When in doubt, ask via `AskUserQuestion`.

**Step 2 — run the CLI.**

```bash
cue-kit "<source>" --mode <mode> [--start T] [--end T] [--max-frames N] [--resolution W] [--fps F] [--no-whisper] [--whisper groq|openai] [--slide-tolerance X] [--ocr]
```

If `cue-kit` isn't on PATH, fall back to `python3 -m cue_kit` (`py -m cue_kit` on Windows). Run `cue-kit --help` for all flags. A non-zero exit means the CLI printed an `[cue-kit] error: ...` line on stderr — relay it to the user.

**Step 3 — Read each frame path** the report lists, in parallel, so you see them together.

**Step 4 — answer.** For `summary`/`transcript`, answer directly with timestamp citations. For `training-doc`, follow the suggested LLM prompt at the bottom of the CLI output to produce the formatted doc. For `lecture-notes`, `Read` each slide image listed under its `## Slide N` heading; the per-slide structure and narration are already in place — summarize or answer per slide. If the CLI warns that no slides were found, or reports far more slides than the talk plausibly has, rerun with `--slide-tolerance 0.01` (webcam insets, cursor movement) or switch to `summary`. Add `--ocr` only if the user needs exact slide text and it's installed.

## Configuration

Whisper API keys (only needed when a video has no native captions) live in `~/.config/cue-kit/.env` on macOS/Linux, or `%APPDATA%\cue-kit\.env` on Windows:

```
GROQ_API_KEY=...
OPENAI_API_KEY=...
```

If the user hits "no transcript available" and wants Whisper, ask them via `AskUserQuestion` which provider they have a key for, then write it to that file (mode `0600`).

## Limits

- Hard cap: 100 frames at 2 fps. The CLI auto-budgets per duration; videos >10 min get a sparse-coverage warning. For long videos with a specific question, pass `--start`/`--end`.
- Token cost is dominated by frames at high resolutions — leave `--resolution 512` unless the user needs to read on-screen text.
- The Whisper fallback uploads the video's audio to Groq or OpenAI. For sensitive material, pass `--no-whisper`.

## License

This skill file is MIT-licensed so it can be copied freely into any Claude Code setup. The cue-kit CLI it invokes is licensed separately (AGPLv3 or commercial — see the repository README).
