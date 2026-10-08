# Changelog

All notable changes to cue-kit are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/). While the version is `0.x`, minor
releases may include breaking changes; they will always be called out below.

## [Unreleased]

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

[Unreleased]: https://github.com/atlas-bear/cue-kit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/atlas-bear/cue-kit/releases/tag/v0.2.0
