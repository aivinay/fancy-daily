import json
import subprocess
import sys
import unittest

from fancy_daily import __version__


class ModuleEntrypointTests(unittest.TestCase):
    def test_module_reports_package_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "fancy_daily", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"fancy-daily {__version__}\n")
        self.assertEqual(result.stderr, "")

    def test_module_parses_stdin_with_cli_options(self) -> None:
        result = subprocess.run(
            [
                sys.executable, "-m", "fancy_daily", "parse", "--strict",
                "--format", "compact-json", "-",
            ],
            input="Date: 2026-10-15\nHighlights: Added module entry point",
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["date"], "2026-10-15")
        self.assertEqual(payload["highlights"], ["Added module entry point"])
        self.assertEqual(result.stderr, "")

    def test_module_returns_cli_validation_errors(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "fancy_daily", "parse", "--strict"],
            input="Notes: Missing a date",
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("daily note is missing a date", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
