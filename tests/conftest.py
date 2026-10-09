from __future__ import annotations

from pathlib import Path

import pytest

from cue_kit.pipeline import PipelineResult


@pytest.fixture
def make_result(tmp_path: Path):
    def _make(**overrides) -> PipelineResult:
        frames_dir = tmp_path / "frames"
        defaults = dict(
            source="https://example.com/video",
            work_dir=tmp_path,
            video_path=str(tmp_path / "video.mp4"),
            info={"title": "Demo video", "uploader": "AB//LABS"},
            metadata={"width": 1280, "height": 720, "codec": "h264"},
            frames=[
                {"index": 0, "timestamp_seconds": 0.0, "path": str(frames_dir / "frame_0001.jpg")},
                {"index": 1, "timestamp_seconds": 5.0, "path": str(frames_dir / "frame_0002.jpg")},
            ],
            transcript_segments=[
                {"start": 0.0, "end": 2.5, "text": "Hello there."},
                {"start": 3.0, "end": 6.0, "text": "Welcome to the demo."},
            ],
            transcript_text="[00:00] Hello there.\n[00:03] Welcome to the demo.",
            transcript_source="captions",
            fps=0.2,
            target_frames=2,
            max_frames=80,
            resolution=512,
            effective_end=10.0,
            effective_duration=10.0,
            full_duration=10.0,
        )
        defaults.update(overrides)
        return PipelineResult(**defaults)

    return _make
