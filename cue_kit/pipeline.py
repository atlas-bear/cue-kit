"""Mode-agnostic pipeline: download → frames → transcript.

Each mode (summary, transcript, training_doc, lecture_notes) consumes the
PipelineResult and renders its own output.
"""
from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from cue_kit import frames as frames_mod
from cue_kit import transcribe, whisper
from cue_kit.download import download, is_url


@dataclass
class PipelineResult:
    source: str
    work_dir: Path
    video_path: str
    info: dict
    metadata: dict
    frames: list[dict]
    transcript_segments: list[dict] = field(default_factory=list)
    transcript_text: str | None = None
    transcript_source: str | None = None
    fps: float = 0.0
    target_frames: int = 0
    max_frames: int = 100
    resolution: int = 512
    focused: bool = False
    start_seconds: float | None = None
    end_seconds: float | None = None
    effective_start: float = 0.0
    effective_end: float = 0.0
    effective_duration: float = 0.0
    full_duration: float = 0.0


def run(
    source: str,
    *,
    out_dir: str | None = None,
    max_frames: int = 80,
    resolution: int = 512,
    fps_override: float | None = None,
    start: str | None = None,
    end: str | None = None,
    use_whisper: bool = True,
    whisper_backend: str | None = None,
) -> PipelineResult:
    max_frames = min(max_frames, 100)

    if out_dir:
        work = Path(out_dir).expanduser().resolve()
    else:
        work = Path(tempfile.mkdtemp(prefix="cue-kit-"))
    work.mkdir(parents=True, exist_ok=True)
    print(f"[cue-kit] working dir: {work}", file=sys.stderr)

    print(
        "[cue-kit] downloading via yt-dlp…" if is_url(source) else "[cue-kit] using local file…",
        file=sys.stderr,
    )
    dl = download(source, work / "download")
    video_path = dl["video_path"]

    meta = frames_mod.get_metadata(video_path)
    full_duration = meta["duration_seconds"]

    start_sec = frames_mod.parse_time(start)
    end_sec = frames_mod.parse_time(end)

    if start_sec is not None and start_sec < 0:
        raise SystemExit("--start must be non-negative")
    if end_sec is not None and start_sec is not None and end_sec <= start_sec:
        raise SystemExit("--end must be greater than --start")
    if full_duration > 0 and start_sec is not None and start_sec >= full_duration:
        raise SystemExit(
            f"--start {start_sec:.1f}s is past end of video ({full_duration:.1f}s)"
        )

    effective_start = start_sec if start_sec is not None else 0.0
    effective_end = end_sec if end_sec is not None else full_duration
    effective_duration = max(0.0, effective_end - effective_start)
    focused = start_sec is not None or end_sec is not None

    if focused:
        fps, target = frames_mod.auto_fps_focus(effective_duration, max_frames=max_frames)
    else:
        fps, target = frames_mod.auto_fps(effective_duration, max_frames=max_frames)
    if fps_override is not None:
        fps = min(fps_override, frames_mod.MAX_FPS)
        target = max(1, int(round(fps * effective_duration)))

    scope = (
        f"{frames_mod.format_time(effective_start)}-{frames_mod.format_time(effective_end)} "
        f"({effective_duration:.1f}s)"
        if focused else f"full {effective_duration:.1f}s"
    )
    print(f"[cue-kit] extracting ~{target} frames at {fps:.3f} fps over {scope}…", file=sys.stderr)

    frames = frames_mod.extract(
        video_path,
        work / "frames",
        fps=fps,
        resolution=resolution,
        max_frames=max_frames,
        start_seconds=start_sec,
        end_seconds=end_sec,
    )

    transcript_segments: list[dict] = []
    transcript_text: str | None = None
    transcript_source: str | None = None
    if dl.get("subtitle_path"):
        try:
            all_segments = transcribe.parse_vtt(dl["subtitle_path"])
            transcript_segments = (
                transcribe.filter_range(all_segments, start_sec, end_sec)
                if focused else all_segments
            )
            transcript_text = transcribe.format_transcript(transcript_segments)
            transcript_source = "captions"
        except Exception as exc:
            print(f"[cue-kit] subtitle parse failed: {exc}", file=sys.stderr)

    if not transcript_segments and use_whisper:
        backend, api_key = whisper.load_api_key(whisper_backend)
        if backend and api_key:
            try:
                all_segments, used_backend = whisper.transcribe_video(
                    video_path,
                    work / "audio.mp3",
                    backend=backend,
                    api_key=api_key,
                )
                transcript_segments = (
                    transcribe.filter_range(all_segments, start_sec, end_sec)
                    if focused else all_segments
                )
                transcript_text = transcribe.format_transcript(transcript_segments)
                transcript_source = f"whisper ({used_backend})"
            except SystemExit as exc:
                print(f"[cue-kit] whisper fallback failed: {exc}", file=sys.stderr)
        else:
            hint = (
                f"--whisper {whisper_backend} was set but the matching API key is missing"
                if whisper_backend else
                "no subtitles and no Whisper API key found"
            )
            print(
                f"[cue-kit] {hint} — set GROQ_API_KEY or OPENAI_API_KEY "
                "in ~/.config/cue-kit/.env to enable the Whisper fallback",
                file=sys.stderr,
            )

    return PipelineResult(
        source=source,
        work_dir=work,
        video_path=video_path,
        info=dl.get("info") or {},
        metadata=meta,
        frames=frames,
        transcript_segments=transcript_segments,
        transcript_text=transcript_text,
        transcript_source=transcript_source,
        fps=fps,
        target_frames=target,
        max_frames=max_frames,
        resolution=resolution,
        focused=focused,
        start_seconds=start_sec,
        end_seconds=end_sec,
        effective_start=effective_start,
        effective_end=effective_end,
        effective_duration=effective_duration,
        full_duration=full_duration,
    )
