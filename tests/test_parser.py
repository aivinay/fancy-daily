import unittest

from fancy_daily import parse_daily_note


class DailyParserTests(unittest.TestCase):
    def test_parses_daily_note_sections(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-06-24

            Highlights:
            - Shipped parser foundation
            - Wrote tests

            Blockers:
            - Need CLI next

            Follow-ups:
            - Add markdown output

            Notes:
            Keep the format lightweight.
            """
        )

        self.assertEqual(entry.date, "2026-06-24")
        self.assertEqual(entry.highlights, ("Shipped parser foundation", "Wrote tests"))
        self.assertEqual(entry.blockers, ("Need CLI next",))
        self.assertEqual(entry.follow_ups, ("Add markdown output",))
        self.assertEqual(entry.notes, ("Keep the format lightweight.",))
        self.assertFalse(entry.is_empty)
        self.assertEqual(entry.total_items, 5)
        self.assertEqual(
            entry.section_counts,
            {
                "highlights": 2,
                "blockers": 1,
                "follow_ups": 1,
                "notes": 1,
            },
        )

    def test_exposes_empty_entry_helpers(self) -> None:
        entry = parse_daily_note("Date: 2026-09-07")

        self.assertTrue(entry.is_empty)
        self.assertEqual(entry.total_items, 0)
        self.assertEqual(
            entry.section_counts,
            {
                "highlights": 0,
                "blockers": 0,
                "follow_ups": 0,
                "notes": 0,
            },
        )

    def test_accepts_a_leading_byte_order_mark(self) -> None:
        for preamble, expected_date in (
            ("Date: 2026-10-03\n", "2026-10-03"),
            ("2026-10-03\n", "2026-10-03"),
            ("# 2026-10-03\n", "2026-10-03"),
            ("---\ntitle: Daily review\ndate: 2026-10-03\n---\n", "2026-10-03"),
            ("", None),
        ):
            with self.subTest(preamble=preamble):
                entry = parse_daily_note("\ufeff" + preamble + "Highlights:\n- Shipped work")

                self.assertEqual(entry.date, expected_date)
                self.assertEqual(entry.highlights, ("Shipped work",))
                self.assertEqual(entry.total_items, 1)

    def test_byte_order_mark_only_note_is_empty(self) -> None:
        entry = parse_daily_note("\ufeff")

        self.assertIsNone(entry.date)
        self.assertTrue(entry.is_empty)

    def test_preserves_embedded_byte_order_mark_in_note_text(self) -> None:
        entry = parse_daily_note("\ufeffNotes:\n- Left\ufeffRight")

        self.assertEqual(entry.notes, ("Left\ufeffRight",))

    def test_defaults_unlabeled_lines_to_notes(self) -> None:
        entry = parse_daily_note("Loose thought\n- Another note")

        self.assertEqual(entry.date, None)
        self.assertEqual(entry.notes, ("Loose thought", "Another note"))

    def test_cleans_ordered_list_items(self) -> None:
        entry = parse_daily_note(
            """
            Highlights:
            1. Added ordered list parsing
            2) Kept parser output stable
            """
        )

        self.assertEqual(
            entry.highlights,
            ("Added ordered list parsing", "Kept parser output stable"),
        )

    def test_cleans_plus_list_items(self) -> None:
        entry = parse_daily_note(
            """
            Notes:
            + Captured a Markdown plus bullet
            + Kept the item text clean
            """
        )

        self.assertEqual(
            entry.notes,
            ("Captured a Markdown plus bullet", "Kept the item text clean"),
        )

    def test_cleans_tab_separated_unordered_items(self) -> None:
        for marker in ("-", "*", "+"):
            with self.subTest(marker=marker):
                entry = parse_daily_note(
                    f"Notes:\n{marker}\tPlain item\n{marker} \t[x] Checked item\n"
                    f"Notes: {marker}\t[ ] Inline item"
                )

                self.assertEqual(entry.notes, ("Plain item", "Checked item", "Inline item"))

    def test_keeps_marker_like_text_without_whitespace(self) -> None:
        values = ("-config", "+1", "*Important*", "**Important**")
        entry = parse_daily_note("Notes:\n" + "\n".join(values))

        self.assertEqual(entry.notes, values)

    def test_accepts_markdown_heading_sections(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-07-03
            ## Highlights
            - Parsed markdown headings
            ### Follow-ups:
            - Document heading support
            """
        )

        self.assertEqual(entry.highlights, ("Parsed markdown headings",))
        self.assertEqual(entry.follow_ups, ("Document heading support",))

    def test_accepts_closed_markdown_section_headings(self) -> None:
        entry = parse_daily_note(
            "## Highlights ##\n- Shipped work\n"
            "> ### **Blockers:** ###\n- Waiting on review\n"
            "## Follow-ups\t####\n- Send update\n## Notes ##\n- Keep context"
        )

        self.assertEqual(entry.highlights, ("Shipped work",))
        self.assertEqual(entry.blockers, ("Waiting on review",))
        self.assertEqual(entry.follow_ups, ("Send update",))
        self.assertEqual(entry.notes, ("Keep context",))

    def test_preserves_hashes_outside_closing_heading_markers(self) -> None:
        values = ("Highlights ##", "## Highlights##", "Notes: Keep #tag ##")
        entry = parse_daily_note("Notes:\n" + "\n".join(values))

        self.assertEqual(entry.notes, (values[0], values[1], "Keep #tag ##"))

    def test_accepts_emphasized_markdown_section_labels(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-09-16
            ## **Highlights**
            - Parsed bold heading labels
            **Blockers:** Waiting on one review
            _Follow-ups:_ Send the rollout note
            `Notes`: Keep labels readable in copied Markdown
            """
        )

        self.assertEqual(entry.highlights, ("Parsed bold heading labels",))
        self.assertEqual(entry.blockers, ("Waiting on one review",))
        self.assertEqual(entry.follow_ups, ("Send the rollout note",))
        self.assertEqual(
            entry.notes,
            ("Keep labels readable in copied Markdown",),
        )

    def test_preserves_markers_in_inline_values(self) -> None:
        for label in ("Notes:", "**Notes**:", "_Notes_:", "`Notes`:"):
            with self.subTest(label=label):
                values = ("_config", "`command`", "**Important**")
                entry = parse_daily_note("\n".join(f"{label} {value}" for value in values))

                self.assertEqual(entry.notes, values)

    def test_removes_only_label_markers_spanning_inline_colon(self) -> None:
        for markers in ("*", "**", "_", "__", "`", "**_"):
            with self.subTest(markers=markers):
                entry = parse_daily_note(f"{markers}Notes:{markers[::-1]} `command`")

                self.assertEqual(entry.notes, ("`command`",))

    def test_accepts_markdown_date_heading(self) -> None:
        entry = parse_daily_note(
            """
            # 2026-07-21

            ## Highlights
            - Parsed heading date
            """
        )

        self.assertEqual(entry.date, "2026-07-21")
        self.assertEqual(entry.highlights, ("Parsed heading date",))

    def test_accepts_markdown_date_heading_with_title(self) -> None:
        entry = parse_daily_note(
            """
            # 2026-07-29 Wednesday Review

            Highlights:
            - Parsed a dated heading title
            """
        )

        self.assertEqual(entry.date, "2026-07-29")
        self.assertEqual(entry.highlights, ("Parsed a dated heading title",))

    def test_accepts_plain_date_line(self) -> None:
        entry = parse_daily_note(
            """
            2026-07-22

            Highlights:
            - Parsed plain date line
            """
        )

        self.assertEqual(entry.date, "2026-07-22")
        self.assertEqual(entry.highlights, ("Parsed plain date line",))

    def test_accepts_plain_date_line_with_title(self) -> None:
        entry = parse_daily_note(
            """
            2026-07-29 Wednesday Review

            Notes:
            - Keep titled daily notes readable
            """
        )

        self.assertEqual(entry.date, "2026-07-29")
        self.assertEqual(entry.notes, ("Keep titled daily notes readable",))

    def test_accepts_date_label_with_title(self) -> None:
        entry = parse_daily_note(
            """
            Date: 2026-07-31 Friday Review

            Highlights:
            - Parsed titled date label
            """
        )

        self.assertEqual(entry.date, "2026-07-31")
        self.assertEqual(entry.highlights, ("Parsed titled date label",))

    def test_accepts_whitespace_before_date_label_colon(self) -> None:
        for label in ("Date :", "DATE\t:", "> Date \t:"):
            with self.subTest(label=label):
                entry = parse_daily_note(f"{label} '2026-10-30'\nNotes: Kept work")
                self.assertEqual(entry.date, "2026-10-30")
                self.assertEqual(entry.notes, ("Kept work",))

    def test_preserves_non_date_labels(self) -> None:
        entry = parse_daily_note("Notes:\nDate range: Tomorrow\nDatabase: Ready")
        self.assertIsNone(entry.date)
        self.assertEqual(entry.notes, ("Date range: Tomorrow", "Database: Ready"))

    def test_accepts_quoted_date_values(self) -> None:
        yaml_entry = parse_daily_note(
            """
            ---
            date: "2026-09-20"
            tags: [daily]
            ---
            Highlights:
            - Parsed a quoted YAML date
            """
        )
        labeled_entry = parse_daily_note("Date: '2026-09-21 Monday Review'")

        self.assertEqual(yaml_entry.date, "2026-09-20")
        self.assertEqual(labeled_entry.date, "2026-09-21")

    def test_extracts_date_from_iso_timestamps(self) -> None:
        yaml_entry = parse_daily_note(
            """
            ---
            date: 2026-09-21T08:30:00-04:00
            ---
            Highlights:
            - Parsed a timestamp from front matter
            """
        )
        plain_entry = parse_daily_note(
            """
            2026-09-22T12:15:00Z
            Notes:
            - Timestamp dates stay concise
            """
        )

        self.assertEqual(yaml_entry.date, "2026-09-21")
        self.assertEqual(plain_entry.date, "2026-09-22")

    def test_extracts_date_from_utc_timestamps(self) -> None:
        templates = (
            "{timestamp}",
            "# {timestamp}",
            "Date: {timestamp}",
            "Date: '{timestamp}'",
            "---\ndate: {timestamp}\n---",
            '---\ndate: "{timestamp}"\n---',
        )
        for timestamp in (
            "2026-09-22T12:15:00Z",
            "2026-09-22T12:15:00.123456Z",
        ):
            for template in templates:
                with self.subTest(timestamp=timestamp, template=template):
                    text = template.format(timestamp=timestamp)
                    entry = parse_daily_note(text + "\nNotes:\n- Kept this note")

                    self.assertEqual(entry.date, "2026-09-22")
                    self.assertEqual(entry.notes, ("Kept this note",))

    def test_rejects_malformed_utc_timestamps(self) -> None:
        for timestamp in (
            "2026-09-22T25:00:00Z",
            "2026-09-22T12:15:00ZZ",
            "2026-09-22T12:15:00Zjunk",
            "2026-09-22T12:Z15:00",
            "2026-09-22T12:15:00+01:00Z",
        ):
            for template in (
                "{timestamp}",
                "Date: {timestamp}",
                "---\ndate: {timestamp}\n---",
            ):
                with self.subTest(timestamp=timestamp, template=template):
                    entry = parse_daily_note(template.format(timestamp=timestamp))
                    self.assertIsNone(entry.date)

    def test_rejects_invalid_iso_timestamps(self) -> None:
        labeled = parse_daily_note("Date: 2026-09-27T99:99:99")
        plain = parse_daily_note("2026-09-27Tnot-a-time")
        yaml_entry = parse_daily_note("---\ndate: 2026-09-27T25:00:00Z\n---")

        self.assertIsNone(labeled.date)
        self.assertIsNone(plain.date)
        self.assertIsNone(yaml_entry.date)

    def test_rejects_invalid_calendar_dates(self) -> None:
        labeled = parse_daily_note("Date: 2026-02-30\nHighlights:\n- Kept this item")
        plain = parse_daily_note("2026-13-01\nHighlights:\n- Kept this item")
        arbitrary = parse_daily_note("Date: someday\nHighlights:\n- Kept this item")

        self.assertIsNone(labeled.date)
        self.assertIsNone(plain.date)
        self.assertIsNone(arbitrary.date)
        self.assertEqual(labeled.highlights, ("Kept this item",))
        self.assertEqual(plain.highlights, ("Kept this item",))

    def test_cleans_checkbox_list_items(self) -> None:
        entry = parse_daily_note(
            """
            Follow-ups:
            - [ ] Write release notes
            - [x] Ship parser support
            * [X] Review summary output
            """
        )

        self.assertEqual(
            entry.follow_ups,
            ("Write release notes", "Ship parser support", "Review summary output"),
        )

    def test_preserves_checkbox_like_text_without_separator(self) -> None:
        values = ("[x]coordinate", "[X]value", "[ ]placeholder")
        for prefix in ("", "- ", "1. "):
            with self.subTest(prefix=prefix):
                entry = parse_daily_note(
                    "Notes:\n" + "\n".join(prefix + value for value in values)
                )
                self.assertEqual(entry.notes, values)

    def test_cleans_tab_separated_checkboxes(self) -> None:
        entry = parse_daily_note("Notes:\n[x]\tDone\n- [ ]\tPending\n[X]")

        self.assertEqual(entry.notes, ("Done", "Pending"))

    def test_ignores_empty_list_placeholders(self) -> None:
        entry = parse_daily_note(
            """
            Highlights:
            -
            - Shipped useful work
            Follow-ups:
            - [ ]
            - [ ] Send update
            Notes:
            +
            *
            Loose note
            """
        )

        self.assertEqual(entry.highlights, ("Shipped useful work",))
        self.assertEqual(entry.follow_ups, ("Send update",))
        self.assertEqual(entry.notes, ("Loose note",))

    def test_ignores_empty_ordered_list_placeholders(self) -> None:
        for section in ("Highlights", "Blockers", "Follow-ups", "Notes"):
            with self.subTest(section=section):
                entry = parse_daily_note(
                    f"Date: 2026-10-07\n{section}:\n"
                    "1.\n2) \t\n  12.\n> 42)\n1. [ ]\n2) [x]\n"
                    f"{section}: 3.\n{section}: 4)"
                )

                self.assertEqual(entry.date, "2026-10-07")
                self.assertTrue(entry.is_empty)
                self.assertEqual(entry.total_items, 0)

    def test_keeps_content_among_ordered_list_placeholders(self) -> None:
        entry = parse_daily_note(
            "Notes:\n1.\n2. Shipped work\n3)\n4)\tReviewed changes\n"
            "1.5 hours\n2)No separator\n2026\nVersion 1."
        )

        self.assertEqual(
            entry.notes,
            (
                "Shipped work", "Reviewed changes", "1.5 hours",
                "2)No separator", "2026", "Version 1.",
            ),
        )
        self.assertEqual(entry.total_items, 6)

    def test_ignores_tab_separated_horizontal_rules(self) -> None:
        for marker in ("-", "*", "_"):
            for separator in ("\t", " \t "):
                with self.subTest(marker=marker, separator=separator):
                    rule = separator.join([marker] * 3)
                    entry = parse_daily_note(f"Notes:\n{rule}\n> {rule}")

                    self.assertTrue(entry.is_empty)
                    self.assertEqual(entry.total_items, 0)

    def test_keeps_item_text_next_to_tab_separated_rules(self) -> None:
        entry = parse_daily_note("Highlights:\n-\tShipped work\n*\t*\t*\nMore work")

        self.assertEqual(entry.highlights, ("Shipped work", "More work"))

    def test_ignores_markdown_horizontal_rules(self) -> None:
        entry = parse_daily_note(
            """
            Notes:
            First note
            ---
            Second note
            ***
            Third note
            ___
            Fourth note
            - - -
            Fifth note
            * * *
            Sixth note
            _ _ _
            """
        )

        self.assertEqual(
            entry.notes,
            (
                "First note",
                "Second note",
                "Third note",
                "Fourth note",
                "Fifth note",
                "Sixth note",
            ),
        )

    def test_ignores_html_comments(self) -> None:
        entry = parse_daily_note(
            """
            <!-- Keep these prompts in the template. -->
            Highlights:
            - Shipped comment filtering <!-- private context -->
            <!--
            Blockers:
            - This template guidance is not a real blocker
            -->
            Follow-ups:
            - Document the behavior
            """
        )

        self.assertEqual(entry.highlights, ("Shipped comment filtering",))
        self.assertEqual(entry.blockers, ())
        self.assertEqual(entry.follow_ups, ("Document the behavior",))

    def test_ignores_fenced_code_without_changing_sections(self) -> None:
        entry = parse_daily_note(
            "Highlights:\n- Shipped parser\n```text\nBlockers:\n- Example only\n```\n- Kept parsing highlights\n~~~\nDate: 2026-09-29\n~~~\nNotes:\n- Real note"
        )

        self.assertIsNone(entry.date)
        self.assertEqual(entry.highlights, ("Shipped parser", "Kept parsing highlights"))
        self.assertEqual(entry.blockers, ())
        self.assertEqual(entry.notes, ("Real note",))

    def test_fenced_code_does_not_close_with_trailing_text(self) -> None:
        for marker in ("```", "~~~"):
            for suffix in (
                "example", " trailing text", "\ttrailing text", " <!-- not a close -->"
            ):
                with self.subTest(marker=marker, suffix=suffix):
                    entry = parse_daily_note(
                        "Highlights:\n- Real before\n"
                        f"{marker}text\n{marker}{suffix}\n"
                        "Date: 2026-09-30\nBlockers:\n- Example only\n"
                        f"{marker}\n- Real after"
                    )

                    self.assertIsNone(entry.date)
                    self.assertEqual(entry.highlights, ("Real before", "Real after"))
                    self.assertEqual(entry.blockers, ())
                    self.assertEqual(entry.total_items, 2)

    def test_fenced_code_requires_a_matching_closing_marker(self) -> None:
        for marker, other in (("`", "~"), ("~", "`")):
            for closing_length in (4, 5):
                with self.subTest(marker=marker, closing_length=closing_length):
                    entry = parse_daily_note(
                        "Notes:\n- Real before\n"
                        f"{marker * 4}text\n{marker * 3}\n{other * 4}\n"
                        "- Example only\n"
                        f"{marker * closing_length} \t\n- Real after"
                    )

                    self.assertEqual(entry.notes, ("Real before", "Real after"))
                    self.assertEqual(entry.total_items, 2)

    def test_unterminated_fenced_code_ignores_remaining_lines(self) -> None:
        for marker in ("```", "~~~"):
            with self.subTest(marker=marker):
                entry = parse_daily_note(
                    "Highlights:\n- Real item\n"
                    f"{marker}text\n{marker}not-a-close\n"
                    "Blockers:\n- Example only"
                )

                self.assertEqual(entry.highlights, ("Real item",))
                self.assertEqual(entry.blockers, ())
                self.assertEqual(entry.total_items, 1)

    def test_multiline_comments_keep_neighboring_items_separate(self) -> None:
        entry = parse_daily_note(
            "Highlights:\n- First item <!--\nprivate context\n-->- Second item"
        )

        self.assertEqual(entry.highlights, ("First item", "Second item"))

    def test_comment_openers_in_code_do_not_hide_following_items(self) -> None:
        for marker in ("```", "~~~"):
            for prefix in ("", "> "):
                with self.subTest(marker=marker, prefix=prefix):
                    lines = (
                        "Highlights:",
                        "- Before",
                        f"{marker}html",
                        "<!-- example opener",
                        marker,
                        "- After",
                        "<!-- template -->",
                        "Blockers:",
                        "- Real blocker",
                    )
                    entry = parse_daily_note(
                        "\n".join(prefix + line for line in lines)
                    )

                    self.assertEqual(entry.highlights, ("Before", "After"))
                    self.assertEqual(entry.blockers, ("Real blocker",))
                    self.assertEqual(entry.total_items, 3)

    def test_comment_markers_in_fence_info_do_not_hide_following_items(self) -> None:
        for marker in ("```", "~~~"):
            with self.subTest(marker=marker):
                entry = parse_daily_note(
                    f"{marker}html <!-- example\n- Hidden\n{marker}\n"
                    "Notes:\n- Visible\n<!-- template -->"
                )

                self.assertEqual(entry.notes, ("Visible",))
                self.assertEqual(entry.total_items, 1)

    def test_fences_inside_comments_do_not_hide_following_items(self) -> None:
        for marker in ("```", "~~~"):
            with self.subTest(marker=marker):
                entry = parse_daily_note(
                    f"<!--\n{marker}text\nBlockers:\n- Hidden\n-->\n"
                    "Highlights:\n- Visible"
                )

                self.assertEqual(entry.highlights, ("Visible",))
                self.assertEqual(entry.blockers, ())
                self.assertEqual(entry.total_items, 1)

    def test_unterminated_comments_ignore_remaining_lines(self) -> None:
        entry = parse_daily_note(
            "Highlights:\n- Visible <!-- unfinished\n```\n"
            "Date: 2026-10-04\nBlockers:\n- Hidden"
        )

        self.assertIsNone(entry.date)
        self.assertEqual(entry.highlights, ("Visible",))
        self.assertEqual(entry.blockers, ())
        self.assertEqual(entry.total_items, 1)

    def test_comments_can_precede_fences_on_the_same_line(self) -> None:
        entry = parse_daily_note(
            "<!-- template --> ```html\n<!-- example\n```\n"
            "Notes: Visible <!-- one --><!-- two --> tail"
        )

        self.assertEqual(entry.notes, ("Visible  tail",))
        self.assertEqual(entry.total_items, 1)

    def test_accepts_markdown_blockquotes(self) -> None:
        entry = parse_daily_note(
            """
            > Date: 2026-09-18
            > ## Highlights
            > - Parsed a quoted daily note
            >> Blockers: Waiting on review
            > Follow-ups:
            > - Document blockquote support
            """
        )

        self.assertEqual(entry.date, "2026-09-18")
        self.assertEqual(entry.highlights, ("Parsed a quoted daily note",))
        self.assertEqual(entry.blockers, ("Waiting on review",))
        self.assertEqual(entry.follow_ups, ("Document blockquote support",))

    def test_ignores_yaml_front_matter_except_date(self) -> None:
        entry = parse_daily_note(
            """
            ---
            title: Friday review
            date: 2026-09-19
            tags:
              - daily
              - work
            ---
            Highlights:
            - Parsed front matter cleanly
            Notes:
            - Metadata does not become note content
            """
        )

        self.assertEqual(entry.date, "2026-09-19")
        self.assertEqual(entry.highlights, ("Parsed front matter cleanly",))
        self.assertEqual(entry.notes, ("Metadata does not become note content",))

    def test_front_matter_prefers_top_level_date_over_nested_dates(self) -> None:
        for indentation in ("", "    "):
            with self.subTest(indentation=indentation):
                lines = (
                    "---", "project:", "  date: 2020-01-01",
                    "Date: 2026-10-10", "---", "Notes: Shipped work",
                )
                entry = parse_daily_note("\n".join(indentation + line for line in lines))

                self.assertEqual(entry.date, "2026-10-10")
                self.assertEqual(entry.notes, ("Shipped work",))
                self.assertEqual(entry.total_items, 1)

    def test_nested_front_matter_dates_do_not_supply_a_note_date(self) -> None:
        for root_date in ("", "date: invalid\n"):
            with self.subTest(root_date=root_date):
                entry = parse_daily_note(
                    "---\nproject:\n  date: 2020-01-01\n"
                    f"{root_date}---\nNotes: Shipped work"
                )

                self.assertIsNone(entry.date)
                self.assertEqual(entry.notes, ("Shipped work",))

    def test_front_matter_accepts_whitespace_before_date_colon(self) -> None:
        for indentation in ("", "  "):
            for separator in (" ", "\t"):
                with self.subTest(indentation=indentation, separator=separator):
                    entry = parse_daily_note(
                        f"---\n{indentation}project:\n"
                        f"{indentation}  date{separator}: 2020-01-01\n"
                        f'{indentation}Date{separator}: "2026-10-23"\n'
                        "---\nNotes: Shipped work"
                    )
                    self.assertEqual(entry.date, "2026-10-23")
                    self.assertEqual(entry.notes, ("Shipped work",))

    def test_nested_spaced_date_field_does_not_supply_note_date(self) -> None:
        entry = parse_daily_note(
            "---\nproject:\n  date : 2020-01-01\n---\nNotes: Shipped work"
        )

        self.assertIsNone(entry.date)
        self.assertEqual(entry.notes, ("Shipped work",))

    def test_front_matter_allows_comments_before_first_field(self) -> None:
        for indentation in ("", "  "):
            with self.subTest(indentation=indentation):
                entry = parse_daily_note(
                    "---\n# Daily template\n\n  # Metadata below\n"
                    f"{indentation}title: Daily review\n"
                    f"{indentation}date: 2026-10-25\n"
                    "---\nHighlights: Shipped work"
                )

                self.assertEqual(entry.date, "2026-10-25")
                self.assertEqual(entry.highlights, ("Shipped work",))
                self.assertEqual(entry.notes, ())

    def test_comments_do_not_hide_sections_between_rules(self) -> None:
        entry = parse_daily_note(
            "---\n# Context\nHighlights: Shipped work\n---\nNotes: Kept context"
        )

        self.assertEqual(entry.highlights, ("Shipped work",))
        self.assertEqual(entry.notes, ("# Context", "Kept context"))

    def test_front_matter_supports_indented_root_metadata(self) -> None:
        entry = parse_daily_note(
            "---\n  project:\n    date: 2020-01-01\n"
            "  date: 2026-10-10\n---\nNotes: Shipped work"
        )

        self.assertEqual(entry.date, "2026-10-10")
        self.assertEqual(entry.notes, ("Shipped work",))

    def test_keeps_sections_between_horizontal_rules(self) -> None:
        entry = parse_daily_note(
            """
            ---
            Highlights:
            - First item
            ---
            Notes: Second item
            """
        )
        inline_entry = parse_daily_note(
            "---\nHighlights: First item\n---\nNotes: Second item"
        )

        self.assertEqual(entry.highlights, ("First item",))
        self.assertEqual(entry.notes, ("Second item",))
        self.assertEqual(inline_entry.highlights, ("First item",))
        self.assertEqual(inline_entry.notes, ("Second item",))

    def test_keeps_freeform_notes_between_horizontal_rules(self) -> None:
        entry = parse_daily_note(
            "---\nA thought without a section\n- Another note\n---\nNotes: Last note"
        )

        self.assertEqual(
            entry.notes,
            ("A thought without a section", "Another note", "Last note"),
        )

    def test_accepts_variable_whitespace_in_section_labels(self) -> None:
        for label in ("Follow  ups", "Action\titems", "Next   steps", "To\tdo"):
            with self.subTest(label=label):
                entry = parse_daily_note(
                    f"## {label}\n- First item\n**{label}:** Keep  inner\tspacing"
                )
                self.assertEqual(
                    entry.follow_ups, ("First item", "Keep  inner\tspacing")
                )
                self.assertEqual(entry.notes, ())

    def test_accepts_inline_section_values(self) -> None:
        entry = parse_daily_note(
            """
            Highlights: Shipped inline labels
            Blockers: Waiting on fixture review
            Follow-ups: Document inline label support
            Notes: Keep single-line notes readable
            """
        )

        self.assertEqual(entry.highlights, ("Shipped inline labels",))
        self.assertEqual(entry.blockers, ("Waiting on fixture review",))
        self.assertEqual(entry.follow_ups, ("Document inline label support",))
        self.assertEqual(entry.notes, ("Keep single-line notes readable",))

    def test_accepts_action_oriented_follow_up_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Follow-up:
            - Send summary
            Actions: Open tracking issue
            Next steps:
            - Draft tomorrow's plan
            """
        )

        self.assertEqual(
            entry.follow_ups,
            ("Send summary", "Open tracking issue", "Draft tomorrow's plan"),
        )

    def test_accepts_task_oriented_follow_up_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Tasks:
            - Prepare demo
            To do: Update checklist
            Todos:
            - Share notes
            """
        )

        self.assertEqual(
            entry.follow_ups,
            ("Prepare demo", "Update checklist", "Share notes"),
        )

    def test_accepts_next_action_follow_up_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Next actions:
            - Draft the launch note
            Next action: Confirm the review owner
            """
        )

        self.assertEqual(
            entry.follow_ups,
            ("Draft the launch note", "Confirm the review owner"),
        )

    def test_accepts_accomplishment_highlight_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Accomplishments:
            - Finished parser cleanup
            Done: Published summary
            """
        )

        self.assertEqual(
            entry.highlights,
            ("Finished parser cleanup", "Published summary"),
        )

    def test_accepts_outcome_highlight_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Outcomes:
            - Cut weekly summary prep time
            Outcome: Daily notes are easier to scan
            """
        )

        self.assertEqual(
            entry.highlights,
            ("Cut weekly summary prep time", "Daily notes are easier to scan"),
        )

    def test_accepts_milestone_highlight_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Milestones:
            - Finished the first parser vocabulary pass
            Milestone: Documented stable output aliases
            """
        )

        self.assertEqual(
            entry.highlights,
            (
                "Finished the first parser vocabulary pass",
                "Documented stable output aliases",
            ),
        )

    def test_accepts_progress_highlight_alias(self) -> None:
        entry = parse_daily_note(
            """
            Progress:
            - Added one more daily note vocabulary alias
            Progress: Kept parser behavior covered by tests
            """
        )

        self.assertEqual(
            entry.highlights,
            (
                "Added one more daily note vocabulary alias",
                "Kept parser behavior covered by tests",
            ),
        )

    def test_accepts_risk_and_issue_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Risks:
            - Review window is tight
            Issue: Waiting on fixture data
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Review window is tight", "Waiting on fixture data"),
        )

    def test_accepts_challenge_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Challenges:
            - Review queue is busy
            Challenge: Need clearer fixture naming
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Review queue is busy", "Need clearer fixture naming"),
        )

    def test_accepts_obstacle_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Obstacles:
            - Waiting on environment access
            Obstacle: Need clearer sample data
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Waiting on environment access", "Need clearer sample data"),
        )

    def test_accepts_problem_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Problems:
            - Release notes are incomplete
            Problem: Need a clearer review owner
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Release notes are incomplete", "Need a clearer review owner"),
        )

    def test_accepts_concern_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Concerns:
            - Review capacity is thin
            Concern: Need clearer release criteria
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Review capacity is thin", "Need clearer release criteria"),
        )

    def test_accepts_dependency_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Dependencies:
            - Waiting on API credentials
            Dependency: Need product review before launch
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Waiting on API credentials", "Need product review before launch"),
        )

    def test_accepts_delay_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Delays:
            - Fixture refresh is running late
            Delay: Release notes need one more review
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Fixture refresh is running late", "Release notes need one more review"),
        )

    def test_accepts_impediment_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Impediments:
            - Release checklist access is missing
            Impediment: Need stakeholder sign-off
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Release checklist access is missing", "Need stakeholder sign-off"),
        )

    def test_accepts_escalation_blocker_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Escalations:
            - Contract review needs leadership input
            Escalation: Customer approval is blocked
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Contract review needs leadership input", "Customer approval is blocked"),
        )

    def test_accepts_stuck_blocker_alias(self) -> None:
        entry = parse_daily_note(
            """
            Stuck:
            - Need clearer deploy access
            Stuck: Waiting on release owner
            """
        )

        self.assertEqual(
            entry.blockers,
            ("Need clearer deploy access", "Waiting on release owner"),
        )

    def test_accepts_reflection_and_thought_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Reflections:
            - The review loop is getting clearer
            Thought: Keep tomorrow's slice small
            """
        )

        self.assertEqual(
            entry.notes,
            ("The review loop is getting clearer", "Keep tomorrow's slice small"),
        )

    def test_accepts_learning_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Lessons:
            - Keep daily changes focused
            Learning: Parser aliases should match real note habits
            """
        )

        self.assertEqual(
            entry.notes,
            (
                "Keep daily changes focused",
                "Parser aliases should match real note habits",
            ),
        )

    def test_accepts_idea_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Ideas:
            - Try a weekly rollup command
            Idea: Keep summaries easy to scan
            """
        )

        self.assertEqual(
            entry.notes,
            ("Try a weekly rollup command", "Keep summaries easy to scan"),
        )

    def test_accepts_question_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Questions:
            - Should the weekly rollup group by section?
            Question: What output should the review command prefer?
            """
        )

        self.assertEqual(
            entry.notes,
            (
                "Should the weekly rollup group by section?",
                "What output should the review command prefer?",
            ),
        )

    def test_accepts_gratitude_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Gratitude:
            - Clear review feedback
            Thanks: Helpful parser examples
            """
        )

        self.assertEqual(
            entry.notes,
            ("Clear review feedback", "Helpful parser examples"),
        )

    def test_accepts_decision_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Decisions:
            - Keep the CLI output stable
            Decision: Document parser vocabulary before adding rollups
            """
        )

        self.assertEqual(
            entry.notes,
            (
                "Keep the CLI output stable",
                "Document parser vocabulary before adding rollups",
            ),
        )

    def test_accepts_summary_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Summary:
            - Parser vocabulary now covers more daily note styles
            Summaries: Keep section aliases explicit and tested
            """
        )

        self.assertEqual(
            entry.notes,
            (
                "Parser vocabulary now covers more daily note styles",
                "Keep section aliases explicit and tested",
            ),
        )

    def test_accepts_review_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Reviews:
            - Weekly notes need one final pass
            Review: Keep the summary focused
            """
        )

        self.assertEqual(
            entry.notes,
            ("Weekly notes need one final pass", "Keep the summary focused"),
        )

    def test_accepts_retrospective_note_aliases(self) -> None:
        entry = parse_daily_note(
            """
            Retrospectives:
            - The release rhythm is getting easier to sustain
            Retrospective: Keep the next improvement small
            """
        )

        self.assertEqual(
            entry.notes,
            (
                "The release rhythm is getting easier to sustain",
                "Keep the next improvement small",
            ),
        )


if __name__ == "__main__":
    unittest.main()
