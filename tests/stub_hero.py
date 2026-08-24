"""A stand-in character for tests that need one but not a real one.

The `.hde` backend renders from a LoadedHero, so even a test about the fixed
opening has to pass something. Loading a real character would make every such
test corpus-gated, which would hide the unit tests behind the oracle gate for
no benefit.

EVERY FIELD GETS A DISTINCT VALUE. Equal stub values make a crossed wire
between two tokens invisible, and that mistake has already shipped in this
project. Numbers are distinct too, and deliberately not round.

This grows as phases land. That is intended: a field appearing here is a
record of what the backend reads.
"""
from __future__ import annotations

from types import SimpleNamespace


def stub_hero(**overrides):
    """A hero-shaped object. Pass overrides to vary one field at a time."""
    fields = dict(
        # identity -- each value names itself so a swap is obvious in a diff
        name="STUB-NAME",
        alternate_identities="STUB-ALTIDS",
        player_name="STUB-PLAYER",
        campaign_name="STUB-CAMPAIGN",
        genre="STUB-GENRE",
        gm="STUB-GM",
        hair_color="STUB-HAIR",
        eye_color="STUB-EYE",
        # 73 inches -> 6' 1"; 181 lbs. Distinct, and neither is a round number
        # that could match the other by coincidence.
        height=73.0,
        weight=181.0,
        # points -- all different, so a token wired to the wrong one shows up
        experience=11,
        base_points=175,
        disad_points=37,
        total_points=213.0,
        disads_used=23,
        # sections -- empty by default; a test that needs items passes its own
        characteristics=(),
        skills=(),
        perks=(),
        talents=(),
        maneuvers=(),
        martial_arts=(),
        powers=(),
        equipment=(),
        complications=(),
    )
    fields.update(overrides)
    return SimpleNamespace(**fields)
