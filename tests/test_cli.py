import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from fancy_daily.cli import main


class CliTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
