# Contributing to cue-kit

## Development setup

```bash
git clone https://github.com/atlas-bear/cue-kit.git
cd cue-kit
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
```

You also need `ffmpeg` and `yt-dlp` on `PATH` (see the README's Install section).

## Checks

Both must pass before a change is merged; CI runs them on Linux, macOS, and Windows.

```bash
ruff check .
pytest
```

Tests are pure unit tests and need no network access or API keys.

## Making changes

- Keep the pipeline mode-agnostic. A new output format is a new `cue_kit/modes/<name>.py`
  with a `render(r: PipelineResult)` function, registered in `MODES` in `cue_kit/cli.py`.
- Raise `CueKitError` (from `cue_kit/errors.py`) for user-facing failures; don't call
  `sys.exit` from library code.
- Use `pathlib` for paths and pass `encoding="utf-8"` when reading or writing text files,
  so behavior is identical on every OS.
- If you change modes or CLI flags, update `README.md` and `skill/SKILL.md` in the same change.
- Add an entry under `## [Unreleased]` in `CHANGELOG.md`.
- Commit messages: imperative subject line, with a body explaining the why when it isn't obvious.

## Releasing (maintainers)

1. Move the `[Unreleased]` entries in `CHANGELOG.md` under a new version heading with today's date.
2. Bump `__version__` in `cue_kit/__init__.py` (the package version is read from there).
3. Commit, merge to `main`, and wait for CI to pass.
4. Tag and push: `git tag v0.X.Y && git push origin v0.X.Y`.

The `Release` workflow re-runs CI, checks that the tag matches `__version__`, builds the
sdist and wheel, creates a GitHub Release with the changelog notes, and publishes to PyPI.

### One-time setup

- **PyPI Trusted Publishing:** on pypi.org, add a pending publisher for project `cue-kit`
  with owner `atlas-bear`, repository `cue-kit`, workflow `release.yml`, environment `pypi`.
- **GitHub environment:** in the repository's Settings → Environments, create an
  environment named `pypi` (optionally requiring maintainer approval).
- **Private vulnerability reporting:** Settings → Code security → enable
  "Private vulnerability reporting" (used by `SECURITY.md`).
