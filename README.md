# Fancy Daily

Fancy Daily is a local-first daily note parser and summary helper. It turns a
plain text daily log into structured JSON or clean Markdown so the same note can
be used for personal review, weekly summaries, or lightweight status reporting.

## Note Format

Daily notes are plain text with optional sections:

```text
Date: 2026-07-02

Highlights:
- Shipped the markdown renderer
1. Added CLI output support

Blockers:
- Waiting on design feedback

Actions: Add examples for weekly review

Notes:
Keep the format easy to write by hand.
```

Supported sections are:

- `Highlights`, `Highlight`, `Wins`, `Accomplishments`, `Accomplishment`, or
  `Done`
- `Blockers`, `Blocker`, `Risks`, `Risk`, `Issues`, or `Issue`
- `Follow-ups`, `Follow-up`, `Follow ups`, `Followups`, `Actions`,
  `Action items`, `Next steps`, `Tasks`, `Task`, `To do`, `Todo`, or `Todos`
- `Notes`, `Note`, `Reflections`, `Reflection`, `Thoughts`, `Thought`,
  `Lessons`, `Lesson`, `Learnings`, or `Learning`

Section labels may be written on their own line or inline with a value, such as
`Highlights: Finished the parser update`. Unlabeled lines are treated as notes.
Dates may be written as `Date: 2026-07-02`, as a plain `2026-07-02` line, or as
a Markdown heading such as `# 2026-07-02`. Date labels, plain date lines, and
date headings may include trailing title text, such as `# 2026-07-02 Friday
Review`.
Bullet items using `-`, `*`, `1.`, or `1)` are normalized before rendering.
Markdown task list markers like `[ ]`, `[x]`, and `[X]` are also removed from
parsed items. Empty bullet or checkbox placeholders are ignored.

## Usage

Run the parser from a checkout with:

```bash
PYTHONPATH=src python3 -m fancy_daily.cli parse daily.txt
```

Render Markdown instead of JSON:

```bash
PYTHONPATH=src python3 -m fancy_daily.cli parse --format markdown daily.txt
```

Use `--format md` for the same Markdown output with a shorter option value.
Use `--format compact-json` for single-line JSON output in scripts or logs.

Check the installed CLI version:

```bash
fancy-daily --version
```

Try the included example note:

```bash
PYTHONPATH=src python3 -m fancy_daily.cli parse --format markdown examples/daily-note.txt
```

Pipe a note through standard input by using `-` as the file path:

```bash
cat daily.txt | PYTHONPATH=src python3 -m fancy_daily.cli parse -
```

When no file path is provided, `parse` also reads from standard input.

Write output to a file:

```bash
PYTHONPATH=src python3 -m fancy_daily.cli parse \
  --format markdown \
  -o reports/daily/summary.md \
  daily.txt
```

Missing parent directories for `--output` are created automatically.
Use `--output -` to write to stdout explicitly.

When a note has a date but no section entries, Markdown output keeps the date
heading and renders `_No entries recorded._` so empty daily logs are explicit.

## Development

Run the test suite with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

The project is intentionally growing in small increments so each change stays
reviewable and useful.
