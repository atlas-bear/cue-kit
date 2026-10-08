from __future__ import annotations

import pytest

from cue_kit import config, whisper


@pytest.fixture
def no_dotenv(monkeypatch):
    monkeypatch.setattr(config, "DOTENV_PATHS", [])
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_load_api_key_prefers_groq(no_dotenv, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert whisper.load_api_key() == ("groq", "g")


def test_load_api_key_falls_back_to_openai(no_dotenv, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert whisper.load_api_key() == ("openai", "o")


def test_load_api_key_forced_backend(no_dotenv, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g")
    assert whisper.load_api_key("openai") == (None, None)
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert whisper.load_api_key("openai") == ("openai", "o")


def test_load_api_key_none(no_dotenv):
    assert whisper.load_api_key() == (None, None)


def test_build_multipart(tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"\x00\x01binary")
    body, boundary = whisper._build_multipart({"model": "whisper-1"}, audio)

    assert boundary.startswith("----CueKitBoundary")
    assert body.startswith(f"--{boundary}\r\n".encode())
    assert body.endswith(f"--{boundary}--\r\n".encode())
    assert b'Content-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n' in body
    assert b'name="file"; filename="audio.mp3"' in body
    assert b"Content-Type: audio/mpeg\r\n\r\n\x00\x01binary\r\n" in body


def test_segments_from_response():
    data = {
        "segments": [
            {"start": 0, "end": 1.234, "text": " hi "},
            {"start": 1.5, "end": 2, "text": "   "},
            {"start": 2, "end": 3, "text": "there"},
        ]
    }
    assert whisper._segments_from_response(data) == [
        {"start": 0.0, "end": 1.23, "text": "hi"},
        {"start": 2.0, "end": 3.0, "text": "there"},
    ]


def test_segments_from_response_text_fallback():
    assert whisper._segments_from_response({"text": " all of it "}) == [
        {"start": 0.0, "end": 0.0, "text": "all of it"}
    ]
    assert whisper._segments_from_response({}) == []


def test_user_agent_is_versioned():
    from cue_kit import __version__

    assert __version__ in whisper.USER_AGENT
    assert "github.com/atlas-bear/cue-kit" in whisper.USER_AGENT
