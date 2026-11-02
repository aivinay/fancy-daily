from __future__ import annotations

import csv
import io

from .parser import DailyEntry


def render_csv(entry: DailyEntry, *, include_header: bool = True) -> str:
    return _render_delimited(entry, delimiter=",", include_header=include_header)


def render_tsv(entry: DailyEntry, *, include_header: bool = True) -> str:
    return _render_delimited(entry, delimiter="\t", include_header=include_header)


def _render_delimited(
    entry: DailyEntry, delimiter: str, *, include_header: bool
) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\r\n")

    def write_row(row: tuple[object, ...]) -> None:
        writer.writerow(row)
        # CRLF enables quoting for both line breaks; shorten only the record ending.
        output.seek(output.tell() - 2)
        output.truncate()
        output.write("\n")

    if include_header:
        write_row(("date", "section", "index", "item"))

    for section, items in (
        ("highlights", entry.highlights),
        ("blockers", entry.blockers),
        ("follow_ups", entry.follow_ups),
        ("notes", entry.notes),
    ):
        for index, item in enumerate(items, start=1):
            write_row((entry.date or "", section, index, item))

    return output.getvalue()


def render_markdown(entry: DailyEntry) -> str:
    lines: list[str] = []
    title = entry.date or "Daily Summary"
    lines.append(f"# {title}")
    lines.append("")

    if entry.is_empty:
        lines.append("_No entries recorded._")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    _append_section(lines, "Highlights", entry.highlights)
    _append_section(lines, "Blockers", entry.blockers)
    _append_section(lines, "Follow-ups", entry.follow_ups)
    _append_section(lines, "Notes", entry.notes)

    return "\n".join(lines).rstrip() + "\n"


def render_text(entry: DailyEntry) -> str:
    lines: list[str] = []
    title = entry.date or "Daily Summary"
    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")

    if entry.is_empty:
        lines.append("No entries recorded.")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    _append_text_section(lines, "Highlights", entry.highlights)
    _append_text_section(lines, "Blockers", entry.blockers)
    _append_text_section(lines, "Follow-ups", entry.follow_ups)
    _append_text_section(lines, "Notes", entry.notes)

    return "\n".join(lines).rstrip() + "\n"


def _append_section(lines: list[str], title: str, items: tuple[str, ...]) -> None:
    if not items:
        return

    lines.append(f"## {title}")
    for item in items:
        lines.append("- " + item.replace("\n", "\n  "))
    lines.append("")


def _append_text_section(lines: list[str], title: str, items: tuple[str, ...]) -> None:
    if not items:
        return

    lines.append(f"{title}:")
    for item in items:
        lines.append("- " + item.replace("\n", "\n  "))
    lines.append("")
