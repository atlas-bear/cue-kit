from __future__ import annotations

from cue_kit import transcribe

VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000 align:start position:0%
hello<00:00:00.500><c> world</c>

00:00:02.000 --> 00:00:03.000
hello world

00:00:03.000 --> 00:00:05.000
hello world and more

00:00:05.000 --> 00:00:07,500
<i>second</i> line
continues here

00:00:08.000 --> 00:00:09.000

"""


def write_vtt(tmp_path, text=VTT):
    path = tmp_path / "subs.en.vtt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_parse_vtt_strips_tags_and_dedupes(tmp_path):
    segments = transcribe.parse_vtt(write_vtt(tmp_path))
    assert segments == [
        {"start": 0.0, "end": 5.0, "text": "hello world and more"},
        {"start": 5.0, "end": 7.5, "text": "second line continues here"},
    ]


def test_parse_vtt_handles_non_ascii(tmp_path):
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\ncafé — naïve\n"
    segments = transcribe.parse_vtt(write_vtt(tmp_path, vtt))
    assert segments[0]["text"] == "café — naïve"


def test_parse_vtt_empty_file(tmp_path):
    assert transcribe.parse_vtt(write_vtt(tmp_path, "WEBVTT\n")) == []


SEGMENTS = [
    {"start": 0.0, "end": 4.0, "text": "a"},
    {"start": 5.0, "end": 9.0, "text": "b"},
    {"start": 10.0, "end": 14.0, "text": "c"},
]


def test_filter_range_no_bounds_returns_all():
    assert transcribe.filter_range(SEGMENTS, None, None) == SEGMENTS


def test_filter_range_overlap_inclusive():
    texts = [s["text"] for s in transcribe.filter_range(SEGMENTS, 4.0, 10.0)]
    assert texts == ["a", "b", "c"]


def test_filter_range_open_ended():
    assert [s["text"] for s in transcribe.filter_range(SEGMENTS, 9.5, None)] == ["c"]
    assert [s["text"] for s in transcribe.filter_range(SEGMENTS, None, 4.5)] == ["a"]


def test_format_transcript():
    out = transcribe.format_transcript(
        [{"start": 5.9, "end": 6, "text": "x"}, {"start": 125, "end": 130, "text": "y"}]
    )
    assert out == "[00:05] x\n[02:05] y"


YOUTUBE_ROLLING = """WEBVTT
Kind: captions
Language: en

00:00:00.080 --> 00:00:01.709 align:start position:0%
\x20
I'll<00:00:00.240><c> be</c><00:00:00.359><c> showing</c><00:00:01.520><c> the</c>

00:00:01.709 --> 00:00:01.719 align:start position:0%
I'll be showing the
\x20

00:00:01.719 --> 00:00:03.709 align:start position:0%
I'll be showing the
improved<00:00:02.760><c> PowerPoint</c><00:00:03.360><c> recorder</c>

00:00:03.709 --> 00:00:03.719 align:start position:0%
improved PowerPoint recorder
\x20

00:00:03.719 --> 00:00:05.869 align:start position:0%
improved PowerPoint recorder
right<00:00:04.319><c> here</c>
"""


def test_parse_vtt_youtube_rolling_captions(tmp_path):
    segments = transcribe.parse_vtt(write_vtt(tmp_path, YOUTUBE_ROLLING))
    assert segments == [
        {"start": 0.08, "end": 1.72, "text": "I'll be showing the"},
        {"start": 1.72, "end": 3.72, "text": "improved PowerPoint recorder"},
        {"start": 3.72, "end": 5.87, "text": "right here"},
    ]


def test_parse_vtt_without_hours(tmp_path):
    vtt = "WEBVTT\n\n01:02.500 --> 01:04.000\nshort form\n"
    assert transcribe.parse_vtt(write_vtt(tmp_path, vtt)) == [
        {"start": 62.5, "end": 64.0, "text": "short form"}
    ]
