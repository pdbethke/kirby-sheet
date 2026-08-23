"""Sheet -> HTML -- a standalone document, with HD's own markup preserved
in display strings and everything a person typed escaped."""
from __future__ import annotations

from kirby_sheet.formats.as_html import to_html
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


# --- document shape -------------------------------------------------

def test_document_starts_with_doctype():
    out = to_html(_sheet())
    assert out.startswith("<!DOCTYPE html>")


def test_exactly_one_html_open_and_close_tag():
    out = to_html(_sheet())
    assert out.count("<html") == 1
    assert out.count("</html>") == 1


# --- escaping: the subtle part --------------------------------------

def test_entry_display_markup_survives_unescaped():
    entry = _entry(display="<i>Name:</i>  Power")
    sheet = _sheet(sections=(Section(name="powers", entries=(entry,)),))

    out = to_html(sheet)

    assert "<i>Name:</i>" in out
    assert "&lt;i&gt;" not in out


def test_characteristic_notes_markup_survives_unescaped():
    row = _char_row(notes="<b>Bold note</b>")
    sheet = _sheet(characteristics=(row,))

    out = to_html(sheet)

    assert "<b>Bold note</b>" in out
    assert "&lt;b&gt;" not in out


def test_background_prose_is_escaped():
    sheet = _sheet(prose=Prose(background="a < b & c"))

    out = to_html(sheet)

    assert "&lt;" in out
    assert "&amp;" in out
    assert "a < b & c" not in out


def test_alternate_identity_is_escaped():
    sheet = _sheet(identity=Identity(name="Bokor", alternate_identities="<script>"))

    out = to_html(sheet)

    assert "<script>" not in out
    assert "&lt;script&gt;" in out


# --- sections ---------------------------------------------------------

def test_empty_sections_are_omitted():
    sheet = _sheet(sections=(Section(name="skills", entries=()),
                              Section(name="powers", entries=(_entry(),))))

    out = to_html(sheet)

    assert "skills" not in out.lower()
    assert "powers" in out.lower()


def test_entry_with_parent_id_is_marked_nested():
    """This backend's chosen mechanism: a `nested` CSS class on the <tr>."""
    parent = _entry(id="pool-id", name="Pool", display="Pool-display")
    child = _entry(id="slot-id", name="Slot", display="Slot-display",
                   parent_id="pool-id")
    sheet = _sheet(sections=(Section(name="powers", entries=(parent, child)),))

    out = to_html(sheet)

    assert 'class="nested"' in out
    # The child row (not the parent) is the one carrying the class.
    slot_index = out.index("Slot-display")
    nested_index = out.index('class="nested"')
    pool_index = out.index("Pool-display")
    assert nested_index < slot_index
    assert nested_index > pool_index


def test_cost_before_framework_is_printed_not_cost():
    entry = _entry(cost=0.0, cost_before_framework=42.0)
    sheet = _sheet(sections=(Section(name="powers", entries=(entry,)),))

    out = to_html(sheet)

    assert "42" in out


# --- totals -------------------------------------------------------------

def test_totals_appear_with_their_values():
    totals = Totals(total_points=123.0, base_points=100.0,
                    complication_points=25.0, experience=3.0)
    sheet = _sheet(totals=totals)

    out = to_html(sheet)

    assert "123" in out
    assert "100" in out
    assert "25" in out
    assert "3" in out


# --- title ----------------------------------------------------------------

def test_title_defaults_to_character_name():
    sheet = _sheet(identity=Identity(name="Bokor"))

    out = to_html(sheet)

    assert "<title>Bokor</title>" in out


def test_title_parameter_overrides_default():
    sheet = _sheet(identity=Identity(name="Bokor"))

    out = to_html(sheet, title="Custom Title")

    assert "<title>Custom Title</title>" in out
    assert "<title>Bokor</title>" not in out
