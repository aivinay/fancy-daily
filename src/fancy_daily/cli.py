from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from . import __version__
from .parser import parse_daily_note
from .renderer import render_csv, render_markdown, render_text, render_tsv


SECTION_NAMES = ("highlights", "blockers", "follow_ups", "notes")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="fancy-daily")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse = subparsers.add_parser("parse", help="Parse a daily note.")
    parse.add_argument(
        "note_file",
        nargs="?",
        default="-",
        help="Path to a note file, or '-' for stdin.",
    )
    parse.add_argument(
        "--format",
        choices=(
            "json",
            "pretty-json",
            "pretty",
            "compact-json",
            "compact",
            "csv",
            "markdown",
            "md",
            "text",
            "txt",
            "plain",
            "tsv",
        ),
        default="json",
        help="Output format.",
    )
    parse.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write output to a file instead of stdout.",
    )
    parse.add_argument(
        "--no-header",
        action="store_true",
        help="Omit the header row for csv and tsv output.",
    )
    parse.add_argument(
        "--require-date",
        action="store_true",
        help="Fail when the note does not include a parseable date.",
    )
    parse.add_argument(
        "--require-entry",
        action="store_true",
        help="Fail when the note does not include any parsed entries.",
    )
    parse.add_argument(
        "--strict",
        action="store_true",
        help="Fail when the note is missing a date or parsed entries.",
    )
    parse.add_argument(
        "--require-section",
        action="append",
        choices=SECTION_NAMES,
        default=[],
        help="Fail when a required section has no parsed entries.",
    )

    args = parser.parse_args(argv)
    if args.command == "parse":
        note_text = _read_note_text(args.note_file, parser)
        payload = parse_daily_note(note_text)
        if (args.require_date or args.strict) and payload.date is None:
            parser.error("daily note is missing a date")
        if (args.require_entry or args.strict) and payload.is_empty:
            parser.error("daily note has no parsed entries")
        for section in args.require_section:
            if not getattr(payload, section):
                parser.error(f"daily note is missing required section: {section}")
        if args.format in {"markdown", "md"}:
            output = render_markdown(payload)
        elif args.format in {"text", "txt", "plain"}:
            output = render_text(payload)
        elif args.format == "csv":
            output = render_csv(payload, include_header=not args.no_header)
        elif args.format == "tsv":
            output = render_tsv(payload, include_header=not args.no_header)
        elif args.format in {"compact-json", "compact"}:
            output = json.dumps(asdict(payload), sort_keys=True) + "\n"
        else:
            output = json.dumps(asdict(payload), indent=2, sort_keys=True) + "\n"

        if args.output and str(args.output) != "-":
            _write_output(args.output, output, parser)
        else:
            print(output, end="")


def _read_note_text(note_file: str, parser: argparse.ArgumentParser) -> str:
    if note_file == "-":
        return sys.stdin.read()

    try:
        return Path(note_file).read_text(encoding="utf-8")
    except OSError as exc:
        parser.error(f"unable to read note file: {exc}")


def _write_output(
    output_path: Path, output: str, parser: argparse.ArgumentParser
) -> None:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    except OSError as exc:
        parser.error(f"unable to write output file: {exc}")


if __name__ == "__main__":
    main()
