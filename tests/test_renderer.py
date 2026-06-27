import unittest

from fancy_daily import parse_daily_note, render_markdown


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


if __name__ == "__main__":
    unittest.main()
