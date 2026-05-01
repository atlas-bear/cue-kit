"""Slide / keyframe detection — used by the lecture-notes mode.

For lecture-style videos where someone narrates over slides, we don't want
N evenly-spaced frames; we want one frame *per slide*. Strategy:

1. Use ffmpeg's `select=gt(scene,T)` filter to emit only frames where the
   scene-change score crosses a threshold. Each detected change is, in
   practice, a slide transition.
2. (Optional) Run OCR over each detected slide to capture slide text.
3. Group transcript segments under the slide whose timestamp range they fall in.

This module is scaffolded — the API below is the contract the lecture-notes
mode will call. Implementation lands in a follow-up commit.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# Default scene-change threshold. Higher = fewer detected slides (more conservative).
# 0.3 is a reasonable starting point for slide decks; tune per source.
DEFAULT_SCENE_THRESHOLD = 0.3


@dataclass
class Slide:
    index: int
    timestamp_seconds: float
    frame_path: str
    ocr_text: str | None = None  # populated when OCR is enabled


def detect_slides(
    video_path: str,
    out_dir: Path,
    threshold: float = DEFAULT_SCENE_THRESHOLD,
    resolution: int = 1024,  # higher than summary frames — we want readable text
) -> list[Slide]:
    """Extract one frame per detected slide change.

    Implementation TODO: ffmpeg `-vf "select=gt(scene\\,{threshold}),scale={W}:-2"`
    with `-vsync vfr` and `-frame_pts 1` so we can recover the source PTS for
    each kept frame. Map each output filename to its PTS to get
    `timestamp_seconds`.
    """
    raise NotImplementedError("slides.detect_slides not yet implemented")


def ocr_slide(slide: Slide) -> str:
    """OCR a single slide image. Requires the [ocr] extras (pytesseract + Pillow).

    Implementation TODO: lazy-import pytesseract; raise a friendly error if it
    or the tesseract binary is missing.
    """
    raise NotImplementedError("slides.ocr_slide not yet implemented")


def group_transcript_by_slide(
    slides: list[Slide],
    transcript_segments: list[dict],
) -> list[dict]:
    """Bucket each transcript segment under the slide active at its timestamp.

    Returns a list shaped like:
        [{"slide": Slide, "segments": [seg, seg, ...]}, ...]

    A segment belongs to slide N if slides[N].timestamp <= seg.start < slides[N+1].timestamp
    (or end-of-video for the last slide).
    """
    if not slides:
        return [{"slide": None, "segments": list(transcript_segments)}]

    boundaries = [s.timestamp_seconds for s in slides] + [float("inf")]
    buckets: list[dict] = [{"slide": s, "segments": []} for s in slides]

    for seg in transcript_segments:
        for i in range(len(slides)):
            if boundaries[i] <= seg["start"] < boundaries[i + 1]:
                buckets[i]["segments"].append(seg)
                break

    return buckets
