import csv
import io
import unittest

from fancy_daily import DailyEntry, parse_daily_note, render_csv, render_markdown, render_text, render_tsv


class MarkdownRendererTests(unittest.TestCase):
    def test_indents_multiline_item_continuations(self) -> None:
        for newline in ("\n", "\r\n", "\r"):
            entry = DailyEntry(
                date=None, highlights=(), blockers=(), follow_ups=(),
                notes=(newline.join(("First line", "Second line", "", "Final line")),
                       "Next item"),
            )
            for renderer in (render_markdown, render_text):
                with self.subTest(renderer=renderer.__name__, newline=newline):
                    rendered = renderer(entry)
                    self.assertIn(
                        "- First line\n  Second line\n  \n  Final line\n- Next item\n",
                        rendered,
                    )
                    self.assertNotIn("\r", rendered)

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

    def test_renders_csv_without_header(self) -> None:
        entry = parse_daily_note("Date: 2026-09-05\nHighlights:\n- Appended clean row")

        self.assertEqual(
            render_csv(entry, include_header=False),
            "2026-09-05,highlights,1,Appended clean row\n",
        )

    def test_empty_delimited_exports_contain_no_item_rows(self) -> None:
        for source in ("", "Date: 2026-11-12"):
            entry = parse_daily_note(source)
            for render, delimiter in ((render_csv, ","), (render_tsv, "\t")):
                with self.subTest(source=source, format=render.__name__):
                    self.assertEqual(
                        render(entry),
                        delimiter.join(("date", "section", "index", "item")) + "\n",
                    )
                    self.assertEqual(render(entry, include_header=False), "")

    def test_delimited_fields_round_trip_with_line_breaks(self) -> None:
        items = (
            "First\rSecond",
            "First\nSecond",
            "First\r\nSecond",
            'Comma, tab\t and "quotes"',
        )
        entry = DailyEntry(
            date="2026-10-08", highlights=(), blockers=(), follow_ups=(), notes=items
        )
        for render, delimiter in ((render_csv, ","), (render_tsv, "\t")):
            for include_header in (True, False):
                with self.subTest(format=render.__name__, header=include_header):
                    output = render(entry, include_header=include_header)
                    rows = list(csv.reader(io.StringIO(output, newline=""), delimiter=delimiter))
                    expected = [
                        ["2026-10-08", "notes", str(index), item]
                        for index, item in enumerate(items, start=1)
                    ]
                    if include_header:
                        expected.insert(0, ["date", "section", "index", "item"])

                    self.assertEqual(rows, expected)

    def test_delimited_output_quotes_carriage_returns_with_lf_record_endings(self) -> None:
        entry = DailyEntry(
            date=None, highlights=(), blockers=(), follow_ups=(), notes=("First\rSecond",)
        )
        for render, delimiter in ((render_csv, ","), (render_tsv, "\t")):
            with self.subTest(format=render.__name__):
                expected = delimiter.join(("", "notes", "1", '"First\rSecond"')) + "\n"

                self.assertEqual(render(entry, include_header=False), expected)

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
