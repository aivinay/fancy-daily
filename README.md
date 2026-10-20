# Fancy Daily

Fancy Daily is a local-first daily note parser and summary helper. It turns a
plain text daily log into structured JSON or clean Markdown so the same note can
be used for personal review, weekly summaries, or lightweight status reporting.

## Installation

Requires Python 3.10 or later. On macOS or Linux, run these commands from the
repository root to install into a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
```

Run the installed CLI without setting `PYTHONPATH` or activating the environment:

```bash
.venv/bin/fancy-daily --version
.venv/bin/fancy-daily parse --strict --format markdown examples/daily-note.txt
```

Alternatively, invoke the same CLI through the environment's Python:

```bash
.venv/bin/python -m fancy_daily parse --strict examples/daily-note.txt
```

On Windows, use `.venv\Scripts\python.exe` and `.venv\Scripts\fancy-daily.exe`
for the environment's executables. Re-run the install command after changing
source files to update the installed copy.

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

- `Highlights`, `Highlight`, `Wins`, `Accomplishments`, `Accomplishment`,
  `Outcomes`, `Outcome`, `Milestones`, `Milestone`, `Progress`, or `Done`
- `Blockers`, `Blocker`, `Risks`, `Risk`, `Issues`, `Issue`, `Challenges`,
  `Challenge`, `Obstacles`, `Obstacle`, `Problems`, `Problem`, `Concerns`,
  `Concern`, `Delays`, `Delay`, `Dependencies`, `Dependency`, `Escalations`,
  `Escalation`, `Impediments`, `Impediment`, or `Stuck`
- `Follow-ups`, `Follow-up`, `Follow ups`, `Followups`, `Actions`,
  `Action items`, `Next action`, `Next actions`, `Next steps`, `Tasks`,
  `Task`, `To do`, `Todo`, or `Todos`
- `Notes`, `Note`, `Reflections`, `Reflection`, `Thoughts`, `Thought`,
  `Lessons`, `Lesson`, `Learnings`, `Learning`, `Ideas`, `Idea`, `Decisions`,
  `Decision`, `Summaries`, `Summary`, `Reviews`, `Review`, `Retrospectives`,
  `Retrospective`, `Questions`, `Question`, `Gratitude`, `Thanks`

Section labels may be written on their own line or inline with a value, such as
`Highlights: Finished the parser update`. Unlabeled lines are treated as notes.
Markdown emphasis around section labels is ignored, so labels such as
`**Highlights:**`, `_Follow-ups:_`, and `` `Notes`: `` are recognized.
Section headings may include closing hashes, such as `## Highlights ##`.
Markers belonging to an inline value, such as `_config`, `` `command` ``, or
`**Important**`, are preserved.
Dates may be written as `Date: 2026-07-02`, as a plain `2026-07-02` line, or as
a Markdown heading such as `# 2026-07-02`. Date labels, plain date lines, and
date headings may include trailing title text, such as `# 2026-07-02 Friday
Review`.
Quoted date values are also accepted, including dates read from YAML front
matter.
ISO 8601 timestamps such as `2026-07-02T09:30:00Z` are normalized to their
calendar date. Date and timestamp values must be valid; invalid values leave
the parsed date unset.
Bullet items using `-`, `*`, `+`, `1.`, or `1)` are normalized before rendering.
Spaces or tabs may separate a list marker from its text.
Markdown task list markers like `[ ]`, `[x]`, and `[X]` are also removed from
parsed items. Empty bullet or checkbox placeholders are ignored.
This includes bare `-`, `*`, and `+` bullets and numbered placeholders such as
`1.` and `2)`. Placeholders do not count toward entry limits or satisfy
`--require-entry` or `--strict`.
Markdown horizontal rules such as `---`, `***`, `___`, and spaced forms like
`- - -` are ignored. Spaces and tabs may separate the rule's markers.
HTML comments are ignored, including multi-line template guidance and comments
appended to otherwise visible items.
An unclosed comment is ignored through the end of the note. Comment markers
inside fenced code are literal examples and do not hide surrounding note text;
likewise, fences inside comments do not start code blocks.
Fenced Markdown code blocks are ignored, so examples inside them do not create
items or change sections. A closing fence must use the same marker character,
be at least as long as its opening fence, and have no trailing text other than
whitespace. An unclosed code block is ignored through the end of the note.
Markdown blockquote prefixes are removed before parsing, so quoted dates,
section labels, and list items work like their unquoted forms.
YAML front matter at the start of a note is ignored except for its top-level
`date` field, which is used as the entry date. Dates inside nested metadata do
not set the entry date.

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
Use `--format text`, `--format txt`, or `--format plain` for a plain
terminal-friendly summary.
Use `--format pretty-json` or `--format pretty` to request indented JSON
explicitly.
Use `--format compact-json` or `--format compact` for single-line JSON output
in scripts or logs.
Use `--format csv` for spreadsheet-friendly rows with `date`, `section`,
`index`, and `item` columns.
Use `--format tsv` for the same row layout with tab-separated columns.
Add `--no-header` with `csv` or `tsv` when appending rows to an existing file.
With any other format, `--no-header` reports an error with exit status 2 before
reading the note.
Library CSV and TSV renderers quote embedded delimiters, quotes, and line breaks
in `DailyEntry` fields, preserving their contents. Record endings use LF.
Use `--format stats-json` or `--format stats` to output only the parsed date,
empty state, total item count, and per-section counts.
Use `--format compact-stats-json` or `--format compact-stats` for the same
stats payload as single-line JSON in scripts or logs.

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
Note files must be UTF-8 encoded. A single leading byte-order mark (BOM) is
ignored for file, stdin, and library input.
Missing files, invalid file encoding, and stdin read or decoding failures are
reported as command-line errors with exit status 2 instead of Python tracebacks.
Undecodable bytes preserved by stdin's `surrogateescape` mode are rejected before
parsing or rendering, rather than copied into summaries.
Failed input reads do not write to the output file.
Use `--require-date` when a pipeline should reject notes that do not include a
parseable date.
Use `--require-entry` when a pipeline should reject dated but otherwise empty
notes.
Use `--strict` as a shortcut for requiring both a parseable date and at least
one parsed entry.
Use `--require-section highlights` to require a specific parsed section; repeat
the option to require multiple sections.
Use `--min-items 3` when a pipeline should require a minimum number of parsed
entries.
Use `--max-items 10` when a pipeline should reject notes that exceed an entry
limit. When used together, the minimum cannot exceed the maximum.

Write output to a file:

```bash
PYTHONPATH=src python3 -m fancy_daily.cli parse \
  --format markdown \
  -o reports/daily/summary.md \
  daily.txt
```

Missing parent directories for `--output` are created automatically.
Use `--output -` to write to stdout explicitly.
Only the literal `-` selects stdout; use `--output ./-` to write a file named `-`.
If stdout's encoding cannot represent the summary, the CLI reports an error
with exit status 2. Use `--output` with a file path to write UTF-8 output.
Output write failures are reported as command-line errors instead of Python
tracebacks.

When a note has a date but no section entries, Markdown output keeps the date
heading and renders `_No entries recorded._` so empty daily logs are explicit.
Library callers can use `DailyEntry.is_empty`, `DailyEntry.total_items`, and
`DailyEntry.section_counts` for quick summary checks after parsing.

## Development

Run the test suite with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

CI builds and installs the package without editable mode on Python 3.10, 3.11,
and 3.12. It runs the tests in isolated mode against the installed package and
checks the installed `fancy-daily` command with the example note.

The project is intentionally growing in small increments so each change stays
reviewable and useful.
