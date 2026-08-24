"""PER Roll, PRE Attack and the two defence totals."""
import pytest

from tests.corpus import (character_path, oracle_path, template_path,
                          why_unavailable)
from tests.keys import both, compare

pytestmark = pytest.mark.skipif(
    not (oracle_path() and character_path() and template_path()),
    reason=why_unavailable() or "oracle, character and template all available")

KEYS = ["per_roll", "pre_attack", "mental_def", "power_def"]


def _value(line: str) -> str:
    return line.split(":", 1)[1].strip()


def test_derived_keys_match_hero_designer():
    ours, theirs = both(KEYS)
    assert compare(ours, theirs, KEYS) == 4


def test_per_roll_and_pre_attack_are_not_crossed():
    """Both are short strings off a characteristic, so a crossed wire between
    them would still look plausible. They are compared as VALUES -- comparing
    the whole lines would differ by the key prefix alone and prove nothing."""
    ours, theirs = both(KEYS)
    assert _value(ours["per_roll"]) == _value(theirs["per_roll"])
    assert _value(ours["pre_attack"]) == _value(theirs["pre_attack"])
    # A PER Roll reads like "12-" and a PRE Attack like "5d6"; if these ever
    # coincide the assertion above still holds, so this only guards the
    # obvious swap.
    if _value(theirs["per_roll"]) != _value(theirs["pre_attack"]):
        assert _value(ours["per_roll"]) != _value(ours["pre_attack"])
