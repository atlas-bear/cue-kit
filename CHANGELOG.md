# Changelog

All notable changes to cue-kit are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). While the version is `0.x`, minor
releases may include breaking changes; they will always be called out below.

## [Unreleased]

## [0.3.0] - 2026-10-09

### Added
- `lecture-notes` mode now works end to end: it detects slides, saves one image per slide, and
  groups the narration under the slide that was on screen when it was spoken. Slides are found
  as the stretches where the picture holds still (ffmpeg `freezedetect`), each slide image is
  taken after any bullet builds have finished, and near-duplicate slides are merged. Detection
  respects `--start`/`--end`.
- `--slide-tolerance` to tune slide detection (raise it for webcam insets or cursor movement).
- `--ocr` to include each slide's text, using the `[ocr]` extra and `tesseract`.

### Changed
- **Breaking:** `transcript` mode now exits with code 1 and an `[cue-kit] error:` message when
  no transcript is available (previously it printed a notice and exited 0). Scripts that relied
  on exit code 0 should check for this.
- Errors raised while rendering output are reported like other errors (exit code 1), not as a
  traceback.
- Transcript lines that begin just before a `--start` range are filed under the first slide
  instead of being dropped.

### Fixed
- YouTube auto-captions no longer repeat half of each line in transcripts. Each rolling cue's
  carried-over line is now dropped, and the first words of a video are no longer lost.
- WebVTT timestamps without an hours field (`MM:SS.mmm`) are now parsed.
- README: restored the OCR install instructions dropped in 0.2.0.

## [0.2.1] - 2026-10-09

### Changed
- Replaced the README screenshot with one that matches the current report format, styled
  as a macOS terminal window to match AB//LABS' other projects, and
  host it in the repository (`assets/cue-kit-terminal.png`) so it renders on PyPI too.

## [0.2.0] - 2026-10-08

### Added
- Windows support: config file at `%APPDATA%\cue-kit\.env`, UTF-8 console output, and Windows install instructions.
- `--version` flag.
- Input validation with clear errors for `--max-frames`, `--fps`, and `--resolution`.
- Timeouts on `ffprobe` and `ffmpeg` calls so a stalled process can't hang the CLI.
- Unit test suite and a CI matrix covering Linux, macOS, and Windows on Python 3.10 and 3.13, including an end-to-end CLI smoke test.
- Tag-driven release workflow publishing to GitHub Releases and PyPI.
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and a README section describing what data leaves the machine.

### Changed
- Library errors are raised as `CueKitError` and reported by the CLI with exit code 1, instead of exiting from inside library code.
- A directory passed as the source is now rejected with a clear error.
- `.env` files may use `export KEY=value` and may start with a UTF-8 BOM.
- The Whisper client's `User-Agent` now carries the package version and repository URL; `MAX_429_RETRIES` now allows the number of retries its name states.
- Package metadata: author is AB//LABS, project URLs added, PEP 639 license expression, version single-sourced from `cue_kit.__version__`.

### Fixed
- `video.info.json` and `.env` files are read as UTF-8 (non-ASCII titles were garbled or failed on Windows).
- Lecture-notes output no longer renders its footer rule as a heading.
- README accuracy: install URL, summary-mode description, and frame-budget numbers.

### Removed
- Unused `CUE_KIT_OUT_DIR` setting from `.env.example`.

## [0.1.0]

- Initial scaffold: `summary` and `transcript` modes, scaffolded `training-doc` and `lecture-notes` modes, Groq/OpenAI Whisper fallback, and the Claude Code skill wrapper.

[Unreleased]: https://github.com/atlas-bear/cue-kit/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/atlas-bear/cue-kit/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/atlas-bear/cue-kit/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/atlas-bear/cue-kit/releases/tag/v0.2.0
