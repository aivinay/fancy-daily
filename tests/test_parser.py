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


if __name__ == "__main__":
    unittest.main()
