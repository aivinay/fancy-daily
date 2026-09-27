from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date as calendar_date, datetime


ORDERED_ITEM_RE = re.compile(r"^\d+[.)]\s+")
CHECKBOX_ITEM_RE = re.compile(r"^\[[ xX]\]\s*")
DATE_LINE_RE = re.compile(
    r"^(?:#+\s+)?(?P<date>\d{4}-\d{2}-\d{2})(?P<suffix>(?:T|\s+).*)?$"
)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
BLOCKQUOTE_PREFIX_RE = re.compile(r"^(?:>\s*)+")
YAML_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:")

SECTION_ALIASES = {
    "accomplishment": "highlights",
    "accomplishments": "highlights",
    "challenge": "blockers",
    "challenges": "blockers",
    "concern": "blockers",
    "concerns": "blockers",
    "delay": "blockers",
    "delays": "blockers",
    "dependencies": "blockers",
    "dependency": "blockers",
    "decision": "notes",
    "decisions": "notes",
    "done": "highlights",
    "escalation": "blockers",
    "escalations": "blockers",
    "impediment": "blockers",
    "impediments": "blockers",
    "gratitude": "notes",
    "highlights": "highlights",
    "highlight": "highlights",
    "idea": "notes",
    "ideas": "notes",
    "obstacle": "blockers",
    "obstacles": "blockers",
    "outcome": "highlights",
    "outcomes": "highlights",
    "progress": "highlights",
    "problem": "blockers",
    "problems": "blockers",
    "question": "notes",
    "questions": "notes",
    "wins": "highlights",
    "blockers": "blockers",
    "blocker": "blockers",
    "issue": "blockers",
    "issues": "blockers",
    "learning": "notes",
    "learnings": "notes",
    "lesson": "notes",
    "lessons": "notes",
    "milestone": "highlights",
    "milestones": "highlights",
    "risk": "blockers",
    "risks": "blockers",
    "stuck": "blockers",
    "summaries": "notes",
    "summary": "notes",
    "actions": "follow_ups",
    "action items": "follow_ups",
    "follow-ups": "follow_ups",
    "follow-up": "follow_ups",
    "follow ups": "follow_ups",
    "followups": "follow_ups",
    "next action": "follow_ups",
    "next actions": "follow_ups",
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
    "retrospective": "notes",
    "retrospectives": "notes",
    "review": "notes",
    "reviews": "notes",
    "thought": "notes",
    "thoughts": "notes",
    "thanks": "notes",
}


@dataclass(frozen=True)
class DailyEntry:
    date: str | None
    highlights: tuple[str, ...]
    blockers: tuple[str, ...]
    follow_ups: tuple[str, ...]
    notes: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        return self.total_items == 0

    @property
    def total_items(self) -> int:
        return sum(self.section_counts.values())

    @property
    def section_counts(self) -> dict[str, int]:
        return {
            "highlights": len(self.highlights),
            "blockers": len(self.blockers),
            "follow_ups": len(self.follow_ups),
            "notes": len(self.notes),
        }


def parse_daily_note(text: str) -> DailyEntry:
    date: str | None = None
    sections: dict[str, list[str]] = {
        "highlights": [],
        "blockers": [],
        "follow_ups": [],
        "notes": [],
    }
    current_section = "notes"
    prepared_text = _without_yaml_front_matter(
        HTML_COMMENT_RE.sub(lambda match: "\n" * match.group().count("\n"), text)
    )

    for raw_line in prepared_text.splitlines():
        line = BLOCKQUOTE_PREFIX_RE.sub("", raw_line.strip())
        if not line:
            continue
        if _is_markdown_rule(line):
            continue

        if line.lower().startswith("date:"):
            value = line.split(":", 1)[1].strip()
            date = _parse_date_value(value)
            continue

        date_match = DATE_LINE_RE.match(line)
        if date is None and date_match:
            parsed_date = _date_from_match(date_match)
            if parsed_date is not None:
                date = parsed_date
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
    if line in {"-", "*", "+"}:
        return ""

    for prefix in ("- ", "* ", "+ "):
        if line.startswith(prefix):
            line = line[len(prefix) :].strip()
            break
    else:
        line = ORDERED_ITEM_RE.sub("", line, count=1).strip()
    return CHECKBOX_ITEM_RE.sub("", line, count=1).strip()


def _parse_date_value(value: str) -> str | None:
    normalized = value.strip()
    if (
        len(normalized) >= 2
        and normalized[0] == normalized[-1]
        and normalized[0] in {"'", '"'}
    ):
        normalized = normalized[1:-1].strip()

    date_match = DATE_LINE_RE.match(normalized)
    return _date_from_match(date_match) if date_match else None


def _date_from_match(match: re.Match[str]) -> str | None:
    value = _valid_calendar_date(match.group("date"))
    suffix = match.group("suffix") or ""
    if value is not None and suffix.startswith("T"):
        try:
            datetime.fromisoformat(value + suffix)
        except ValueError:
            return None
    return value


def _valid_calendar_date(value: str) -> str | None:
    try:
        calendar_date.fromisoformat(value)
    except ValueError:
        return None
    return value


def _append_clean_item(
    sections: dict[str, list[str]], section: str, line: str
) -> None:
    item = _clean_item(line)
    if item:
        sections[section].append(item)


def _normalize_section_name(line: str) -> str:
    return _normalize_label(line.lstrip("#"))


def _normalize_label(label: str) -> str:
    return label.strip().strip("*_`").rstrip(":").strip().strip("*_`").lower()


def _is_markdown_rule(line: str) -> bool:
    rule_chars = line.replace(" ", "")
    return (
        len(rule_chars) >= 3
        and len(set(rule_chars)) == 1
        and rule_chars[0] in {"-", "*", "_"}
    )


def _without_yaml_front_matter(text: str) -> str:
    lines = text.splitlines()
    first_content = next(
        (index for index, line in enumerate(lines) if line.strip()),
        None,
    )
    if first_content is None or lines[first_content].strip() != "---":
        return text

    closing = next(
        (
            index
            for index in range(first_content + 1, len(lines))
            if lines[index].strip() in {"---", "..."}
        ),
        None,
    )
    if closing is None:
        return text

    first_body_line = next(
        (line.strip() for line in lines[first_content + 1 : closing] if line.strip()),
        "",
    )
    if (
        not YAML_FIELD_RE.match(first_body_line)
        or _normalize_section_name(first_body_line) in SECTION_ALIASES
        or _split_inline_section(first_body_line) is not None
    ):
        return text

    date_line = next(
        (
            line.strip()
            for line in lines[first_content + 1 : closing]
            if line.strip().lower().startswith("date:")
        ),
        None,
    )
    body = lines[:first_content]
    if date_line is not None:
        body.append(date_line)
    body.extend(lines[closing + 1 :])
    return "\n".join(body)


def _split_inline_section(line: str) -> tuple[str, str] | None:
    label, separator, value = line.lstrip("#").strip().partition(":")
    if not separator or not value.strip():
        return None

    normalized = _normalize_label(label)
    if normalized not in SECTION_ALIASES:
        return None

    return SECTION_ALIASES[normalized], value.strip().lstrip("*_`").strip()
