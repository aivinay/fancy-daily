import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
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


if __name__ == "__main__":
    unittest.main()
