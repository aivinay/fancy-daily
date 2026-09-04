import unittest

from fancy_daily import parse_daily_note, render_csv, render_markdown, render_text, render_tsv


class MarkdownRendererTests(unittest.TestCase):
    def test_renders_populated_sections(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-06-27
            Highlights:
            - Added markdown output
            Blockers:
            - None
            Follow-ups:
            - Wire this into the CLI
            """
        )

        self.assertEqual(
            render_markdown(entry),
            "\n".join(
                [
                    "# 2026-06-27",
                    "",
                    "## Highlights",
                    "- Added markdown output",
                    "",
                    "## Blockers",
                    "- None",
                    "",
                    "## Follow-ups",
                    "- Wire this into the CLI",
                    "",
                ]
            ),
        )

    def test_uses_default_title_without_date(self) -> None:
        entry = parse_daily_note("Notes:\n- Keep it simple")

        self.assertTrue(render_markdown(entry).startswith("# Daily Summary\n"))

    def test_renders_empty_state_without_sections(self) -> None:
        entry = parse_daily_note("")

        self.assertEqual(render_markdown(entry), "# Daily Summary\n\n_No entries recorded._\n")

    def test_renders_plain_text_summary(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-08-05
            Highlights:
            - Added text output
            Notes:
            - Keep terminal output readable
            """
        )

        self.assertEqual(
            render_text(entry),
            "\n".join(
                [
                    "2026-08-05",
                    "==========",
                    "",
                    "Highlights:",
                    "- Added text output",
                    "",
                    "Notes:",
                    "- Keep terminal output readable",
                    "",
                ]
            ),
        )

    def test_renders_plain_text_empty_state(self) -> None:
        entry = parse_daily_note("")

        self.assertEqual(render_text(entry), "Daily Summary\n=============\n\nNo entries recorded.\n")

    def test_renders_csv_section_rows(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-09-03
            Highlights:
            - Shipped CSV output
            Blockers:
            - Waiting on review, still
            Follow-ups:
            - Share summary
            Notes:
            - Kept rows spreadsheet-friendly
            """
        )

        self.assertEqual(
            render_csv(entry),
            "\n".join(
                [
                    "date,section,index,item",
                    "2026-09-03,highlights,1,Shipped CSV output",
                    '2026-09-03,blockers,1,"Waiting on review, still"',
                    "2026-09-03,follow_ups,1,Share summary",
                    "2026-09-03,notes,1,Kept rows spreadsheet-friendly",
                    "",
                ]
            ),
        )

    def test_renders_tsv_section_rows(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-09-04
            Highlights:
            - Added tab output
            Notes:
            - Keeps comma-heavy notes readable
            """
        )

        self.assertEqual(
            render_tsv(entry),
            "\n".join(
                [
                    "date\tsection\tindex\titem",
                    "2026-09-04\thighlights\t1\tAdded tab output",
                    "2026-09-04\tnotes\t1\tKeeps comma-heavy notes readable",
                    "",
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
