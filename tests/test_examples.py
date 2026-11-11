import unittest
from pathlib import Path

from fancy_daily import parse_daily_note, render_markdown


class ExampleNoteTests(unittest.TestCase):
    def test_examples_round_trip_through_markdown(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for filename in ("daily-note.txt", "daily-note.md"):
            with self.subTest(filename=filename):
                original = parse_daily_note(
                    (root / "examples" / filename).read_text(encoding="utf-8")
                )
                rendered = render_markdown(original)

                self.assertEqual(parse_daily_note(rendered), original)
                self.assertEqual(render_markdown(parse_daily_note(rendered)), rendered)

    def test_markdown_example_excludes_template_guidance(self) -> None:
        root = Path(__file__).resolve().parents[1]
        entry = parse_daily_note(
            (root / "examples" / "daily-note.md").read_text(encoding="utf-8")
        )

        self.assertEqual(entry.date, "2026-10-28")
        self.assertEqual(
            entry.highlights,
            ("Shipped the release checklist", "Verified the installed CLI"),
        )
        self.assertEqual(entry.blockers, ())
        self.assertEqual(
            entry.follow_ups,
            ("Share the release summary", "Confirm tomorrow's review owner"),
        )
        self.assertEqual(entry.notes, ("Keep the rollout small and observable.",))
        self.assertEqual(entry.total_items, 5)

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
