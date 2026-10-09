from __future__ import annotations

import pytest

from cue_kit import slides as slides_mod
from cue_kit.errors import CueKitError
from cue_kit.modes import lecture_notes, summary, training_doc, transcript
from cue_kit.slides import Slide


def test_summary_render(make_result, capsys):
    summary.render(make_result())
    out = capsys.readouterr().out
    assert "# cue-kit: video report" in out
    assert "**Title:** Demo video" in out
    assert "frame_0002.jpg` (t=00:05)" in out
    assert "[00:03] Welcome to the demo." in out
    assert "Warning" not in out


def test_summary_long_video_warning(make_result, capsys):
    summary.render(make_result(full_duration=1800.0))
    assert "30-minute video" in capsys.readouterr().out


def test_summary_without_transcript(make_result, capsys):
    summary.render(make_result(transcript_segments=[], transcript_text=None))
    assert "No transcript available" in capsys.readouterr().out


def test_summary_focused_empty_range(make_result, capsys):
    summary.render(
        make_result(
            transcript_segments=[],
            transcript_text=None,
            focused=True,
            effective_start=60.0,
            effective_end=90.0,
        )
    )
    assert "No transcript lines fell inside 01:00 → 01:30" in capsys.readouterr().out


def test_transcript_render(make_result, capsys):
    transcript.render(make_result())
    out = capsys.readouterr().out
    assert out.startswith("# Transcript — Demo video")
    assert "[00:00] Hello there." in out


def test_transcript_render_none_raises(make_result, capsys):
    with pytest.raises(CueKitError, match="no transcript available"):
        transcript.render(make_result(transcript_text=None, transcript_source=None))
    assert capsys.readouterr().out == ""


def test_transcript_render_empty_focus_range_raises(make_result):
    result = make_result(
        transcript_segments=[],
        transcript_text="",
        focused=True,
        effective_start=60.0,
        effective_end=90.0,
    )
    with pytest.raises(CueKitError, match="no transcript lines fall inside 01:00-01:30"):
        transcript.render(result)


def test_training_doc_render(make_result, capsys):
    training_doc.render(make_result())
    out = capsys.readouterr().out
    assert "# Training doc — Demo video" in out
    assert "## Suggested LLM prompt" in out


def _fake_slides(tmp_path):
    return [
        Slide(0, 0.0, str(tmp_path / "slides" / "slide_0001.jpg")),
        Slide(1, 3.0, str(tmp_path / "slides" / "slide_0003.jpg")),
    ]


def test_lecture_notes_groups_narration_by_slide(make_result, capsys, monkeypatch, tmp_path):
    calls = {}

    def fake_detect(video_path, out_dir, **kwargs):
        calls.update(kwargs)
        return _fake_slides(tmp_path)

    monkeypatch.setattr(slides_mod, "detect_slides", fake_detect)
    lecture_notes.render(make_result(slide_tolerance=0.01))
    captured = capsys.readouterr()
    out = captured.out

    assert calls["tolerance"] == 0.01
    assert calls["resolution"] == 1024
    assert "**Slides detected:** 2" in out
    assert calls["duration_seconds"] == 10.0
    slide1, slide2 = out.split("## Slide 2 — t=00:03")
    assert "## Slide 1 — t=00:00" in slide1
    assert "- [00:00] Hello there." in slide1
    assert "- [00:03] Welcome to the demo." in slide2
    assert "slide_0003.jpg" in slide2
    assert "detected 2 slides" in captured.err


def test_lecture_notes_slide_without_narration(make_result, capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(slides_mod, "detect_slides", lambda *a, **k: _fake_slides(tmp_path))
    lecture_notes.render(make_result(transcript_segments=[], transcript_text=None))
    out = capsys.readouterr().out
    assert out.count("_No narration during this slide._") == 2
    assert "**Transcript:** none available" in out


def test_lecture_notes_ocr(make_result, capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(slides_mod, "detect_slides", lambda *a, **k: _fake_slides(tmp_path))
    monkeypatch.setattr(slides_mod, "ocr_slide", lambda slide: f"Text {slide.index}")
    lecture_notes.render(make_result(ocr=True))
    out = capsys.readouterr().out
    assert "**Slide text (OCR):**" in out
    assert "Text 0" in out and "Text 1" in out


def test_lecture_notes_ocr_unavailable_warns(make_result, capsys, monkeypatch, tmp_path):
    def missing(slide):
        raise CueKitError("OCR needs the optional dependencies")

    monkeypatch.setattr(slides_mod, "detect_slides", lambda *a, **k: _fake_slides(tmp_path))
    monkeypatch.setattr(slides_mod, "ocr_slide", missing)
    lecture_notes.render(make_result(ocr=True))
    captured = capsys.readouterr()
    assert "OCR skipped" in captured.err
    assert "Slide text (OCR)" not in captured.out
    assert "## Slide 2" in captured.out
