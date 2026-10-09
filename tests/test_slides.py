from __future__ import annotations

import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

from cue_kit import slides
from cue_kit.errors import CueKitError
from cue_kit.slides import Slide, group_transcript_by_slide

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def seg(start: float, text: str) -> dict:
    return {"start": start, "end": start + 1, "text": text}


def test_group_without_slides_returns_single_bucket():
    segments = [seg(0, "a"), seg(5, "b")]
    assert group_transcript_by_slide([], segments) == [{"slide": None, "segments": segments}]


def test_group_buckets_by_slide_start():
    slides = [Slide(0, 0.0, "s0.jpg"), Slide(1, 10.0, "s1.jpg"), Slide(2, 20.0, "s2.jpg")]
    segments = [seg(0, "a"), seg(9.9, "b"), seg(10, "c"), seg(25, "d"), seg(500, "e")]
    groups = group_transcript_by_slide(slides, segments)

    assert [[s["text"] for s in g["segments"]] for g in groups] == [
        ["a", "b"],
        ["c"],
        ["d", "e"],
    ]
    assert [g["slide"] for g in groups] == slides


def test_group_assigns_early_segments_to_first_slide():
    slides = [Slide(0, 5.0, "s0.jpg"), Slide(1, 10.0, "s1.jpg")]
    groups = group_transcript_by_slide(slides, [seg(1, "early"), seg(6, "mid"), seg(11, "late")])
    assert [[s["text"] for s in g["segments"]] for g in groups] == [["early", "mid"], ["late"]]


FREEZE_LOG = """\
[freezedetect @ 0x6000] lavfi.freezedetect.freeze_start: 0
[freezedetect @ 0x6000] lavfi.freezedetect.freeze_duration: 7.48
[freezedetect @ 0x6000] lavfi.freezedetect.freeze_end: 7.48
[freezedetect @ 0x6000] lavfi.freezedetect.freeze_start: 7.96
[freezedetect @ 0x6000] lavfi.freezedetect.freeze_end: 16.88
[freezedetect @ 0x6000] lavfi.freezedetect.freeze_start: 17.36
[out#0/null @ 0x600] video:0kB audio:0kB
"""


def test_parse_freezes_closes_open_final_stretch():
    assert slides._parse_freezes(FREEZE_LOG, range_end=24.8) == [
        (0.0, 7.48),
        (7.96, 16.88),
        (17.36, 24.8),
    ]


def test_parse_freezes_empty():
    assert slides._parse_freezes("no freezes here", range_end=10) == []


def test_merge_close_keeps_first_start_and_last_end():
    segments = [(0.0, 5.0), (10.0, 10.5), (11.0, 15.0), (20.0, 25.0)]
    assert slides._merge_close(segments, min_gap=2.0) == [(0.0, 5.0), (10.0, 15.0), (20.0, 25.0)]


def test_changed_fraction():
    a = bytes([0] * 100)
    b = bytes([0] * 97 + [255] * 3)
    assert slides._changed_fraction(a, a) == 0.0
    assert slides._changed_fraction(a, b) == 0.03
    assert slides._changed_fraction(a, bytes([20] * 100)) == 0.0
    assert slides._changed_fraction(a, b"") == 1.0
    assert slides._changed_fraction(b"", b"") == 1.0


def test_drop_duplicates_keeps_first_time_and_last_image(tmp_path, monkeypatch):
    paths = []
    for i in range(4):
        path = tmp_path / f"slide_{i:04d}.jpg"
        path.write_bytes(b"")
        paths.append(str(path))
    base = bytes([0] * 1000)
    nudge = bytes([0] * 995 + [255] * 5)  # 0.5% changed: same slide
    other = bytes([255] * 1000)
    monkeypatch.setattr(slides, "_thumbnails", lambda _paths: [base, nudge, other, other])

    detected = [Slide(i, float(i * 10), paths[i]) for i in range(4)]
    kept = slides._drop_duplicates(detected)

    assert [(s.index, s.timestamp_seconds, s.frame_path) for s in kept] == [
        (0, 0.0, paths[1]),
        (1, 20.0, paths[3]),
    ]
    assert not Path(paths[0]).exists()
    assert not Path(paths[2]).exists()


def test_detect_slides_rejects_bad_tolerance(tmp_path):
    with pytest.raises(CueKitError, match="between 0 and 1"):
        slides.detect_slides("video.mp4", tmp_path, tolerance=1.5)


def make_deck(path):
    """Three solid-colour 'slides' with hard cuts: red 0-3s, blue 3-7s, white 7-10s."""
    inputs = []
    for colour, seconds in (("red", 3), ("blue", 4), ("white", 3)):
        inputs += ["-f", "lavfi", "-i", f"color=c={colour}:s=320x240:d={seconds}:r=10"]
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
         "-filter_complex", "[0][1][2]concat=n=3:v=1:a=0",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )


@needs_ffmpeg
def test_detect_slides_on_generated_deck(tmp_path):
    video = tmp_path / "deck.mp4"
    make_deck(video)
    detected = slides.detect_slides(
        str(video), tmp_path / "slides", resolution=160, duration_seconds=10.0
    )

    assert [s.timestamp_seconds for s in detected] == pytest.approx([0.0, 3.0, 7.0], abs=0.15)
    assert [s.index for s in detected] == [0, 1, 2]
    for slide in detected:
        assert Path(slide.frame_path).is_file()


@needs_ffmpeg
def test_detect_slides_respects_range(tmp_path):
    video = tmp_path / "deck.mp4"
    make_deck(video)
    detected = slides.detect_slides(
        str(video), tmp_path / "slides", resolution=160, start_seconds=4.0, end_seconds=9.5
    )
    assert [s.timestamp_seconds for s in detected] == pytest.approx([4.0, 7.0], abs=0.15)


@needs_ffmpeg
def test_detect_slides_without_still_frames_returns_one_slide(tmp_path, capsys):
    video = tmp_path / "motion.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "testsrc2=s=320x240:r=10:d=4",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
        check=True,
    )
    detected = slides.detect_slides(str(video), tmp_path / "slides", resolution=160)
    assert len(detected) == 1
    assert detected[0].timestamp_seconds == 0.0
    assert "never holds still" in capsys.readouterr().err


def test_ocr_slide_missing_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules, "pytesseract", None)
    with pytest.raises(CueKitError, match=r"cue-kit\[ocr\]"):
        slides.ocr_slide(Slide(0, 0.0, "slide.jpg"))


def test_ocr_slide_cleans_text(monkeypatch, tmp_path):
    image_mod = pytest.importorskip("PIL.Image")
    path = tmp_path / "slide.png"
    image_mod.new("RGB", (8, 8)).save(path)

    class FakeTesseract(types.ModuleType):
        class TesseractNotFoundError(Exception):
            pass

        @staticmethod
        def image_to_string(image):
            return "  Title  \n\n  Bullet one\n"

    monkeypatch.setitem(sys.modules, "pytesseract", FakeTesseract("pytesseract"))
    assert slides.ocr_slide(Slide(0, 0.0, str(path))) == "Title\nBullet one"
