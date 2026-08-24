"""Identity and the point aggregates, against Hero Designer's own output."""
import pytest

from tests.corpus import (character_path, oracle_path, template_path,
                          why_unavailable)
from tests.keys import both, compare

pytestmark = pytest.mark.skipif(
    not (oracle_path() and character_path() and template_path()),
    reason=why_unavailable() or "oracle, character and template all available")

IDENTITY = ["character_name", "alt_identities", "player_name", "campaign",
            "genre", "gamemaster", "height", "weight", "hair_color", "eye_color"]

POINTS = ["characteristic_total_pts", "total_points", "base_points",
          "disad_points", "disad_points_allowed", "skill_etc_points",
          "power_points", "xp_earned", "xp_unspent", "xp_spent"]


def test_identity_keys_match_hero_designer():
    ours, theirs = both(IDENTITY)
    assert compare(ours, theirs, IDENTITY) == 10


def test_points_keys_match_hero_designer():
    ours, theirs = both(POINTS)
    assert compare(ours, theirs, POINTS) == 10


def test_the_point_aggregates_are_not_all_the_same_number():
    """The sums are the one place this layer does arithmetic, and a mistake
    that wired several tokens to the same total would still look plausible
    key by key. Bokor's differ (138 characteristics, 41 skills-etc, 97
    powers), so a collapsed set is caught here rather than in a byte diff."""
    ours, _ = both(POINTS)
    distinct = {ours[k] for k in
                ("characteristic_total_pts", "skill_etc_points", "power_points")}
    assert len(distinct) == 3, f"aggregates collapsed to: {distinct}"
