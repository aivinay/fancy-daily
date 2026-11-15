from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from . import __version__
from .parser import DailyEntry, parse_daily_note
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
            "stats-json",
            "stats",
            "compact-stats-json",
            "compact-stats",
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
        help="Write UTF-8 output to a file; '-' selects stdout (the default).",
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
    parse.add_argument(
        "--min-items",
        type=int,
        default=0,
        help="Fail when fewer than this many entries are parsed.",
    )
    parse.add_argument(
        "--max-items",
        type=int,
        help="Fail when more than this many entries are parsed.",
    )

    args = parser.parse_args(argv)
    if args.command == "parse":
        if args.min_items < 0:
            parser.error("--min-items must be zero or greater")
        if args.max_items is not None:
            if args.max_items < 0:
                parser.error("--max-items must be zero or greater")
            if args.min_items > args.max_items:
                parser.error("--min-items cannot exceed --max-items")
        if args.no_header and args.format not in {"csv", "tsv"}:
            parser.error("--no-header requires --format csv or tsv")

        note_text = _read_note_text(args.note_file, parser)
        payload = parse_daily_note(note_text)
        if (args.require_date or args.strict) and payload.date is None:
            parser.error("daily note is missing a date")
        if (args.require_entry or args.strict) and payload.is_empty:
            parser.error("daily note has no parsed entries")
        if payload.total_items < args.min_items:
            parser.error(
                f"daily note has {payload.total_items} parsed entries; "
                f"expected at least {args.min_items}"
            )
        if args.max_items is not None and payload.total_items > args.max_items:
            parser.error(
                f"daily note has {payload.total_items} parsed entries; "
                f"expected at most {args.max_items}"
            )
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
        elif args.format in {"stats-json", "stats"}:
            output = json.dumps(_entry_stats(payload), indent=2, sort_keys=True) + "\n"
        elif args.format in {"compact-stats-json", "compact-stats"}:
            output = json.dumps(_entry_stats(payload), sort_keys=True) + "\n"
        elif args.format in {"compact-json", "compact"}:
            output = json.dumps(asdict(payload), sort_keys=True) + "\n"
        else:
            output = json.dumps(asdict(payload), indent=2, sort_keys=True) + "\n"

        if args.output is not None and args.output != "-":
            _write_output(Path(args.output), output, parser)
        else:
            try:
                print(output, end="")
            except UnicodeEncodeError as exc:
                parser.error(
                    f"unable to encode stdout using {exc.encoding}: {exc.reason}; "
                    "use --output for a UTF-8 file"
                )
            except OSError as exc:
                parser.error(f"unable to write stdout: {exc}")


def _entry_stats(entry: DailyEntry) -> dict[str, object]:
    return {
        "date": entry.date,
        "is_empty": entry.is_empty,
        "section_counts": entry.section_counts,
        "total_items": entry.total_items,
    }


def _read_note_text(note_file: str, parser: argparse.ArgumentParser) -> str:
    try:
        if note_file == "-":
            text = sys.stdin.read()
            # Stdin's surrogateescape mode can preserve undecodable input bytes.
            text.encode("utf-8")
            return text
        return Path(note_file).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        source = "stdin" if note_file == "-" else f"note file {note_file!r}"
        parser.error(f"unable to decode {source} using {exc.encoding}: {exc.reason}")
    except UnicodeEncodeError:
        parser.error("unable to decode stdin: input contains invalid Unicode characters")
    except (OSError, ValueError) as exc:
        source = "stdin" if note_file == "-" else "note file"
        parser.error(f"unable to read {source}: {exc}")


def _write_output(
    output_path: Path, output: str, parser: argparse.ArgumentParser
) -> None:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.error(f"unable to write output file: {exc}")


if __name__ == "__main__":
    main()
