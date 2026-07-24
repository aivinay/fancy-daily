from __future__ import annotations

import re
from dataclasses import dataclass


ORDERED_ITEM_RE = re.compile(r"^\d+[.)]\s+")
CHECKBOX_ITEM_RE = re.compile(r"^\[[ xX]\]\s*")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_HEADING_RE = re.compile(r"^#+\s+\d{4}-\d{2}-\d{2}\s*$")

SECTION_ALIASES = {
    "accomplishment": "highlights",
    "accomplishments": "highlights",
    "done": "highlights",
    "highlights": "highlights",
    "highlight": "highlights",
    "wins": "highlights",
    "blockers": "blockers",
    "blocker": "blockers",
    "issue": "blockers",
    "issues": "blockers",
    "risk": "blockers",
    "risks": "blockers",
    "actions": "follow_ups",
    "action items": "follow_ups",
    "follow-ups": "follow_ups",
    "follow-up": "follow_ups",
    "follow ups": "follow_ups",
    "followups": "follow_ups",
    "next steps": "follow_ups",
    "task": "follow_ups",
    "tasks": "follow_ups",
    "to do": "follow_ups",
    "todo": "follow_ups",
    "todos": "follow_ups",
    "notes": "notes",
    "note": "notes",
    "reflection": "notes",
    "reflections": "notes",
    "thought": "notes",
    "thoughts": "notes",
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

        if date is None and DATE_ONLY_RE.match(line):
            date = line
            continue

        if date is None and DATE_HEADING_RE.match(line):
            date = line.lstrip("#").strip()
            continue

        inline_section = _split_inline_section(line)
        if inline_section is not None:
            current_section, value = inline_section
            _append_clean_item(sections, current_section, value)
            continue

        normalized = _normalize_section_name(line)
        if normalized in SECTION_ALIASES:
            current_section = SECTION_ALIASES[normalized]
            continue

        _append_clean_item(sections, current_section, line)

    return DailyEntry(
        date=date,
        highlights=tuple(sections["highlights"]),
        blockers=tuple(sections["blockers"]),
        follow_ups=tuple(sections["follow_ups"]),
        notes=tuple(sections["notes"]),
    )


def _clean_item(line: str) -> str:
    if line in {"-", "*"}:
        return ""

    for prefix in ("- ", "* "):
        if line.startswith(prefix):
            line = line[len(prefix) :].strip()
            break
    else:
        line = ORDERED_ITEM_RE.sub("", line, count=1).strip()
    return CHECKBOX_ITEM_RE.sub("", line, count=1).strip()


def _append_clean_item(
    sections: dict[str, list[str]], section: str, line: str
) -> None:
    item = _clean_item(line)
    if item:
        sections[section].append(item)


def _normalize_section_name(line: str) -> str:
    return line.lstrip("#").strip().rstrip(":").lower()


def _split_inline_section(line: str) -> tuple[str, str] | None:
    label, separator, value = line.lstrip("#").strip().partition(":")
    if not separator or not value.strip():
        return None

    normalized = label.strip().lower()
    if normalized not in SECTION_ALIASES:
        return None

    return SECTION_ALIASES[normalized], value.strip()
