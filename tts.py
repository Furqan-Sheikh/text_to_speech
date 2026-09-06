#!/usr/bin/env python3
"""Natural-sounding text-to-speech CLI using Edge neural voices.

This tool is intended for transparent, disclosed synthetic narration. It does
not attempt to bypass platform AI-detection or labeling systems.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import edge_tts


DEFAULT_VOICE = "ur-PK-AsadNeural"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert text into speech.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Text to synthesize.")
    source.add_argument("--file", type=Path, help="UTF-8 text file to synthesize.")
    parser.add_argument("--output", type=Path, default=Path("speech.mp3"))
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"Voice name (default: {DEFAULT_VOICE})")
    parser.add_argument("--rate", default="+0%", help="Speaking-rate adjustment, e.g. -8%% or +5%%.")
    parser.add_argument("--pitch", default="+0Hz", help="Pitch adjustment, e.g. -2Hz or +3Hz.")
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available voices and exit. This can be used without --text/--file.",
    )
    parser.add_argument(
        "--disclosure",
        action="store_true",
        help="Append a short disclosure to a sidecar .txt file next to the audio.",
    )
    return parser.parse_args()


async def list_voices() -> None:
    voices = await edge_tts.list_voices()
    for voice in voices:
        print(f"{voice['ShortName']}\t{voice['Gender']}\t{voice['LocaleName']}")


async def synthesize(text: str, args: argparse.Namespace) -> None:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text=text,
        voice=args.voice,
        rate=args.rate,
        pitch=args.pitch,
    )
    await communicate.save(str(args.output))

    if args.disclosure:
        disclosure_path = args.output.with_suffix(".txt")
        disclosure_path.write_text(
            "This narration was generated with text-to-speech technology.\n",
            encoding="utf-8",
        )

    print(f"Wrote {args.output}")


async def main() -> None:
    args = parse_args()
    if args.list_voices:
        await list_voices()
        return

    if not args.text and not args.file:
        raise SystemExit("Provide --text or --file, or use --list-voices.")

    if args.file:
        text = args.file.read_text(encoding="utf-8").strip()
    else:
        text = args.text.strip()

    if not text:
        raise SystemExit("Input text is empty.")

    await synthesize(text, args)


if __name__ == "__main__":
    asyncio.run(main())