from __future__ import annotations

from .parser import DailyEntry


def render_markdown(entry: DailyEntry) -> str:
    lines: list[str] = []
    title = entry.date or "Daily Summary"
    lines.append(f"# {title}")
    lines.append("")

    if not any((entry.highlights, entry.blockers, entry.follow_ups, entry.notes)):
        lines.append("_No entries recorded._")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    _append_section(lines, "Highlights", entry.highlights)
    _append_section(lines, "Blockers", entry.blockers)
    _append_section(lines, "Follow-ups", entry.follow_ups)
    _append_section(lines, "Notes", entry.notes)

    return "\n".join(lines).rstrip() + "\n"


def _append_section(lines: list[str], title: str, items: tuple[str, ...]) -> None:
    if not items:
        return

    lines.append(f"## {title}")
    for item in items:
        lines.append(f"- {item}")
    lines.append("")
