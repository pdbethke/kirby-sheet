"""THE GATE: our bytes against Hero Designer's.

minimal.hde contains only tokens this milestone implements, so every other
substitution generateOutput performs is a no-op and the two documents should
match exactly. Anything less than exact equality here is the machine moving
text it should not have touched.

Skips unless the oracle and a character are configured.
"""
from pathlib import Path

import pytest

from kirby_sheet.render import render
from kirby_sheet.template import Template
from tests.corpus import character_path, oracle_path, why_unavailable
from tests.oracle import normalise, oracle_export

MINIMAL = Path(__file__).parent / "fixtures" / "minimal.hde"

pytestmark = pytest.mark.skipif(
    not (oracle_path() and character_path()),
    reason=why_unavailable() or "oracle and character both available",
)


def _ours(character):
    return render(
        Template.from_path(MINIMAL),
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
    """The milestone's real assertion."""
    character = character_path()
    hd = normalise(oracle_export(MINIMAL, character))
    ours = normalise(_ours(character))
    assert ours == hd
