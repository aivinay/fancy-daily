from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .parser import parse_daily_note
from .renderer import render_markdown


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="fancy-daily")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse = subparsers.add_parser("parse", help="Parse a daily note.")
    parse.add_argument("note_file", type=Path)
    parse.add_argument(
        "--format",
        choices=("json", "markdown"),
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
        payload = parse_daily_note(args.note_file.read_text(encoding="utf-8"))
        if args.format == "markdown":
            output = render_markdown(payload)
        else:
            output = json.dumps(asdict(payload), indent=2, sort_keys=True) + "\n"

        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")


if __name__ == "__main__":
    main()
