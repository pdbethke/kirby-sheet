"""The paired <!--STR-->...<!--/STR--> blocks, against HD's own output.

The template's form is a block per characteristic whose body carries GENERIC
sub-tokens:

    str_val: <!--STR--><!--TOTAL-->
    str_pts: <!--COST-->
    str_roll: <!--ROLL--><!--/STR-->

TOTAL, COST, ROLL and NOTES recur in every block and mean "of THIS
characteristic". That is why this cannot be a flat substitution, and why the
discrimination test below matters more than the count.
"""
import pytest

from tests.corpus import (character_path, oracle_path, template_path,
                          why_unavailable)
from tests.keys import both, compare

pytestmark = pytest.mark.skipif(
    not (oracle_path() and character_path() and template_path()),
    reason=why_unavailable() or "oracle, character and template all available")

KEYS = ("str_val str_pts str_roll str_damage str_lift str_end "
        "dex_val dex_pts dex_roll con_val con_pts con_roll "
        "int_val int_pts int_roll ego_val ego_pts ego_roll "
        "pre_val pre_pts pre_roll ocv_val ocv_pts dcv_val dcv_pts "
        "omcv_val omcv_pts dmcv_val dmcv_pts spd_val spd_pts phases "
        "pd_val pd_pts pd r_pd ed_val ed_pts ed r_ed "
        "rec_val rec_pts end_val end_pts body_val body_pts body_roll "
        "stun_val stun_pts").split()




def test_every_characteristic_key_matches_hero_designer():
    ours, theirs = both(KEYS)
    assert compare(ours, theirs, KEYS) == 49



def _value(line: str) -> str:
    """The part after `key:`.

    Comparing whole lines between two DIFFERENT keys is meaningless -- they
    always differ by their key prefix. The first version of the two tests
    below did exactly that and passed while every token was still an
    unsubstituted marker. Compare values, or compare nothing.
    """
    return line.split(":", 1)[1].strip()


def test_the_generic_subtokens_resolve_per_block_not_globally():
    """COST appears inside every characteristic block. Resolved globally,
    every *_pts line would carry the same number. Bokor's differ (STR 5,
    DEX 16, PRE 15), so this catches a flat substitution that the key-by-key
    comparison alone might not explain."""
    points = [k for k in KEYS if k.endswith("_pts")]
    ours, theirs = both(points)
    mine = [_value(ours[k]) for k in points]
    hd = [_value(theirs[k]) for k in points]
    # Compared against HD rather than asserting they are all distinct: a
    # character CAN legitimately pay the same for two characteristics, and
    # Ravel does. What cannot happen is ours collapsing to one value while
    # HD's vary -- that is the signature of COST resolved globally instead of
    # inside each block.
    assert not (len(set(mine)) == 1 and len(set(hd)) > 1), (
        f"every point value came out {mine[0]!r} while HD's vary: {sorted(set(hd))}")
    assert len(set(mine)) == len(set(hd)), (
        f"we produced {len(set(mine))} distinct point values, HD {len(set(hd))}")


def test_a_characteristics_own_tokens_stay_inside_its_block():
    """STR_LIFT and STR_END live in the STR block. If block boundaries were
    wrong they could leak into a neighbouring characteristic's lines, which
    would still look like plausible output."""
    ours, theirs = both(KEYS)
    assert _value(ours["str_lift"]), "str_lift rendered empty"
    assert "<!--" not in _value(ours["str_lift"]), "str_lift left a marker"
    # Compared against HD, not asserted distinct. Two characteristics CAN
    # legitimately roll the same -- the Lawman's STR and DEX are both 10 --
    # and demanding otherwise was a fact about Bokor, not about the renderer.
    assert _value(ours["dex_roll"]) == _value(theirs["dex_roll"])
    assert _value(ours["str_roll"]) == _value(theirs["str_roll"])
