"""The seven repeated sections, against Hero Designer's own output.

Sections are not addressable by top-level key -- their item keys are indented
and repeat -- so these compare whole section BODIES.
"""
import re

import pytest

from tests.corpus import (character_path, oracle_path, template_path,
                          why_unavailable)
from tests.keys import PINNED
from tests.oracle import normalise, oracle_export

pytestmark = pytest.mark.skipif(
    not (oracle_path() and character_path() and template_path()),
    reason=why_unavailable() or "oracle, character and template all available")

SECTIONS = ["skills", "martial_arts", "perks", "talents", "powers",
            "equipment", "disads"]


def _bodies(document):
    out = {}
    for i, name in enumerate(SECTIONS):
        end = SECTIONS[i + 1] if i + 1 < len(SECTIONS) else None
        pattern = (rf"^{name}:\n(.*?)(?=^{end}:)" if end
                   else rf"^{name}:\n(.*)\Z")
        match = re.search(pattern, document, re.S | re.M)
        out[name] = match.group(1) if match else ""
    return out


def _ours_and_theirs():
    from kirby_cost.io.hdc_loader import HDCLoader
    from kirby_sheet.render import render
    from kirby_sheet.template import Template
    character, template = character_path(), template_path()
    hero = HDCLoader().load_file(str(character))
    ours = render(Template.from_path(template), hero,
                  character_file=character.name, **PINNED)
    return normalise(ours), normalise(oracle_export(template, character))


def test_every_section_body_matches_hero_designer():
    ours, theirs = _ours_and_theirs()
    mine, hd = _bodies(ours), _bodies(theirs)
    differing = [s for s in SECTIONS if mine[s] != hd[s]]
    if differing:
        s = differing[0]
        raise AssertionError(
            f"sections differing: {differing}\n\n--- ours ({s}) ---\n"
            f"{mine[s][:900]}\n--- HD ({s}) ---\n{hd[s][:900]}")


def test_item_counts_match_per_section():
    ours, theirs = _ours_and_theirs()
    mine, hd = _bodies(ours), _bodies(theirs)
    counts = {s: (mine[s].count("\n - "), hd[s].count("\n - ")) for s in SECTIONS}
    wrong = {s: c for s, c in counts.items() if c[0] != c[1]}
    assert not wrong, f"(ours, HD) item counts differ: {wrong}"


def test_the_comparison_saw_populated_sections():
    """THE GUARD THAT MATTERS.

    An empty section compares equal on both sides, so the body test above
    passes for a character who owns nothing -- and BOTH of Hero Designer's
    equipment failure modes produce exactly that (see the spec: a character
    whose RULES lack EQUIPMENTALLOWED, or an object lifted from a POWERS
    section without PRICE/WEIGHT/CARRIED, is dropped silently). Name what was
    actually exercised, and fail if it was nothing.
    """
    _, theirs = _ours_and_theirs()
    hd = _bodies(theirs)
    populated = {s: hd[s].count("\n - ") for s in SECTIONS if hd[s].strip()}
    print(f"sections populated in the oracle output: {populated}")
    assert populated, "the corpus character has no sections at all"
    # At least one section with at least one ITEM. An earlier version demanded
    # four populated sections, which was a number about Bokor rather than
    # about the gate -- Power Lad legitimately has three and failed it. What
    # actually makes the body comparison vacuous is comparing nothing.
    assert any(count > 0 for count in populated.values()), (
        f"every populated section is item-less: {populated}")
