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

    args = parser.parse_args(argv)
    if args.command == "parse":
        payload = parse_daily_note(args.note_file.read_text(encoding="utf-8"))
        if args.format == "markdown":
            print(render_markdown(payload), end="")
        else:
            print(json.dumps(asdict(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
