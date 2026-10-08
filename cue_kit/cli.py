"""cue-kit CLI: parse args, dispatch to a mode renderer."""
from __future__ import annotations

import argparse
import sys

from cue_kit import __version__, pipeline
from cue_kit.errors import CueKitError
from cue_kit.modes import lecture_notes, summary, training_doc, transcript

MODES = {
    "summary": summary.render,
    "transcript": transcript.render,
    "training-doc": training_doc.render,
    "lecture-notes": lecture_notes.render,
}


def _force_utf8_output() -> None:
    # Output contains non-ASCII (…, —, →); Windows consoles and redirected
    # streams otherwise default to a legacy code page and raise on print.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="cue-kit",
        description=(
            "Turn a video into structured text — summary, transcript, training doc, "
            "or lecture notes."
        ),
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("source", help="Video URL or local file path")
    ap.add_argument(
        "--mode",
        choices=list(MODES.keys()),
        default="summary",
        help="Output shape (default: summary)",
    )
    ap.add_argument(
        "--max-frames", type=int, default=80, help="Cap on frame count (default 80, hard max 100)"
    )
    ap.add_argument(
        "--resolution", type=int, default=512, help="Frame width in pixels (default 512)"
    )
    ap.add_argument("--fps", type=float, default=None, help="Override auto-fps (max 2.0)")
    ap.add_argument("--start", type=str, default=None, help="Range start (SS, MM:SS, or HH:MM:SS)")
    ap.add_argument("--end", type=str, default=None, help="Range end (SS, MM:SS, or HH:MM:SS)")
    ap.add_argument(
        "--out-dir", type=str, default=None, help="Working directory (default: new temp dir)"
    )
    ap.add_argument(
        "--no-whisper",
        action="store_true",
        help="Disable Whisper fallback. Frames-only if no native captions.",
    )
    ap.add_argument(
        "--whisper",
        choices=["groq", "openai"],
        default=None,
        help="Force a Whisper backend. Default: prefer Groq, fall back to OpenAI.",
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    args = build_parser().parse_args(argv)

    try:
        result = pipeline.run(
            args.source,
            out_dir=args.out_dir,
            max_frames=args.max_frames,
            resolution=args.resolution,
            fps_override=args.fps,
            start=args.start,
            end=args.end,
            use_whisper=not args.no_whisper,
            whisper_backend=args.whisper,
        )
    except CueKitError as exc:
        print(f"[cue-kit] error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("[cue-kit] interrupted", file=sys.stderr)
        return 130

    MODES[args.mode](result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
