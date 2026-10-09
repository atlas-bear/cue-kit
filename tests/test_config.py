from __future__ import annotations

from cue_kit import config


def test_from_dotenv_parses_values(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "# comment\n"
        "\n"
        "EMPTY=\n"
        "PLAIN=abc\n"
        "QUOTED=\"with spaces\"\n"
        "SINGLE='single'\n"
        "export EXPORTED=yes\n"
        "  SPACED  =  padded  \n",
        encoding="utf-8",
    )
    assert config._from_dotenv(env, "PLAIN") == "abc"
    assert config._from_dotenv(env, "QUOTED") == "with spaces"
    assert config._from_dotenv(env, "SINGLE") == "single"
    assert config._from_dotenv(env, "EXPORTED") == "yes"
    assert config._from_dotenv(env, "SPACED") == "padded"
    assert config._from_dotenv(env, "EMPTY") is None
    assert config._from_dotenv(env, "MISSING") is None


def test_from_dotenv_handles_bom_and_missing_file(tmp_path):
    env = tmp_path / ".env"
    env.write_bytes("﻿KEY=value\n".encode())
    assert config._from_dotenv(env, "KEY") == "value"
    assert config._from_dotenv(tmp_path / "nope.env", "KEY") is None
    assert config._from_dotenv(tmp_path, "KEY") is None


def test_get_prefers_environment(tmp_path, monkeypatch):
    first = tmp_path / "first.env"
    second = tmp_path / "second.env"
    first.write_text("KEY=from-first\n", encoding="utf-8")
    second.write_text("KEY=from-second\nOTHER=only-second\n", encoding="utf-8")
    monkeypatch.setattr(config, "DOTENV_PATHS", [first, second])

    monkeypatch.setenv("KEY", "from-env")
    assert config.get("KEY") == "from-env"

    monkeypatch.setenv("KEY", "   ")
    assert config.get("KEY") == "from-first"

    monkeypatch.delenv("KEY")
    assert config.get("KEY") == "from-first"
    assert config.get("OTHER") == "only-second"
    assert config.get("ABSENT") is None


def test_config_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert config._config_dir() == tmp_path / "cue-kit"


def test_config_dir_posix(monkeypatch):
    monkeypatch.setattr(config.sys, "platform", "linux")
    assert config._config_dir().parts[-2:] == (".config", "cue-kit")
