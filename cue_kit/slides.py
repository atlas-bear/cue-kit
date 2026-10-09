"""Slide detection — used by the lecture-notes mode.

For lecture-style videos where someone narrates over slides, we don't want
N evenly-spaced frames; we want one frame *per slide*. Strategy:

1. Run ffmpeg's `freezedetect` filter to find the stretches where the picture
   holds still. On a slide deck, each still stretch is one slide; transitions,
   fades, and animations are the gaps between them. Per-frame scene-change
   scores don't work here: a fade spreads the change across many frames and a
   text-only change on a plain background barely registers.
2. Merge still stretches that start within a couple of seconds of each other,
   and adjacent slides whose images barely differ (a webcam inset, a moving
   cursor, or a bullet build can split one slide into several).
3. Grab one image per slide from the *end* of its still stretch, so slides with
   bullet-by-bullet builds are captured in their completed state.
4. (Optional) OCR each slide image for slide text.
5. Group transcript segments under the slide active at their timestamp.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from cue_kit.errors import CueKitError

# How much frame-to-frame change still counts as "holding still" (ffmpeg
# freezedetect noise ratio). Raise it for videos with a webcam inset or a
# moving cursor; lower it if consecutive slides are being merged.
DEFAULT_TOLERANCE = 0.003
MIN_STILL_SECONDS = 1.0
DEFAULT_MIN_GAP_SECONDS = 2.0
MAX_SLIDES = 200
DETECT_TIMEOUT = 3600
EXTRACT_TIMEOUT = 120

# Adjacent slides whose thumbnails differ in fewer than this fraction of
# pixels are treated as one slide (keeping the later image). Measured on real
# and synthetic decks: cursor/UI jitter ~0.2-0.7%, a bullet build ~1%, a new
# slide on the same template ~3%+.
DUPLICATE_FRACTION = 0.015
_THUMB_W, _THUMB_H = 128, 72
_PIXEL_DELTA = 32

_FREEZE_RE = re.compile(r"freeze_(start|end):\s*(-?[\d.]+)")


@dataclass
class Slide:
    index: int
    timestamp_seconds: float
    frame_path: str
    ocr_text: str | None = None  # populated when OCR is enabled


def _run(cmd: list[str], timeout: int, what: str, binary: bool = False):
    try:
        if binary:
            return subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CueKitError(f"{what} timed out after {timeout}s") from exc


def _parse_freezes(stderr: str, range_end: float) -> list[tuple[float, float]]:
    """Return (start, end) still stretches, relative to the analysed range."""
    segments: list[tuple[float, float]] = []
    start: float | None = None
    for kind, value in _FREEZE_RE.findall(stderr):
        t = float(value)
        if kind == "start":
            start = t
        elif start is not None:
            segments.append((start, t))
            start = None
    if start is not None:
        segments.append((start, max(start, range_end)))
    return segments


def _merge_close(
    segments: list[tuple[float, float]], min_gap: float
) -> list[tuple[float, float]]:
    """Merge stretches that start within `min_gap` seconds of the previous one,
    keeping the earlier start and the later end."""
    merged: list[tuple[float, float]] = []
    for start, end in segments:
        if merged and start - merged[-1][0] < min_gap:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged


def _changed_fraction(a: bytes, b: bytes) -> float:
    """Fraction of pixels that differ noticeably between two grayscale thumbnails."""
    if not a or len(a) != len(b):
        return 1.0
    changed = sum(1 for x, y in zip(a, b, strict=True) if abs(x - y) > _PIXEL_DELTA)
    return changed / len(a)


def _extract_frame(video_path: str, at: float, resolution: int, out_path: Path) -> bool:
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{max(at, 0.0):.3f}",
        "-i", video_path,
        "-frames:v", "1",
        "-vf", f"scale={resolution}:-2",
        "-q:v", "3",
        str(out_path),
    ]
    result = _run(cmd, EXTRACT_TIMEOUT, "slide image extraction")
    return result.returncode == 0 and out_path.is_file()


def _thumbnails(paths: list[Path]) -> list[bytes]:
    thumbs: list[bytes] = []
    size = _THUMB_W * _THUMB_H
    for path in paths:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(path),
            "-vf", f"scale={_THUMB_W}:{_THUMB_H},format=gray",
            "-f", "rawvideo", "-",
        ]
        result = _run(cmd, EXTRACT_TIMEOUT, "slide comparison", binary=True)
        thumbs.append(result.stdout[:size] if result.returncode == 0 else b"")
    return thumbs


def _video_duration(video_path: str) -> float:
    from cue_kit.frames import get_metadata

    return get_metadata(video_path)["duration_seconds"]


def detect_slides(
    video_path: str,
    out_dir: Path,
    tolerance: float = DEFAULT_TOLERANCE,
    resolution: int = 1024,  # higher than summary frames — we want readable text
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    duration_seconds: float | None = None,
    min_gap_seconds: float = DEFAULT_MIN_GAP_SECONDS,
    max_slides: int = MAX_SLIDES,
) -> list[Slide]:
    """Extract one image per slide, in chronological order.

    `timestamp_seconds` is when the slide settled on screen. If the video never
    holds still (e.g. a talking-head recording), a single slide is returned.
    """
    if not 0 < tolerance < 1:
        raise CueKitError("slide tolerance must be between 0 and 1")
    if shutil.which("ffmpeg") is None:
        raise CueKitError("ffmpeg is not installed. See README install instructions.")

    offset = start_seconds or 0.0
    if end_seconds is None:
        end_seconds = duration_seconds if duration_seconds else _video_duration(video_path)
    range_len = max(0.0, end_seconds - offset)

    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "info"]
    if start_seconds is not None:
        cmd += ["-ss", f"{start_seconds:.3f}"]
    cmd += ["-to", f"{end_seconds:.3f}"] if end_seconds else []
    cmd += [
        "-i", video_path,
        "-an",
        "-vf", f"freezedetect=n={tolerance}:d={MIN_STILL_SECONDS}",
        "-f", "null", "-",
    ]
    result = _run(cmd, DETECT_TIMEOUT, "slide detection")
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-5:])
        raise CueKitError(f"ffmpeg slide detection failed: {tail}")

    segments = _merge_close(_parse_freezes(result.stderr, range_len), min_gap_seconds)
    if not segments:
        print(
            "[cue-kit] warning: the picture never holds still, so no slides were found "
            "(is this a slide-based video?). Try a higher --slide-tolerance.",
            file=sys.stderr,
        )
        segments = [(0.0, min(range_len, 1.0))]
    if len(segments) > max_slides:
        print(
            f"[cue-kit] warning: {len(segments)} slides found; keeping the first {max_slides}",
            file=sys.stderr,
        )
        segments = segments[:max_slides]

    out_dir.mkdir(parents=True, exist_ok=True)
    for existing in out_dir.glob("slide_*.jpg"):
        existing.unlink()

    slides: list[Slide] = []
    for start, end in segments:
        path = out_dir / f"slide_{len(slides) + 1:04d}.jpg"
        # Last frame of the still stretch = the slide with any builds completed.
        settled = offset + max(start, end - 0.3)
        if not _extract_frame(video_path, settled, resolution, path) and not _extract_frame(
            video_path, offset + start, resolution, path
        ):
            continue
        slides.append(Slide(len(slides), round(offset + start, 2), str(path)))

    return _drop_duplicates(slides)


def _drop_duplicates(slides: list[Slide]) -> list[Slide]:
    """Merge adjacent slides whose images are effectively identical."""
    if len(slides) < 2:
        return slides
    thumbs = _thumbnails([Path(s.frame_path) for s in slides])
    kept: list[Slide] = [slides[0]]
    kept_thumb = thumbs[0]
    for slide, thumb in zip(slides[1:], thumbs[1:], strict=True):
        if _changed_fraction(kept_thumb, thumb) < DUPLICATE_FRACTION:
            Path(kept[-1].frame_path).unlink(missing_ok=True)
            kept[-1].frame_path = slide.frame_path
        else:
            kept.append(slide)
        kept_thumb = thumb
    for i, slide in enumerate(kept):
        slide.index = i
    return kept


def ocr_slide(slide: Slide) -> str:
    """OCR a single slide image. Requires the [ocr] extras (pytesseract + Pillow)
    and the `tesseract` binary on PATH."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise CueKitError(
            "OCR needs the optional dependencies: pip install 'cue-kit[ocr]'"
        ) from exc
    try:
        with Image.open(slide.frame_path) as image:
            text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as exc:
        raise CueKitError(
            "OCR needs the tesseract binary on PATH (brew install tesseract, "
            "apt install tesseract-ocr, or winget install UB-Mannheim.TesseractOCR)"
        ) from exc
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def group_transcript_by_slide(
    slides: list[Slide],
    transcript_segments: list[dict],
) -> list[dict]:
    """Bucket each transcript segment under the slide active at its timestamp.

    Returns a list shaped like:
        [{"slide": Slide, "segments": [seg, seg, ...]}, ...]

    A segment belongs to slide N if slides[N].timestamp <= seg.start < slides[N+1].timestamp
    (or end-of-video for the last slide). Segments that start before the first
    slide (e.g. a caption already running when a focus range begins) go to the
    first slide.
    """
    if not slides:
        return [{"slide": None, "segments": list(transcript_segments)}]

    boundaries = [float("-inf")] + [s.timestamp_seconds for s in slides[1:]] + [float("inf")]
    buckets: list[dict] = [{"slide": s, "segments": []} for s in slides]

    for seg in transcript_segments:
        for i in range(len(slides)):
            if boundaries[i] <= seg["start"] < boundaries[i + 1]:
                buckets[i]["segments"].append(seg)
                break

    return buckets
