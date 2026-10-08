from __future__ import annotations

import pytest

from cue_kit import download
from cue_kit.errors import CueKitError


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("https://youtu.be/abc", True),
        ("http://example.com/v.mp4", True),
        ("./talk.mp4", False),
        ("C:\\Videos\\talk.mp4", False),
        ("file:///tmp/talk.mp4", False),
    ],
)
def test_is_url(source, expected):
    assert download.is_url(source) is expected


def test_resolve_local_ok(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"")
    result = download.resolve_local(str(video))
    assert result["video_path"] == str(video.resolve())
    assert result["info"]["title"] == "clip.mp4"
    assert result["downloaded"] is False


def test_resolve_local_missing(tmp_path):
    with pytest.raises(CueKitError, match="File not found"):
        download.resolve_local(str(tmp_path / "missing.mp4"))


def test_resolve_local_directory(tmp_path):
    with pytest.raises(CueKitError, match="Not a file"):
        download.resolve_local(str(tmp_path))


def test_resolve_local_unknown_extension_warns(tmp_path, capsys):
    odd = tmp_path / "clip.xyz"
    odd.write_bytes(b"")
    download.resolve_local(str(odd))
    assert "not a known video extension" in capsys.readouterr().err


def test_pick_subtitle_prefers_english(tmp_path):
    assert download._pick_subtitle(tmp_path) is None
    (tmp_path / "video.de.vtt").write_text("", encoding="utf-8")
    assert download._pick_subtitle(tmp_path).name == "video.de.vtt"
    (tmp_path / "video.en-US.vtt").write_text("", encoding="utf-8")
    assert download._pick_subtitle(tmp_path).name == "video.en-US.vtt"


def test_pick_video_prefers_mp4(tmp_path):
    assert download._pick_video(tmp_path) is None
    (tmp_path / "video.webm").write_bytes(b"")
    assert download._pick_video(tmp_path).name == "video.webm"
    (tmp_path / "video.mp4").write_bytes(b"")
    assert download._pick_video(tmp_path).name == "video.mp4"


def test_pick_video_ignores_non_video(tmp_path):
    (tmp_path / "video.info.json").write_text("{}", encoding="utf-8")
    (tmp_path / "video.en.vtt").write_text("", encoding="utf-8")
    assert download._pick_video(tmp_path) is None


def test_read_info_utf8(tmp_path):
    info = tmp_path / "video.info.json"
    info.write_text(
        '{"title": "Café — 東京", "channel": "AB//LABS", "duration": 12}', encoding="utf-8"
    )
    result = download._read_info(info, "https://x")
    assert result == {
        "title": "Café — 東京",
        "uploader": "AB//LABS",
        "duration": 12,
        "url": "https://x",
    }


def test_read_info_invalid_json(tmp_path):
    info = tmp_path / "video.info.json"
    info.write_text("not json", encoding="utf-8")
    assert download._read_info(info, "https://x") == {"url": "https://x"}
