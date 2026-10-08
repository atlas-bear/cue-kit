from __future__ import annotations

import pytest

from cue_kit import __version__, cli


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_unknown_mode_rejected(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["video.mp4", "--mode", "nope"])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    ("flags", "message"),
    [
        (["--max-frames", "0"], "--max-frames must be at least 1"),
        (["--fps", "0"], "--fps must be greater than 0"),
        (["--fps", "-1"], "--fps must be greater than 0"),
        (["--resolution", "0"], "--resolution must be at least 16"),
    ],
)
def test_invalid_numeric_flags(tmp_path, capsys, flags, message):
    code = cli.main([str(tmp_path / "missing.mp4"), "--out-dir", str(tmp_path), *flags])
    assert code == 1
    assert message in capsys.readouterr().err


def test_missing_file_is_friendly_error(tmp_path, capsys):
    code = cli.main([str(tmp_path / "missing.mp4"), "--out-dir", str(tmp_path / "work")])
    assert code == 1
    assert "File not found" in capsys.readouterr().err


def test_modes_registered():
    assert set(cli.MODES) == {"summary", "transcript", "training-doc", "lecture-notes"}
