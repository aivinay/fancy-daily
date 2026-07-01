from __future__ import annotations

import re
from dataclasses import dataclass


ORDERED_ITEM_RE = re.compile(r"^\d+[.)]\s+")

SECTION_ALIASES = {
    "highlights": "highlights",
    "highlight": "highlights",
    "wins": "highlights",
    "blockers": "blockers",
    "blocker": "blockers",
    "follow-ups": "follow_ups",
    "follow ups": "follow_ups",
    "followups": "follow_ups",
    "notes": "notes",
    "note": "notes",
}


@dataclass(frozen=True)
class DailyEntry:
    date: str | None
    highlights: tuple[str, ...]
    blockers: tuple[str, ...]
    follow_ups: tuple[str, ...]
    notes: tuple[str, ...]


def parse_daily_note(text: str) -> DailyEntry:
    date: str | None = None
    sections: dict[str, list[str]] = {
        "highlights": [],
        "blockers": [],
        "follow_ups": [],
        "notes": [],
    }
    current_section = "notes"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.lower().startswith("date:"):
            date = line.split(":", 1)[1].strip() or None
            continue

        normalized = line.rstrip(":").lower()
        if normalized in SECTION_ALIASES:
            current_section = SECTION_ALIASES[normalized]
            continue

        sections[current_section].append(_clean_item(line))

    return DailyEntry(
        date=date,
        highlights=tuple(sections["highlights"]),
        blockers=tuple(sections["blockers"]),
        follow_ups=tuple(sections["follow_ups"]),
        notes=tuple(sections["notes"]),
    )


def _clean_item(line: str) -> str:
    for prefix in ("- ", "* "):
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ORDERED_ITEM_RE.sub("", line, count=1).strip()
