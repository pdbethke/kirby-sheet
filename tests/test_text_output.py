"""Sheet -> plain text -- the format a person reads at the table."""
import os

import pytest

from kirby_sheet.build import sheet_from_hdc
from kirby_sheet.formats import as_text
from kirby_sheet.formats.as_text import to_text
from kirby_sheet.sheet import (CharacteristicRow, Entry, Identity, Prose,
                               Section, Sheet, Totals)


def _sheet(**kw):
    base = dict(
        identity=Identity(name="Identity-name"),
        characteristics=(),
        sections=(),
        prose=Prose(),
        totals=Totals(),
    )
    base.update(kw)
    return Sheet(**base)


def _char_row(**kw):
    """Every field distinct, so a test can tell one from another."""
    base = dict(xmlid="STR-xmlid", name="Char-name", value=15.0, base=10.0,
                cost=5.0, active_cost=7.0, total="Total-str", roll="Roll-str",
                notes="Notes-str")
    base.update(kw)
    return CharacteristicRow(**base)


def _entry(**kw):
    base = dict(id="Entry-id", name="Entry-name", alias="Entry-alias",
                xmlid="Entry-xmlid", display="Display-str", cost=1.0,
                cost_before_framework=2.0, active_cost=3.0, end=4.0,
                parent_id="")
    base.update(kw)
    return Entry(**base)


# --- header -----------------------------------------------------------

def test_header_centers_the_name():
    out = to_text(_sheet(identity=Identity(name="Bokor")))
    lines = out.splitlines()
    assert lines[1].strip() == "BOKOR"
    assert lines[1] == "BOKOR".center(78).rstrip()


def test_header_uppercases_the_name():
    out = to_text(_sheet(identity=Identity(name="lower-name")))
    assert "LOWER-NAME" in out.splitlines()[1]


def test_header_centers_the_alternate_identity_when_present():
    out = to_text(_sheet(identity=Identity(
        name="Bokor", alternate_identities="Jean-Pierre Baptiste St. Clair")))
    lines = out.splitlines()
    assert lines[2].strip() == "Jean-Pierre Baptiste St. Clair"
    # Not uppercased, unlike the name.
    assert "Jean-Pierre" in lines[2]


def test_header_omits_the_alternate_identity_line_when_absent():
    out = to_text(_sheet(identity=Identity(name="Bokor", alternate_identities="")))
    lines = out.splitlines()
    # rule, name, rule, blank -- no third centered line before the blank.
    assert lines[0] == "=" * 78
    assert lines[2] == "=" * 78


def test_header_rule_lines_span_the_requested_width():
    out = to_text(_sheet(identity=Identity(name="X")), width=40)
    assert out.splitlines()[0] == "=" * 40


# --- characteristics ----------------------------------------------------

def test_characteristics_print_total_name_cost_roll_notes_verbatim():
    """total and roll are display strings from kirby-cost -- printed as-is,
    never reformatted. Every token below is distinct and non-overlapping so
    ordering can be checked unambiguously."""
    row = _char_row(name="Charname", total="Totvalue", roll="Rollvalue",
                    cost=99.0, notes="Notesvalue")
    out = to_text(_sheet(characteristics=(row,)))
    lines = [l for l in out.splitlines() if "Charname" in l]
    assert len(lines) == 1
    line = lines[0]
    for token in ("Totvalue", "Charname", "99", "Rollvalue", "Notesvalue"):
        assert token in line
    # total, then name, then cost, then roll, then notes -- the column
    # order the brief specifies.
    assert (line.index("Totvalue") < line.index("Charname")
            < line.index("99") < line.index("Rollvalue")
            < line.index("Notesvalue"))


def test_characteristic_notes_pass_through_plain_text():
    row = _char_row(notes="<i>Only</i> when STR &amp; DEX both apply")
    out = to_text(_sheet(characteristics=(row,)))
    assert "Only when STR & DEX both apply" in out
    assert "<i>" not in out


def test_characteristic_name_column_fits_the_longest_kirby_cost_name():
    """"Swimming" (8 chars) is the longest name kirby-cost produces; a
    narrower column pushes the Cost column out of alignment between rows."""
    swim = _char_row(name="Swimming", cost=2.0)
    run = _char_row(name="Running", cost=0.0)
    out = to_text(_sheet(characteristics=(swim, run)))
    swim_line = next(l for l in out.splitlines() if "Swimming" in l)
    run_line = next(l for l in out.splitlines() if "Running" in l
                    and "Swimming" not in l)
    assert swim_line.index("2") == run_line.index("0")


def test_characteristic_header_row_names_every_column():
    out = to_text(_sheet())
    header = next(l for l in out.splitlines() if "Val" in l)
    assert "Char" in header and "Cost" in header and "Roll" in header
    assert "Notes" in header


# --- sections / entries --------------------------------------------------

def test_a_non_empty_section_prints_its_heading_and_entries():
    section = Section(name="powers", entries=(_entry(display="Flight"),))
    out = to_text(_sheet(sections=(section,)))
    assert "POWERS" in out
    assert "Flight" in out


def test_an_empty_section_is_omitted_entirely():
    section = Section(name="skills", entries=())
    out = to_text(_sheet(sections=(section,)))
    assert "SKILLS" not in out


def test_an_entry_prints_cost_before_framework_not_cost():
    """A pooled slot's `cost` is 0; `cost_before_framework` is what it costs
    on its own, which is the number a reader expects beside it."""
    entry = _entry(cost=0.0, cost_before_framework=29.0, end=4.0,
                   display="Growth")
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)))
    line = next(l for l in out.splitlines() if "Growth" in l)
    numeric_prefix = line.split("Growth", 1)[0]
    assert "29" in numeric_prefix
    assert "0" not in numeric_prefix


def test_an_entry_prints_its_end():
    entry = _entry(cost_before_framework=6.0, end=3.0, display="Blast")
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)))
    line = next(l for l in out.splitlines() if "Blast" in l)
    assert "6" in line and "3" in line
    assert line.index("6") < line.index("3") < line.index("Blast")


def test_an_entry_with_a_parent_id_is_indented_under_its_pool():
    pool = _entry(id="7", name="Pool", display="Multipower", parent_id="")
    slot = _entry(id="8", name="Slot", display="Slot-display", parent_id="7")
    section = Section(name="powers", entries=(pool, slot))
    out = to_text(_sheet(sections=(section,)))
    pool_line = next(l for l in out.splitlines() if "Multipower" in l)
    slot_line = next(l for l in out.splitlines() if "Slot-display" in l)
    pool_indent = len(pool_line) - len(pool_line.lstrip(" "))
    slot_indent = len(slot_line) - len(slot_line.lstrip(" "))
    assert slot_indent > pool_indent


def test_display_strings_pass_through_plain_text():
    entry = _entry(display="<b>Killing Attack</b> plus <i>Flash</i>")
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)))
    assert "Killing Attack plus Flash" in out
    assert "<b>" not in out and "<i>" not in out


def test_a_long_display_string_wraps_with_continuations_aligned_under_text():
    long_display = ("Growth (+15 STR, +5 CON, +5 BODY, +2 PRE, -2 KB, +12"
                    " STR points) something long enough that it must wrap"
                    " onto a second line for certain, definitely for sure")
    entry = _entry(display=long_display, cost_before_framework=29.0, end=0.0)
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)), width=78)
    lines = out.splitlines()
    heading = next(i for i, l in enumerate(lines) if "POWERS" in l)
    start = heading + 1
    assert lines[start] == "-" * 78
    body_lines = []
    for l in lines[start + 1:]:
        if l == "":
            break
        body_lines.append(l)
    assert len(body_lines) >= 2, "display text did not wrap in this test"
    # cost(5) + end(5) + 2-space gap = the text column, per the brief's
    # worked example.
    continuation_indent = len(body_lines[1]) - len(body_lines[1].lstrip(" "))
    assert continuation_indent == 12
    for l in body_lines[1:]:
        assert l.startswith(" " * 12)


def test_no_display_line_exceeds_the_requested_width():
    long_display = "word " * 40
    entry = _entry(display=long_display)
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)), width=60)
    for line in out.splitlines():
        assert len(line) <= 60


def test_section_column_labels_sit_over_the_columns_they_name():
    """Cost and END print at columns 0-9 on every entry row (`prefix` in
    `_entry_lines`), so the heading's labels must line up there too, not at
    the far right where no number ever appears."""
    entry = _entry(cost_before_framework=29.0, end=4.0, display="Growth")
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)))
    lines = out.splitlines()
    heading = next(l for l in lines if "POWERS" in l)
    entry_line = next(l for l in lines if "Growth" in l)
    # Both fields are right-aligned in the same 5-char width, so it is the
    # SLICE (columns 0-4, columns 5-9) that must match, not the label's
    # first character -- "Cost" and "29" end-align, they don't start-align.
    assert heading[0:5].strip() == "Cost"
    assert entry_line[0:5].strip() == "29"
    assert heading[5:10].strip() == "END"
    assert entry_line[5:10].strip() == "4"


# --- footer / identity ----------------------------------------------------

def test_footer_states_the_character_s_cost():
    totals = Totals(total_points=350.0, available_points=39.0,
                    base_points=300.0, complication_points=50.0,
                    experience=25.0, complications_taken=50.0,
                    complications_shortfall=0.0, spendable_points=350.0,
                    points_unspent=0.0)
    out = to_text(_sheet(totals=totals))
    assert "Total Points: 300" in out
    assert "Experience: +25" in out
    assert "50 / 50 matching" in out
    assert "Spendable: 350" in out
    assert "Spent: 350" in out
    assert "Unspent: 0" in out


def test_footer_shows_negative_unspent_marked_over_budget():
    """Terminal output has no colour cue to fall back on -- the word "over"
    must be in the text itself."""
    totals = Totals(total_points=276.0, available_points=39.0,
                    base_points=270.0, complication_points=40.0,
                    experience=5.0, complications_taken=40.0,
                    complications_shortfall=0.0, spendable_points=275.0,
                    points_unspent=-1.0)
    out = to_text(_sheet(totals=totals))
    assert "Unspent: -1" in out
    assert "over" in out.lower()


def test_footer_shortfall_explains_itself():
    totals = Totals(total_points=200.0, available_points=0.0,
                    base_points=270.0, complication_points=40.0,
                    experience=5.0, complications_taken=20.0,
                    complications_shortfall=20.0, spendable_points=255.0,
                    points_unspent=55.0)
    out = to_text(_sheet(totals=totals))
    assert "20 / 40 matching" in out
    assert "shortfall cost 20" in out.lower()


def test_identity_block_prints_only_non_empty_fields():
    identity = Identity(name="Bokor", player_name="Player-name",
                        campaign_name="", genre="Genre-name")
    out = to_text(_sheet(identity=identity))
    assert "Player-name" in out
    assert "Genre-name" in out
    assert "Campaign:" not in out


def test_identity_block_formats_height_and_weight_readably():
    identity = Identity(name="Bokor", height=96.45669, weight=350.53)
    out = to_text(_sheet(identity=identity))
    assert "96.45669" not in out
    assert "350.53" not in out
    assert "8'0\"" in out
    assert "351 lbs" in out


def test_identity_block_omits_zero_height_and_weight():
    identity = Identity(name="Bokor", height=0.0, weight=0.0)
    out = to_text(_sheet(identity=identity))
    assert "Height:" not in out
    assert "Weight:" not in out


# --- prose ---------------------------------------------------------------

def test_prose_sections_print_only_when_non_empty_each_under_a_heading():
    prose = Prose(background="Background-words", personality="",
                  quote="Quote-words", tactics="", campaign_use="",
                  appearance="", notes=())
    out = to_text(_sheet(prose=prose))
    assert "BACKGROUND" in out and "Background-words" in out
    assert "QUOTE" in out and "Quote-words" in out
    assert "PERSONALITY" not in out
    assert "TACTICS" not in out
    assert "CAMPAIGN USE" not in out
    assert "APPEARANCE" not in out


def test_prose_notes_print_under_a_notes_heading_only_when_non_empty():
    out = to_text(_sheet(prose=Prose(notes=("Note-one", "", "Note-two"))))
    lines = out.splitlines()
    heading_idx = lines.index("NOTES")
    rule_idx = heading_idx + 1
    assert lines[rule_idx] == "-" * 78
    body = []
    for l in lines[rule_idx + 1:]:
        if l == "" or l == "-" * 78:
            break
        body.append(l)
    assert any("Note-one" in l for l in body)
    assert any("Note-two" in l for l in body)
    # The empty middle note contributes no line of its own -- an empty note
    # must not print as a blank body line between the two real ones.
    assert "" not in body


def test_all_prose_empty_prints_no_prose_headings():
    out = to_text(_sheet(prose=Prose()))
    for heading in ("BACKGROUND", "PERSONALITY", "QUOTE", "TACTICS",
                    "CAMPAIGN USE", "APPEARANCE", "NOTES"):
        assert heading not in out


def test_prose_paragraph_breaks_do_not_orphan_the_next_word():
    """An embedded blank line marks a paragraph break. Each paragraph must
    wrap on its own, with the first word of the second paragraph starting a
    real line of its own -- not sitting alone on a line by itself because a
    wrap chunk swallowed the blank line whole."""
    prose = Prose(background="First paragraph of words that goes on for a "
                             "good while so it definitely wraps around.\n\n"
                             "Second paragraph starts here and also runs on "
                             "for quite a while to force a second wrap.")
    out = to_text(_sheet(prose=prose))
    lines = out.splitlines()
    start = lines.index("BACKGROUND") + 2  # heading, then rule, then body
    rule = "-" * 78
    body = []
    for l in lines[start:]:
        if l == rule:
            break
        body.append(l)
    # Exactly one blank line separates the two paragraphs.
    blank_indices = [i for i, l in enumerate(body) if l == ""]
    assert blank_indices, "no blank line between paragraphs"
    second_para_start = body[blank_indices[0] + 1]
    assert second_para_start.startswith("Second paragraph starts here")
    # The lone-word-orphan bug looked like a line containing only "Second".
    assert not any(l.strip() == "Second" for l in body)


def test_prose_passes_through_plain_text():
    out = to_text(_sheet(prose=Prose(background="<i>Born</i> in Haiti")))
    assert "Born in Haiti" in out
    assert "<i>" not in out


# --- cost formatting -------------------------------------------------

def test_a_whole_number_cost_prints_without_a_trailing_dot_zero():
    entry = _entry(cost_before_framework=29.0, display="Whole-cost")
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)))
    line = next(l for l in out.splitlines() if "Whole-cost" in l)
    assert "29" in line
    assert "29.0" not in line


def test_a_fractional_cost_prints_its_fraction():
    """Power Lad's Leaping: 44.5 is a real active-point cost, not a rounding
    artifact -- it must survive to the rendered sheet."""
    entry = _entry(cost_before_framework=44.5, display="Fractional-cost")
    section = Section(name="powers", entries=(entry,))
    out = to_text(_sheet(sections=(section,)))
    line = next(l for l in out.splitlines() if "Fractional-cost" in l)
    assert "44.5" in line


# --- end to end -------------------------------------------------------

@pytest.mark.skipif(not os.environ.get("KIRBY_COST_HDT"),
                    reason="requires KIRBY_COST_HDT and a character file")
def test_a_real_character_renders_end_to_end():
    hdc = os.environ.get("KIRBY_SHEET_HDC")
    if not hdc:
        pytest.skip("requires KIRBY_SHEET_HDC")
    sheet = sheet_from_hdc(hdc)
    out = to_text(sheet)
    assert sheet.identity.name.upper() in out
    assert isinstance(out, str) and out.strip() != ""

    lines = out.splitlines()
    for section in sheet.sections:
        if not section.entries:
            continue
        heading_line = next(l for l in lines if section.name.upper() in l)
        heading_idx = lines.index(heading_line)
        rule_idx = heading_idx + 1
        body_start = rule_idx + 1
        body = []
        for l in lines[body_start:]:
            if l == "":
                break
            body.append(l)
        # `_entry_lines` is production code, not a re-derivation: it is the
        # exact function that produced this section's body, so the number
        # of lines it says an entry takes (1, or more if the display
        # wrapped) is the ground truth to compare the body against.
        expected = sum(len(as_text._entry_lines(entry, width=78))
                       for entry in section.entries)
        assert len(body) == expected, (
            f"{section.name}: {len(body)} lines under the heading, "
            f"expected {expected} for {len(section.entries)} entries")
