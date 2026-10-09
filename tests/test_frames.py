from __future__ import annotations

import pytest

from cue_kit import frames
from cue_kit.errors import CueKitError


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("45", 45.0),
        ("1.5", 1.5),
        ("2:15", 135.0),
        ("1:02:03", 3723.0),
        ("0:00:01.250", 1.25),
        (30, 30.0),
        (12.5, 12.5),
    ],
)
def test_parse_time(value, expected):
    assert frames.parse_time(value) == expected


@pytest.mark.parametrize("value", ["abc", "1:2:3:4", "1:xx"])
def test_parse_time_rejects_garbage(value):
    with pytest.raises(CueKitError):
        frames.parse_time(value)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "00:00"), (59.4, "00:59"), (61, "01:01"), (3600, "1:00:00"), (3723, "1:02:03")],
)
def test_format_time(seconds, expected):
    assert frames.format_time(seconds) == expected


@pytest.mark.parametrize(
    ("duration", "expected_target"),
    [(10, 12), (25, 25), (45, 40), (120, 60), (300, 80), (1200, 80)],
)
def test_auto_fps_budget(duration, expected_target):
    fps, target = frames.auto_fps(duration, max_frames=80)
    assert target == expected_target
    assert 0 < fps <= frames.MAX_FPS


def test_auto_fps_respects_max_frames():
    _, target = frames.auto_fps(1200, max_frames=100)
    assert target == 100
    _, target = frames.auto_fps(120, max_frames=10)
    assert target == 10


def test_auto_fps_zero_duration():
    assert frames.auto_fps(0) == (1.0, 1)


def test_auto_fps_caps_fps_for_short_clips():
    fps, target = frames.auto_fps(2, max_frames=80)
    assert fps == frames.MAX_FPS
    assert target == 4


@pytest.mark.parametrize(
    ("duration", "expected_target"),
    [(4, 8), (10, 20), (25, 50), (45, 80), (120, 100), (600, 100)],
)
def test_auto_fps_focus_budget(duration, expected_target):
    fps, target = frames.auto_fps_focus(duration, max_frames=100)
    assert target == expected_target
    assert fps <= frames.MAX_FPS


def test_auto_fps_focus_zero_duration():
    fps, target = frames.auto_fps_focus(0, max_frames=1)
    assert fps == frames.MAX_FPS
    assert target == 1
