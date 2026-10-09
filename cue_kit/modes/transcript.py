"""Transcript-only mode: just the timestamped transcript, nothing else."""
from __future__ import annotations

from cue_kit.errors import CueKitError
from cue_kit.frames import format_time
from cue_kit.pipeline import PipelineResult


def render(r: PipelineResult) -> None:
    if not r.transcript_text:
        if r.transcript_source and r.focused:
            raise CueKitError(
                f"no transcript lines fall inside {format_time(r.effective_start)}"
                f"-{format_time(r.effective_end)}"
            )
        raise CueKitError(
            "no transcript available: the video has no captions and the Whisper fallback "
            "was unavailable (no API key set, or --no-whisper was used)"
        )

    info = r.info
    title = info.get("title") or r.source
    print(f"# Transcript — {title}")
    print()
    print(f"_Source: {r.transcript_source or 'captions'}._  ", end="")
    print(f"_Duration: {format_time(r.full_duration)}._")
    if r.focused:
        print(
            f"_Filtered to {format_time(r.effective_start)} → "
            f"{format_time(r.effective_end)}._"
        )
    print()
    print(r.transcript_text)
