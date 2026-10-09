from __future__ import annotations

from cue_kit.slides import Slide, group_transcript_by_slide


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


def test_group_drops_segments_before_first_slide():
    slides = [Slide(0, 5.0, "s0.jpg")]
    groups = group_transcript_by_slide(slides, [seg(1, "early"), seg(6, "late")])
    assert [s["text"] for s in groups[0]["segments"]] == ["late"]
