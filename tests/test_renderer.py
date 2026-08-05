import unittest

from fancy_daily import parse_daily_note, render_markdown, render_text


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


if __name__ == "__main__":
    unittest.main()
