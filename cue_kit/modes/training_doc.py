"""Training-doc mode: turn a recorded training video into a structured document.

Target shape:

    # <Title>

    ## Overview
    1-2 paragraph summary of what this training covers.

    ## Sections
    ### 1. <Section title>  (MM:SS – MM:SS)
    Narrative explanation of the section. Embeds frame references where the
    visual is critical (e.g. UI screenshots, diagrams).

    Steps:
    - Step 1
    - Step 2

    ## Key terms
    - **Term**: definition

This module currently emits a structured stub plus the raw transcript so a
downstream LLM (Claude in the SKILL.md flow, or a separate process) can
produce the final formatted doc. Section detection / step extraction are
on the roadmap — see slides.py for the building blocks.
"""
from __future__ import annotations

from cue_kit.frames import format_time
from cue_kit.pipeline import PipelineResult


def render(r: PipelineResult) -> None:
    info = r.info
    title = info.get("title") or r.source

    print(f"# Training doc — {title}")
    print()
    print("> _cue-kit `training-doc` mode is a scaffold._ The pipeline below produces the raw")
    print("> material (frames + timestamped transcript). Final formatting (sections, steps,")
    print("> glossary) is intended to be performed by an LLM consumer of this output.")
    print()
    print("## Source metadata")
    print()
    print(f"- Source: {r.source}")
    if info.get("uploader"):
        print(f"- Uploader: {info['uploader']}")
    print(f"- Duration: {format_time(r.full_duration)} ({r.full_duration:.1f}s)")
    print(f"- Frames extracted: {len(r.frames)} at {r.fps:.3f} fps")
    print()

    print("## Frames (visual reference)")
    print()
    print(f"Frames live at `{r.work_dir / 'frames'}`. Each is timestamped (t=MM:SS).")
    print()
    for frame in r.frames:
        print(f"- `{frame['path']}` (t={format_time(frame['timestamp_seconds'])})")
    print()

    print("## Raw transcript")
    print()
    if r.transcript_text:
        print(f"_Source: {r.transcript_source or 'captions'}._")
        print()
        print("```")
        print(r.transcript_text)
        print("```")
    else:
        print("_No transcript available — frames-only training doc is degraded but possible._")

    print()
    print("## Suggested LLM prompt")
    print()
    print("```")
    print("You are reading the raw output of cue-kit on a recorded training video.")
    print("Produce a polished training document with the following structure:")
    print()
    print("  # <Title> (preserve the source title)")
    print("  ## Overview — 1-2 paragraph summary")
    print("  ## Sections — chronological, with MM:SS-MM:SS time ranges,")
    print("                  named by the topic (not the timestamp), each with")
    print("                  a narrative explanation and bulleted steps where")
    print("                  the speaker walks through a procedure.")
    print("  ## Key terms — glossary of jargon introduced.")
    print()
    print("Cite frame timestamps when referring to on-screen content.")
    print("```")
    print()
    print("---")
    print(f"_Work dir: `{r.work_dir}` — delete when done._")
