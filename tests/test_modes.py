from __future__ import annotations

from cue_kit.modes import lecture_notes, summary, training_doc, transcript


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


def test_transcript_render_none(make_result, capsys):
    transcript.render(make_result(transcript_text=None))
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no transcript available" in captured.err


def test_training_doc_render(make_result, capsys):
    training_doc.render(make_result())
    out = capsys.readouterr().out
    assert "# Training doc — Demo video" in out
    assert "## Suggested LLM prompt" in out


def test_lecture_notes_falls_back_without_slide_detection(make_result, capsys):
    lecture_notes.render(make_result())
    captured = capsys.readouterr()
    assert "## Transcript (ungrouped)" in captured.out
    assert "Slides detected: 0" in captured.out
    assert "slide detection" in captured.err
