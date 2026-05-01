"""cue-kit CLI: parse args, dispatch to a mode renderer."""
from __future__ import annotations

import argparse

from cue_kit import pipeline
from cue_kit.modes import lecture_notes, summary, training_doc, transcript


MODES = {
    "summary": summary.render,
    "transcript": transcript.render,
    "training-doc": training_doc.render,
    "lecture-notes": lecture_notes.render,
}


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="cue-kit",
        description="Turn a video into structured text — summary, transcript, training doc, or lecture notes.",
    )
    ap.add_argument("source", help="Video URL or local file path")
    ap.add_argument(
        "--mode",
        choices=list(MODES.keys()),
        default="summary",
        help="Output shape (default: summary)",
    )
    ap.add_argument("--max-frames", type=int, default=80, help="Cap on frame count (default 80, hard max 100)")
    ap.add_argument("--resolution", type=int, default=512, help="Frame width in pixels (default 512)")
    ap.add_argument("--fps", type=float, default=None, help="Override auto-fps")
    ap.add_argument("--start", type=str, default=None, help="Range start (SS, MM:SS, or HH:MM:SS)")
    ap.add_argument("--end", type=str, default=None, help="Range end (SS, MM:SS, or HH:MM:SS)")
    ap.add_argument("--out-dir", type=str, default=None, help="Working directory (default: tmp)")
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
    args = ap.parse_args()

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

    render = MODES[args.mode]
    render(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
