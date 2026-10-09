"""Exception types raised by cue-kit library code."""
from __future__ import annotations


class CueKitError(Exception):
    """A user-facing failure. The CLI prints the message and exits non-zero."""
