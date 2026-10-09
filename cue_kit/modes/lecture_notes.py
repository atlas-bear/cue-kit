"""Lecture-notes mode: transcript grouped under detected slides.

Pipeline:
  1. Detect slides as the stretches where the picture holds still
     (restricted to --start/--end when given).
  2. (Optional, --ocr) OCR each slide image for slide text.
  3. Group transcript segments under the slide active at their timestamp.
  4. Emit a per-slide section with the slide image path, slide text, and narration.
"""
from __future__ import annotations

import sys

from cue_kit import slides as slides_mod
from cue_kit.errors import CueKitError
from cue_kit.frames import format_time
from cue_kit.pipeline import PipelineResult


def _apply_ocr(detected: list[slides_mod.Slide]) -> None:
    print(f"[cue-kit] running OCR on {len(detected)} slides…", file=sys.stderr)
    for slide in detected:
        try:
            slide.ocr_text = slides_mod.ocr_slide(slide) or None
        except CueKitError as exc:
            print(f"[cue-kit] warning: OCR skipped — {exc}", file=sys.stderr)
            return


def render(r: PipelineResult) -> None:
    info = r.info
    title = info.get("title") or r.source

    print(f"[cue-kit] detecting slides (tolerance {r.slide_tolerance})…", file=sys.stderr)
    detected = slides_mod.detect_slides(
        r.video_path,
        r.work_dir / "slides",
        tolerance=r.slide_tolerance,
        resolution=max(r.resolution, 1024),
        start_seconds=r.start_seconds,
        end_seconds=r.end_seconds,
        duration_seconds=r.full_duration or None,
    )
    print(f"[cue-kit] detected {len(detected)} slides", file=sys.stderr)
    if r.ocr:
        _apply_ocr(detected)

    print(f"# Lecture notes — {title}")
    print()
    print(f"- **Source:** {r.source}")
    print(f"- **Duration:** {format_time(r.full_duration)} ({r.full_duration:.1f}s)")
    if r.focused:
        print(
            f"- **Focus range:** {format_time(r.effective_start)} → "
            f"{format_time(r.effective_end)}"
        )
    print(f"- **Slides detected:** {len(detected)}")
    if r.transcript_segments:
        print(
            f"- **Transcript:** {len(r.transcript_segments)} segments via "
            f"{r.transcript_source or 'captions'}"
        )
    else:
        print("- **Transcript:** none available")
    print()
    print(f"Slide images live at: `{r.work_dir / 'slides'}`")
    print()

    groups = slides_mod.group_transcript_by_slide(detected, r.transcript_segments)
    for i, group in enumerate(groups, 1):
        slide = group["slide"]
        stamp = format_time(slide.timestamp_seconds) if slide else "?"
        print(f"## Slide {i} — t={stamp}")
        print()
        if slide:
            print(f"Image: `{slide.frame_path}`")
            print()
        if slide and slide.ocr_text:
            print("**Slide text (OCR):**")
            print()
            print("```")
            print(slide.ocr_text)
            print("```")
            print()
        print("**Narration:**")
        print()
        if group["segments"]:
            for seg in group["segments"]:
                print(f"- [{format_time(int(seg['start']))}] {seg['text']}")
        else:
            print("_No narration during this slide._")
        print()

    print("---")
    print(f"_Work dir: `{r.work_dir}` — delete when done._")
