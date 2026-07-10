import unittest
from pathlib import Path

from fancy_daily import parse_daily_note


class ExampleNoteTests(unittest.TestCase):
    def test_daily_note_example_parses_supported_patterns(self) -> None:
        root = Path(__file__).resolve().parents[1]
        example = root / "examples" / "daily-note.txt"

        entry = parse_daily_note(example.read_text(encoding="utf-8"))

        self.assertEqual(entry.date, "2026-07-09")
        self.assertEqual(
            entry.highlights,
            ("Parsed inline section labels", "Documented supported note formats"),
        )
        self.assertEqual(entry.blockers, ("Waiting on weekly review notes",))
        self.assertEqual(
            entry.follow_ups,
            (
                "Add a richer weekly summary example",
                "Try markdown output with this example",
                "Keep the parser format readable by hand",
            ),
        )
        self.assertEqual(
            entry.notes,
            ("This example uses the same plain-text conventions supported by the parser.",),
        )


if __name__ == "__main__":
    unittest.main()
