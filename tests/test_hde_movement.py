"""The eight IF_ movement blocks and their totals."""
import pytest

from tests.corpus import (character_path, oracle_path, template_path,
                          why_unavailable)
from tests.keys import both, compare

pytestmark = pytest.mark.skipif(
    not (oracle_path() and character_path() and template_path()),
    reason=why_unavailable() or "oracle, character and template all available")

#: Every movement key the shipped 6E template can emit. Which of them HD
#: actually prints depends on the character -- an unowned mode has its whole
#: IF_ block stripped, so the line does not appear at all.
ALL_KEYS = ["running", "running_noncom", "swimming", "swimming_noncom",
            "flight", "flight_noncom", "gliding", "gliding_noncom",
            "swinging", "swinging_noncom", "teleportation",
            "teleportation_noncom", "tunneling", "tunneling_noncom",
            "horiz_leap", "vert_leap", "horiz_leap_noncom"]


def test_the_movement_keys_hero_designer_emits_all_match():
    """Compared against whatever HD emits for THIS character, rather than a
    hardcoded list: Bokor has no Flight and Power Lad does, and pinning one
    character's modes would make this pass for the wrong reason on the other."""
    ours, theirs = both(ALL_KEYS)
    present = [k for k in ALL_KEYS if k in theirs]
    assert present, "the oracle emitted no movement keys at all"
    assert compare(ours, theirs, present) == len(present)


def test_we_emit_no_movement_line_hero_designer_omits():
    """The other half, and the one a per-key sweep cannot catch: a mode the
    character does not own must produce NO line. Emitting an empty
    `flight:` would be a diff, so absence is asserted as hard as presence."""
    ours, theirs = both(ALL_KEYS)
    leaked = [k for k in ALL_KEYS if k in ours and k not in theirs]
    assert leaked == [], f"we emitted movement lines HD does not: {leaked}"


def test_the_character_exercises_both_paths():
    """Names what was actually proven. A character owning every mode, or
    none, would make one of the two tests above vacuous."""
    _, theirs = both(ALL_KEYS)
    present = [k for k in ALL_KEYS if k in theirs]
    absent = [k for k in ALL_KEYS if k not in theirs]
    print(f"movement present: {present}\nmovement absent: {absent}")
    assert present, "no mode present - the match test proves nothing"
    assert absent, "no mode absent - the omission test proves nothing"
