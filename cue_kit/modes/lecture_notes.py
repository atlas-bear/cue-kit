"""Lecture-notes mode: transcript grouped under detected slides.

Pipeline:
  1. Detect slide changes via scene-change detection on the source video.
  2. (Optional) OCR each slide image for slide text.
  3. Group transcript segments under the slide active at their timestamp.
  4. Emit a per-slide narrative with the slide's image reference + spoken text.

slides.detect_slides() and slides.ocr_slide() are the implementation hooks —
both currently raise NotImplementedError. Until they land, this mode falls
back to emitting an evenly-sliced transcript with a TODO marker, so the
output shape is testable end-to-end.
"""
from __future__ import annotations

import sys

from cue_kit.frames import format_time
from cue_kit.pipeline import PipelineResult
from cue_kit import slides as slides_mod


def render(r: PipelineResult) -> None:
    info = r.info
    title = info.get("title") or r.source

    print(f"# Lecture notes — {title}")
    print()

    # Slide detection — falls back to "no slides detected" while NotImplementedError stands.
    detected: list[slides_mod.Slide] = []
    try:
        detected = slides_mod.detect_slides(r.video_path, r.work_dir / "slides")
    except NotImplementedError:
        print(
            "[cue-kit] slide detection is scaffolded (slides.detect_slides not implemented). "
            "Falling back to ungrouped transcript output.",
            file=sys.stderr,
        )

    print(f"- Source: {r.source}")
    print(f"- Duration: {format_time(r.full_duration)} ({r.full_duration:.1f}s)")
    print(f"- Slides detected: {len(detected)}")
    if r.transcript_segments:
        print(
            f"- Transcript: {len(r.transcript_segments)} segments via "
            f"{r.transcript_source or 'captions'}"
        )
    else:
        print("- Transcript: none available")
    print()

    if detected:
        groups = slides_mod.group_transcript_by_slide(detected, r.transcript_segments)
        for i, group in enumerate(groups, 1):
            slide = group["slide"]
            stamp = format_time(slide.timestamp_seconds) if slide else "?"
            print(f"## Slide {i} — t={stamp}")
            print()
            if slide and slide.frame_path:
                print(f"![slide {i}]({slide.frame_path})")
                print()
            if slide and slide.ocr_text:
                print("**Slide text (OCR):**")
                print()
                print(slide.ocr_text)
                print()
            print("**Narration:**")
            print()
            if group["segments"]:
                for seg in group["segments"]:
                    s = int(seg["start"])
                    print(f"- [{s // 60:02d}:{s % 60:02d}] {seg['text']}")
            else:
                print("_No transcript covering this slide._")
            print()
    else:
        print("## Transcript (ungrouped)")
        print()
        if r.transcript_text:
            print("```")
            print(r.transcript_text)
            print("```")
        else:
            print("_No transcript available._")

    print("---")
    print(f"_Work dir: `{r.work_dir}` — delete when done._")
