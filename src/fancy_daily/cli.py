from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from . import __version__
from .parser import parse_daily_note
from .renderer import render_markdown


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="fancy-daily")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse = subparsers.add_parser("parse", help="Parse a daily note.")
    parse.add_argument("note_file", help="Path to a note file, or '-' for stdin.")
    parse.add_argument(
        "--format",
        choices=("json", "markdown", "md"),
        default="json",
        help="Output format.",
    )
    parse.add_argument(
        "--output",
        type=Path,
        help="Write output to a file instead of stdout.",
    )

    args = parser.parse_args(argv)
    if args.command == "parse":
        note_text = (
            sys.stdin.read()
            if args.note_file == "-"
            else Path(args.note_file).read_text(encoding="utf-8")
        )
        payload = parse_daily_note(note_text)
        if args.format in {"markdown", "md"}:
            output = render_markdown(payload)
        else:
            output = json.dumps(asdict(payload), indent=2, sort_keys=True) + "\n"

        if args.output and str(args.output) != "-":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")


if __name__ == "__main__":
    main()
