import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from fancy_daily.cli import main


class CliTests(unittest.TestCase):
    def test_parse_command_outputs_version(self) -> None:
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stdout(stdout):
            main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stdout.getvalue(), "fancy-daily 0.1.0\n")

    def test_parse_command_outputs_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-06-25",
                        "Highlights:",
                        "- Added CLI",
                        "Follow-ups:",
                        "- Add markdown rendering",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", str(note)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-06-25")
        self.assertEqual(payload["highlights"], ["Added CLI"])
        self.assertEqual(payload["follow_ups"], ["Add markdown rendering"])

    def test_parse_command_accepts_pretty_json_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-08-17",
                        "Highlights:",
                        "- Used explicit pretty JSON output",
                    ]
                ),
                encoding="utf-8",
            )

            outputs: list[str] = []
            for output_format in ("pretty-json", "pretty"):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    main(["parse", "--format", output_format, str(note)])
                outputs.append(stdout.getvalue())

        self.assertEqual(outputs[0], outputs[1])
        self.assertIn('\n  "date": "2026-08-17"', outputs[0])
        payload = json.loads(outputs[0])
        self.assertEqual(payload["highlights"], ["Used explicit pretty JSON output"])

    def test_parse_command_reads_stdin_for_dash_path(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO(
            "\n".join(
                [
                    "Date: 2026-07-23",
                    "Highlights:",
                    "- Parsed piped input",
                ]
            )
        )

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "-"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-07-23")
        self.assertEqual(payload["highlights"], ["Parsed piped input"])

    def test_parse_command_reads_stdin_without_path(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO(
            "\n".join(
                [
                    "Date: 2026-07-28",
                    "Highlights:",
                    "- Parsed implicit stdin",
                ]
            )
        )

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-07-28")
        self.assertEqual(payload["highlights"], ["Parsed implicit stdin"])

    def test_parse_command_reports_missing_input_file(self) -> None:
        stderr = io.StringIO()
        missing = "missing-daily-note.txt"

        with self.assertRaises(SystemExit) as raised, redirect_stderr(stderr):
            main(["parse", missing])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("unable to read note file:", stderr.getvalue())
        self.assertIn(missing, stderr.getvalue())

    def test_parse_command_reports_invalid_utf8_file_without_changing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            output = Path(tmpdir) / "summary.json"
            note.write_bytes(b"Notes:\n- Invalid byte: \xff")
            output.write_text("previous summary\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                self.assertRaises(SystemExit) as raised,
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                main(["parse", str(note), "--output", str(output)])

            self.assertEqual(output.read_text(encoding="utf-8"), "previous summary\n")

        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("unable to decode note file", stderr.getvalue())
        self.assertIn(str(note), stderr.getvalue())
        self.assertIn("utf-8", stderr.getvalue())

    def test_parse_command_reports_stdin_decoding_errors(self) -> None:
        for arguments in (["parse"], ["parse", "-"]):
            with self.subTest(arguments=arguments):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with (
                    io.TextIOWrapper(io.BytesIO(b"Notes:\n- \xff"), encoding="utf-8") as stdin,
                    patch("sys.stdin", stdin),
                    self.assertRaises(SystemExit) as raised,
                    redirect_stdout(stdout),
                    redirect_stderr(stderr),
                ):
                    main(arguments)

                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(stdout.getvalue(), "")
                self.assertIn("unable to decode stdin", stderr.getvalue())
                self.assertIn("utf-8", stderr.getvalue())

    def test_parse_command_reports_stdin_read_errors(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch("sys.stdin.read", side_effect=OSError("input stream unavailable")),
            self.assertRaises(SystemExit) as raised,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            main(["parse", "-"])

        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("unable to read stdin: input stream unavailable", stderr.getvalue())

    def test_parse_command_preserves_utf8_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text("Notes:\n- Caf\u00e9 review", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", str(note)])

        self.assertEqual(json.loads(stdout.getvalue())["notes"], ["Caf\u00e9 review"])

    def test_parse_command_requires_date_when_requested(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Highlights:\n- Missing a date")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--require-date"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("daily note is missing a date", stderr.getvalue())

    def test_parse_command_rejects_invalid_date_when_required(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Date: 2026-02-30\nHighlights:\n- Has content")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--require-date"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("daily note is missing a date", stderr.getvalue())

    def test_parse_command_accepts_required_date(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-09\nHighlights:\n- Has a date")

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "--require-date"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-09-09")
        self.assertEqual(payload["highlights"], ["Has a date"])

    def test_parse_command_requires_entry_when_requested(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-10")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--require-entry"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("daily note has no parsed entries", stderr.getvalue())

    def test_parse_command_accepts_required_entry(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-10\nNotes:\n- Has content")

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "--require-entry"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-09-10")
        self.assertEqual(payload["notes"], ["Has content"])

    def test_parse_command_strict_requires_date(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Highlights:\n- Missing a date")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--strict"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("daily note is missing a date", stderr.getvalue())

    def test_parse_command_strict_requires_entry(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-12")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--strict"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("daily note has no parsed entries", stderr.getvalue())

    def test_parse_command_accepts_strict_note(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-12\nHighlights:\n- Has content")

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "--strict"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-09-12")
        self.assertEqual(payload["highlights"], ["Has content"])

    def test_parse_command_requires_specific_section(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-11\nNotes:\n- Has content")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--require-section", "highlights"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn(
            "daily note is missing required section: highlights",
            stderr.getvalue(),
        )

    def test_parse_command_accepts_required_sections(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO(
            "\n".join(
                [
                    "Date: 2026-09-11",
                    "Highlights:",
                    "- Has a win",
                    "Follow-ups:",
                    "- Has next step",
                ]
            )
        )

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(
                [
                    "parse",
                    "--require-section",
                    "highlights",
                    "--require-section",
                    "follow_ups",
                ]
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["highlights"], ["Has a win"])
        self.assertEqual(payload["follow_ups"], ["Has next step"])

    def test_parse_command_requires_minimum_items(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-13\nHighlights:\n- One item")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--min-items", "2"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn(
            "daily note has 1 parsed entries; expected at least 2",
            stderr.getvalue(),
        )

    def test_parse_command_rejects_negative_minimum_items(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-13\nHighlights:\n- One item")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--min-items", "-1"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--min-items must be zero or greater", stderr.getvalue())

    def test_parse_command_accepts_minimum_items(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO(
            "\n".join(
                [
                    "Date: 2026-09-13",
                    "Highlights:",
                    "- First item",
                    "Notes:",
                    "- Second item",
                ]
            )
        )

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "--min-items", "2"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["highlights"], ["First item"])
        self.assertEqual(payload["notes"], ["Second item"])

    def test_parse_command_requires_maximum_items(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO(
            "Date: 2026-09-22\nHighlights:\n- First item\n- Second item"
        )

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--max-items", "1"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn(
            "daily note has 2 parsed entries; expected at most 1",
            stderr.getvalue(),
        )

    def test_parse_command_rejects_negative_maximum_items(self) -> None:
        stderr = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-22")

        with (
            patch("sys.stdin", stdin),
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--max-items", "-1"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--max-items must be zero or greater", stderr.getvalue())

    def test_parse_command_rejects_conflicting_item_limits_before_reading(self) -> None:
        stderr = io.StringIO()

        with (
            patch("sys.stdin") as stdin,
            self.assertRaises(SystemExit) as raised,
            redirect_stderr(stderr),
        ):
            main(["parse", "--min-items", "3", "--max-items", "1"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--min-items cannot exceed --max-items", stderr.getvalue())
        stdin.read.assert_not_called()

    def test_parse_command_accepts_maximum_items(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-22\nNotes:\n- One item")

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "--max-items", "1"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["notes"], ["One item"])

    def test_parse_command_outputs_empty_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text("Date: 2026-07-14\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", str(note)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            payload,
            {
                "date": "2026-07-14",
                "blockers": [],
                "follow_ups": [],
                "highlights": [],
                "notes": [],
            },
        )

    def test_parse_command_outputs_markdown_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-06-28",
                        "Highlights:",
                        "- Wired markdown output",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "markdown", str(note)])

        self.assertIn("# 2026-06-28", stdout.getvalue())
        self.assertIn("- Wired markdown output", stdout.getvalue())

    def test_parse_command_accepts_md_format_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-07-26",
                        "Highlights:",
                        "- Used short markdown alias",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "md", str(note)])

        self.assertIn("# 2026-07-26", stdout.getvalue())
        self.assertIn("- Used short markdown alias", stdout.getvalue())

    def test_parse_command_outputs_text_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-08-05",
                        "Highlights:",
                        "- Rendered plain text",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "text", str(note)])

        self.assertEqual(
            stdout.getvalue(),
            "2026-08-05\n==========\n\nHighlights:\n- Rendered plain text\n",
        )

    def test_parse_command_outputs_csv_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-09-03",
                        "Highlights:",
                        "- Exported CSV rows",
                        "Notes:",
                        "- Includes commas, safely",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "csv", str(note)])

        self.assertEqual(
            stdout.getvalue(),
            "\n".join(
                [
                    "date,section,index,item",
                    "2026-09-03,highlights,1,Exported CSV rows",
                    '2026-09-03,notes,1,"Includes commas, safely"',
                    "",
                ]
            ),
        )

    def test_parse_command_outputs_tsv_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-09-04",
                        "Highlights:",
                        "- Exported TSV rows",
                        "Follow-ups:",
                        "- Paste into spreadsheet",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "tsv", str(note)])

        self.assertEqual(
            stdout.getvalue(),
            "\n".join(
                [
                    "date\tsection\tindex\titem",
                    "2026-09-04\thighlights\t1\tExported TSV rows",
                    "2026-09-04\tfollow_ups\t1\tPaste into spreadsheet",
                    "",
                ]
            ),
        )

    def test_parse_command_outputs_stats_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-09-14",
                        "Highlights:",
                        "- Added stats output",
                        "Blockers:",
                        "- Waiting on review",
                        "Notes:",
                        "- Counted sections",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "stats-json", str(note)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            payload,
            {
                "date": "2026-09-14",
                "is_empty": False,
                "section_counts": {
                    "blockers": 1,
                    "follow_ups": 0,
                    "highlights": 1,
                    "notes": 1,
                },
                "total_items": 3,
            },
        )

    def test_parse_command_outputs_empty_stats_alias(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-14")

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "--format", "stats"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-09-14")
        self.assertTrue(payload["is_empty"])
        self.assertEqual(payload["total_items"], 0)
        self.assertEqual(
            payload["section_counts"],
            {
                "blockers": 0,
                "follow_ups": 0,
                "highlights": 0,
                "notes": 0,
            },
        )

    def test_parse_command_outputs_compact_stats_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-09-15",
                        "Highlights:",
                        "- Added compact stats output",
                        "Follow-ups:",
                        "- Wire into nightly summary",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "compact-stats-json", str(note)])

        self.assertEqual(
            stdout.getvalue(),
            (
                '{"date": "2026-09-15", "is_empty": false, '
                '"section_counts": {"blockers": 0, "follow_ups": 1, '
                '"highlights": 1, "notes": 0}, "total_items": 2}\n'
            ),
        )

    def test_parse_command_accepts_compact_stats_alias(self) -> None:
        stdout = io.StringIO()
        stdin = io.StringIO("Date: 2026-09-15\nNotes:\n- Count this")

        with patch("sys.stdin", stdin), redirect_stdout(stdout):
            main(["parse", "--format", "compact-stats"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-09-15")
        self.assertEqual(payload["section_counts"]["notes"], 1)
        self.assertEqual(payload["total_items"], 1)

    def test_parse_command_omits_delimited_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-09-05",
                        "Highlights:",
                        "- Appended one CSV row",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "csv", "--no-header", str(note)])

        self.assertEqual(
            stdout.getvalue(),
            "2026-09-05,highlights,1,Appended one CSV row\n",
        )

    def test_parse_command_accepts_text_format_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-08-06",
                        "Notes:",
                        "- Used a text alias",
                    ]
                ),
                encoding="utf-8",
            )

            outputs: list[str] = []
            for output_format in ("txt", "plain"):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    main(["parse", "--format", output_format, str(note)])
                outputs.append(stdout.getvalue())

        self.assertEqual(
            outputs,
            [
                "2026-08-06\n==========\n\nNotes:\n- Used a text alias\n",
                "2026-08-06\n==========\n\nNotes:\n- Used a text alias\n",
            ],
        )

    def test_parse_command_outputs_compact_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-07-30",
                        "Highlights:",
                        "- Used compact JSON output",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "compact-json", str(note)])

        self.assertEqual(
            stdout.getvalue(),
            (
                '{"blockers": [], "date": "2026-07-30", "follow_ups": [], '
                '"highlights": ["Used compact JSON output"], "notes": []}\n'
            ),
        )

    def test_parse_command_accepts_compact_format_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-08-07",
                        "Highlights:",
                        "- Used compact alias",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "compact", str(note)])

        self.assertEqual(
            stdout.getvalue(),
            (
                '{"blockers": [], "date": "2026-08-07", "follow_ups": [], '
                '"highlights": ["Used compact alias"], "notes": []}\n'
            ),
        )

    def test_parse_command_outputs_empty_markdown_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "daily.txt"
            note.write_text("Date: 2026-07-12\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--format", "markdown", str(note)])

        self.assertEqual(stdout.getvalue(), "# 2026-07-12\n\n_No entries recorded._\n")

    def test_parse_command_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            note = root / "daily.txt"
            output = root / "summary.md"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-06-29",
                        "Highlights:",
                        "- Added file output",
                    ]
                ),
                encoding="utf-8",
            )

            main(["parse", "--format", "markdown", "--output", str(output), str(note)])

            rendered = output.read_text(encoding="utf-8")

        self.assertIn("# 2026-06-29", rendered)
        self.assertIn("- Added file output", rendered)

    def test_parse_command_accepts_short_output_option(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            note = root / "daily.txt"
            output = root / "summary.json"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-07-27",
                        "Highlights:",
                        "- Used short output option",
                    ]
                ),
                encoding="utf-8",
            )

            main(["parse", "-o", str(output), str(note)])

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["date"], "2026-07-27")
        self.assertEqual(payload["highlights"], ["Used short output option"])

    def test_parse_command_treats_dash_output_as_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            note = root / "daily.txt"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-07-25",
                        "Highlights:",
                        "- Kept output on stdout",
                    ]
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["parse", "--output", "-", str(note)])

            dash_file = root / "-"

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["date"], "2026-07-25")
        self.assertEqual(payload["highlights"], ["Kept output on stdout"])
        self.assertFalse(dash_file.exists())

    def test_parse_command_writes_json_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            note = root / "daily.txt"
            output = root / "summary.json"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-07-15",
                        "Blockers:",
                        "- Waiting on review",
                    ]
                ),
                encoding="utf-8",
            )

            main(["parse", "--output", str(output), str(note)])

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["date"], "2026-07-15")
        self.assertEqual(payload["blockers"], ["Waiting on review"])
        self.assertEqual(payload["highlights"], [])

    def test_parse_command_creates_output_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            note = root / "daily.txt"
            output = root / "reports" / "daily" / "summary.md"
            note.write_text(
                "\n".join(
                    [
                        "Date: 2026-06-30",
                        "Highlights:",
                        "- Created nested output directories",
                    ]
                ),
                encoding="utf-8",
            )

            main(["parse", "--format", "markdown", "--output", str(output), str(note)])

            rendered = output.read_text(encoding="utf-8")

        self.assertIn("# 2026-06-30", rendered)
        self.assertIn("- Created nested output directories", rendered)

    def test_parse_command_reports_output_write_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            note = root / "daily.txt"
            note.write_text("Date: 2026-09-01\n", encoding="utf-8")

            stderr = io.StringIO()
            with self.assertRaises(SystemExit) as raised, redirect_stderr(stderr):
                main(["parse", "--output", str(root), str(note)])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("unable to write output file:", stderr.getvalue())
        self.assertIn(str(root), stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
