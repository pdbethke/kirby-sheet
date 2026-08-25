"""THE GATE: our bytes against Hero Designer's.

minimal.hde contains only tokens this milestone implements, so every other
substitution generateOutput performs is a no-op and the two documents should
match exactly. Anything less than exact equality here is the machine moving
text it should not have touched.

Skips unless the oracle and a character are configured.
"""
import re
from pathlib import Path

import pytest

from kirby_sheet.render import render
from kirby_sheet.template import Template
from tests.corpus import (character_path, oracle_path, template_path,
                          why_unavailable)
from tests.oracle import normalise, oracle_export

MINIMAL = Path(__file__).parent / "fixtures" / "minimal.hde"

pytestmark = pytest.mark.skipif(
    not (oracle_path() and character_path()),
    reason=why_unavailable() or "oracle and character both available",
)


def _hero(character):
    """minimal.hde uses only opening-region tokens, which do not read the
    character -- but render() requires one, and loading the real character is
    honest where a None would quietly assert something this gate does not
    test."""
    from kirby_sheet.build import hero_from_hdc
    return hero_from_hdc(character)


def _ours(character):
    # timestamp, export_id and save_timestamp are all passed the same literal
    # "<PINNED>", and normalise() collapses HD's three real values to that
    # same string too — so this gate cannot tell those three arguments apart
    # and would not catch them being cross-wired with each other. That case
    # is covered separately by
    # test_render_opening.py::test_the_four_volatile_tokens_are_filled, which
    # uses distinct sentinels per argument.
    return render(
        Template.from_path(MINIMAL),
        _hero(character),
        app_version="headless-fork",
        timestamp="<PINNED>",
        export_id="<PINNED>",
        save_timestamp="<PINNED>",
        character_file=character.name,
    )


def test_no_markers_survive_on_either_side():
    """Checked first: it names WHICH marker leaked, where a byte diff would
    only say the documents differ."""
    character = character_path()
    hd = oracle_export(MINIMAL, character)
    ours = _ours(character)
    for marker in ("<!--TEMPLATE_NAME-->", "<!--TEMPLATE_DESCRIPTION-->",
                   "<!--FILE_EXTENSION-->", "<!--APP_VERSION-->",
                   "<!--TIMESTAMP-->", "<!--EXPORT_ID-->",
                   "<!--CHARACTER_SAVE_TIMESTAMP-->", "<!--CHARACTER_FILE-->"):
        assert marker not in hd, f"{marker} survived in HD's output"
        assert marker not in ours, f"{marker} survived in ours"


def test_the_documents_are_byte_identical():
    """The milestone's real assertion.

    minimal.hde deliberately contains one latin-1 non-ASCII byte (\\xa0, a
    non-breaking space) in a static <p> line in the <body> — a part of the
    document that render() does not consume or remove, so the byte survives
    into the compared output. (It was first placed in the
    TEMPLATE_DESCRIPTION block, which render() strips before comparison, so
    that placement never exercised anything — the body is load-bearing
    here.) template.py deliberately mangles latin-1 bytes the way
    `new String(data)` does on a UTF-8 JVM, and until this byte was added
    that mangling was asserted only by a unit test encoding our own belief
    about Java's behaviour — nothing checked that belief against HD itself.
    With the byte present, this gate proves the mangling against the real
    oracle output instead.
    """
    character = character_path()
    hd = normalise(oracle_export(MINIMAL, character))
    ours = normalise(_ours(character))
    assert ours == hd


# ---------------------------------------------------------------------------
# THE GATE: the whole shipped 6E template, not a sample of keys.
# ---------------------------------------------------------------------------

_needs_template = pytest.mark.skipif(
    template_path() is None,
    reason=why_unavailable() or "KIRBY_SHEET_HDE is configured")


def _render_shipped(character):
    from kirby_sheet.build import hero_from_hdc
    template = template_path()
    return render(Template.from_path(template), hero_from_hdc(character),
                  app_version="headless-fork", timestamp="<PINNED>",
                  export_id="<PINNED>", save_timestamp="<PINNED>",
                  character_file=character.name)


@_needs_template
def test_no_marker_survives_in_the_shipped_template():
    """Checked before the byte diff, because it NAMES the token that leaked
    where a diff would only say the documents differ."""
    ours = _render_shipped(character_path())
    leaked = sorted(set(re.findall(r"<!--/?[A-Za-z0-9_]+-->", ours)))
    assert leaked == [], f"unresolved tokens: {leaked}"


#: Byte fidelity is proven for: Bokor (Heroic6E), Ravel and Power Lad
#: (Superheroic6E), and "Lawman (Armed)" -- the last because the three
#: authored characters carry NO EQUIPMENT, so nothing else exercises
#: getEquipmentString beyond rendering it empty. Point KIRBY_SHEET_HDC at an
#: equipment-bearing character to exercise that section.
#:
#: KNOWN GAP, one key, on a hand-built character only: a power whose options
#: are SENSE GROUPS declared by GROUPCOST/SENSECOST rather than
#: TARGETINGCOST -- ADJACENTFIXED is the one to hand -- gets no synthetic
#: options from hdt_provider._sense_group_options, so its OPTION prints
#: empty where HD prints "Sight Group". None of the four characters above
#: has one; "Ravel (CSI Kit)" does.
@_needs_template
def test_the_shipped_6e_template_is_byte_identical():
    """The whole point of the backend.

    minimal.hde proved the opening; this proves the port. Every token the
    shipped template uses, every section, every item -- one document,
    compared whole, with only the four volatile values normalised.
    """
    character = character_path()
    ours = normalise(_render_shipped(character))
    theirs = normalise(oracle_export(template_path(), character))
    assert ours == theirs
