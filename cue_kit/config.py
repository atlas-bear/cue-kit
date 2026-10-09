"""Resolve cue-kit configuration from env vars and dotenv files.

Lookup order for any key: process env > <config dir>/.env > ./.env

The config dir is %APPDATA%\\cue-kit on Windows and ~/.config/cue-kit elsewhere.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _config_dir() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "cue-kit"
    return Path.home() / ".config" / "cue-kit"


CONFIG_DIR = _config_dir()
CONFIG_FILE = CONFIG_DIR / ".env"
DOTENV_PATHS = [CONFIG_FILE, Path.cwd() / ".env"]


def _from_dotenv(path: Path, name: str) -> str | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        if key != name:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        return value or None
    return None


def get(name: str) -> str | None:
    """Read `name` from the environment, then dotenv files, in that order."""
    value = os.environ.get(name)
    if value and value.strip():
        return value.strip()
    for path in DOTENV_PATHS:
        value = _from_dotenv(path, name)
        if value:
            return value
    return None
