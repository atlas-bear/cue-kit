"""Default mode: full report with frame timeline and transcript.

This is the original /watch report shape — useful when an LLM (Claude) will
read the frames and produce a summary, or when a human wants the raw evidence.
"""
from __future__ import annotations

from cue_kit.frames import format_time
from cue_kit.pipeline import PipelineResult


def render(r: PipelineResult) -> None:
    info = r.info

    print()
    print("# cue-kit: video report")
    print()
    print(f"- **Source:** {r.source}")
    if info.get("title"):
        print(f"- **Title:** {info['title']}")
    if info.get("uploader"):
        print(f"- **Uploader:** {info['uploader']}")
    print(f"- **Duration:** {format_time(r.full_duration)} ({r.full_duration:.1f}s)")
    if r.focused:
        print(
            f"- **Focus range:** {format_time(r.effective_start)} → {format_time(r.effective_end)} "
            f"({r.effective_duration:.1f}s)"
        )
    if r.metadata.get("width") and r.metadata.get("height"):
        print(
            f"- **Resolution:** {r.metadata['width']}x{r.metadata['height']} "
            f"({r.metadata.get('codec') or 'unknown codec'})"
        )
    mode = "focused" if r.focused else "full"
    print(
        f"- **Frames:** {len(r.frames)} @ {r.fps:.3f} fps, {mode} mode "
        f"(budget {r.target_frames}, max {r.max_frames})"
    )
    print(f"- **Frame size:** {r.resolution}px wide")
    if r.transcript_segments:
        in_range = " in range" if r.focused else ""
        print(
            f"- **Transcript:** {len(r.transcript_segments)} segments{in_range} "
            f"(via {r.transcript_source or 'captions'})"
        )
    else:
        print("- **Transcript:** none available")

    if not r.focused and r.full_duration > 600:
        mins = int(r.full_duration // 60)
        print()
        print(
            f"> **Warning:** This is a {mins}-minute video. Frame coverage is sparse at this "
            "length — accuracy degrades noticeably on anything over 10 minutes. For better "
            "results, re-run with `--start HH:MM:SS --end HH:MM:SS` to zoom into a section."
        )

    print()
    print("## Frames")
    print()
    print(f"Frames live at: `{r.work_dir / 'frames'}`")
    print()
    for frame in r.frames:
        print(f"- `{frame['path']}` (t={format_time(frame['timestamp_seconds'])})")

    print()
    print("## Transcript")
    print()
    if r.transcript_text:
        label = r.transcript_source or "captions"
        if r.focused:
            print(
                f"_Source: {label}. Filtered to "
                f"{format_time(r.effective_start)} → {format_time(r.effective_end)}:_"
            )
        else:
            print(f"_Source: {label}._")
        print()
        print("```")
        print(r.transcript_text)
        print("```")
    elif r.focused and r.transcript_segments == []:
        print(
            f"_No transcript lines fell inside "
            f"{format_time(r.effective_start)} → {format_time(r.effective_end)}._"
        )
    else:
        print(
            "_No transcript available — proceed with frames only. Captions were missing and "
            "the Whisper fallback was unavailable (no API key set, or `--no-whisper` was used)._"
        )

    print()
    print("---")
    print(f"_Work dir: `{r.work_dir}` — delete when done._")
