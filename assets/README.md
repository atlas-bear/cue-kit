# assets

Source files for repository images. Not part of the installed package.

- `terminal-mockup.html` — source for the README screenshot. It mirrors real `summary`-mode
  output for an illustrative 7½-minute local video transcribed via Groq Whisper; the
  video and transcript text are fictional.
- `cue-kit-terminal.png` — the rendered screenshot used in the README. Regenerate it by
  capturing the `.stage` element of the HTML at 2× scale (e.g. with Playwright) and keep
  the mockup in sync when the report format changes.
