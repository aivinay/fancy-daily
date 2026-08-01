import unittest

from fancy_daily import parse_daily_note


class DailyParserTests(unittest.TestCase):
    def test_parses_daily_note_sections(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-06-24

            Highlights:
            - Shipped parser foundation
            - Wrote tests

            Blockers:
            - Need CLI next

            Follow-ups:
            - Add markdown output

            Notes:
            Keep the format lightweight.
            """
        )

        self.assertEqual(entry.date, "2026-06-24")
        self.assertEqual(entry.highlights, ("Shipped parser foundation", "Wrote tests"))
        self.assertEqual(entry.blockers, ("Need CLI next",))
        self.assertEqual(entry.follow_ups, ("Add markdown output",))
        self.assertEqual(entry.notes, ("Keep the format lightweight.",))

    def test_defaults_unlabeled_lines_to_notes(self) -> None:
        entry = parse_daily_note("Loose thought\n- Another note")

        self.assertEqual(entry.date, None)
        self.assertEqual(entry.notes, ("Loose thought", "Another note"))

    def test_cleans_ordered_list_items(self) -> None:
        entry = parse_daily_note(
            """
            Highlights:
            1. Added ordered list parsing
            2) Kept parser output stable
            """
        )

        self.assertEqual(
            entry.highlights,
            ("Added ordered list parsing", "Kept parser output stable"),
        )

    def test_accepts_markdown_heading_sections(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-07-03
            ## Highlights
            - Parsed markdown headings
            ### Follow-ups:
            - Document heading support
            """
        )

        self.assertEqual(entry.highlights, ("Parsed markdown headings",))
        self.assertEqual(entry.follow_ups, ("Document heading support",))

    def test_accepts_markdown_date_heading(self) -> None:
        entry = parse_daily_note(
            """
            # 2026-07-21

            ## Highlights
            - Parsed heading date
            """
        )

        self.assertEqual(entry.date, "2026-07-21")
        self.assertEqual(entry.highlights, ("Parsed heading date",))

    def test_accepts_markdown_date_heading_with_title(self) -> None:
        entry = parse_daily_note(
            """
            # 2026-07-29 Wednesday Review

            Highlights:
            - Parsed a dated heading title
            """
        )

        self.assertEqual(entry.date, "2026-07-29")
        self.assertEqual(entry.highlights, ("Parsed a dated heading title",))

    def test_accepts_plain_date_line(self) -> None:
        entry = parse_daily_note(
            """
            2026-07-22

            Highlights:
            - Parsed plain date line
            """
        )

        self.assertEqual(entry.date, "2026-07-22")
        self.assertEqual(entry.highlights, ("Parsed plain date line",))

    def test_accepts_plain_date_line_with_title(self) -> None:
        entry = parse_daily_note(
            """
            2026-07-29 Wednesday Review

            Notes:
            - Keep titled daily notes readable
            """
        )

        self.assertEqual(entry.date, "2026-07-29")
        self.assertEqual(entry.notes, ("Keep titled daily notes readable",))

    def test_accepts_date_label_with_title(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-07-31 Friday Review

            Highlights:
            - Parsed titled date label
            """
        )

        self.assertEqual(entry.date, "2026-07-31")
        self.assertEqual(entry.highlights, ("Parsed titled date label",))

    def test_cleans_checkbox_list_items(self) -> None:
        entry = parse_daily_note(
            """
            Follow-ups:
            - [ ] Write release notes
            - [x] Ship parser support
            * [X] Review summary output
            """
        )

        self.assertEqual(
            entry.follow_ups,
            ("Write release notes", "Ship parser support", "Review summary output"),
        )

    def test_ignores_empty_list_placeholders(self) -> None:
        entry = parse_daily_note(
            """
            Highlights:
            -
            - Shipped useful work
            Follow-ups:
            - [ ]
            - [ ] Send update
            Notes:
            *
            Loose note
            """
        )

        self.assertEqual(entry.highlights, ("Shipped useful work",))
        self.assertEqual(entry.follow_ups, ("Send update",))
        self.assertEqual(entry.notes, ("Loose note",))

    def test_accepts_inline_section_values(self) -> None:
        entry = parse_daily_note(
            """
            Highlights: Shipped inline labels
            Blockers: Waiting on fixture review
            Follow-ups: Document inline label support
            Notes: Keep single-line notes readable
            """
        )

        self.assertEqual(entry.highlights, ("Shipped inline labels",))
        self.assertEqual(entry.blockers, ("Waiting on fixture review",))
        self.assertEqual(entry.follow_ups, ("Document inline label support",))
        self.assertEqual(entry.notes, ("Keep single-line notes readable",))

    def test_accepts_action_oriented_follow_up_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Follow-up:
            - Send summary
            Actions: Open tracking issue
            Next steps:
            - Draft tomorrow's plan
            """
        )

        self.assertEqual(
            entry.follow_ups,
            ("Send summary", "Open tracking issue", "Draft tomorrow's plan"),
        )

    def test_accepts_task_oriented_follow_up_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Tasks:
            - Prepare demo
            To do: Update checklist
            Todos:
            - Share notes
            """
        )

        self.assertEqual(
            entry.follow_ups,
            ("Prepare demo", "Update checklist", "Share notes"),
        )

    def test_accepts_accomplishment_highlight_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Accomplishments:
            - Finished parser cleanup
            Done: Published summary
            """
        )

        self.assertEqual(
            entry.highlights,
            ("Finished parser cleanup", "Published summary"),
        )

    def test_accepts_risk_and_issue_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Risks:
            - Review window is tight
            Issue: Waiting on fixture data
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Review window is tight", "Waiting on fixture data"),
        )

    def test_accepts_reflection_and_thought_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Reflections:
            - The review loop is getting clearer
            Thought: Keep tomorrow's slice small
            """
        )

        self.assertEqual(
            entry.notes,
            ("The review loop is getting clearer", "Keep tomorrow's slice small"),
        )

    def test_accepts_learning_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Lessons:
            - Keep daily changes focused
            Learning: Parser aliases should match real note habits
            """
        )

        self.assertEqual(
            entry.notes,
            (
                "Keep daily changes focused",
                "Parser aliases should match real note habits",
            ),
        )


if __name__ == "__main__":
    unittest.main()
