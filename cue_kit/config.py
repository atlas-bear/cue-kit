"""Resolve cue-kit configuration from env vars and dotenv files.

Lookup order for any key: process env > ~/.config/cue-kit/.env > ./.env
"""
from __future__ import annotations

import os
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "cue-kit"
DOTENV_PATHS = [CONFIG_DIR / ".env", Path.cwd() / ".env"]


def _from_dotenv(path: Path, name: str) -> str | None:
    if not path.exists():
        return None
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() != name:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            return value or None
    except OSError:
        return None
    return None


def get(name: str) -> str | None:
    """Read `name` from the environment, then dotenv files, in that order."""
    value = os.environ.get(name)
    if value:
        return value.strip() or None
    for path in DOTENV_PATHS:
        value = _from_dotenv(path, name)
        if value:
            return value
    return None
