"""Sheet -> JSON."""
import json

from kirby_sheet.build import build_sheet
from kirby_sheet.formats.as_json import to_json
from tests.test_build import _hero, _obj


def _doc(**kw):
    return json.loads(to_json(build_sheet(_hero(**kw))))


def test_it_is_valid_json():
    assert isinstance(_doc(), dict)


def test_the_top_level_shape_is_stable():
    """Consumers key off this; changing it is a breaking change."""
    assert sorted(_doc()) == ["characteristics", "identity", "prose", "sections", "totals"]


def test_identity_round_trips():
    assert _doc(name="Bokor", gm="Gamemaster")["identity"]["name"] == "Bokor"


def test_sections_are_a_list_of_named_objects_not_a_bare_map():
    """A list keeps the sheet's ORDER, which a JSON object does not promise."""
    sections = _doc()["sections"]
    assert isinstance(sections, list)
    assert [s["name"] for s in sections] == ["skills", "perks", "talents",
                                             "powers", "equipment", "martial_arts", "complications"]


def test_an_entry_exposes_both_costs():
    doc = _doc(powers=[_obj(real_cost=0, real_cost_pre_list=29)])
    entry = next(s for s in doc["sections"] if s["name"] == "powers")["entries"][0]
    assert entry["cost"] == 0 and entry["cost_before_framework"] == 29


def test_display_strings_survive_verbatim():
    doc = _doc(powers=[_obj(column2_output='Growth (+15 STR, "x2")')])
    entry = next(s for s in doc["sections"] if s["name"] == "powers")["entries"][0]
    assert entry["display"] == 'Growth (+15 STR, "x2")'


def test_non_ascii_is_not_escaped():
    """ensure_ascii=False. A sheet carries player-written prose; \\u00e9 in a
    file a human reads is a worse default than the character itself."""
    out = to_json(build_sheet(_hero(name="Café")))
    assert "Café" in out and "\\u00e9" not in out


def test_indent_none_produces_one_line():
    out = to_json(build_sheet(_hero()), indent=None)
    assert "\n" not in out


# --- the 6E points fields, alongside HD's own ------------------------------
#
# JSON is the full record: both `available_points` (HD's 5E-style figure)
# and `points_unspent` (the 6E figure) must be present, with their DIFFERENT
# values -- a test that could not tell the two apart would be worthless
# here, since a serialiser bug that dropped one and duplicated the other
# would still show "some number" in the document.

def test_totals_carries_both_hds_figure_and_the_6e_figure_distinctly():
    doc = _doc(available_points=39.0, points_unspent=-1.0)
    totals = doc["totals"]
    assert totals["available_points"] == 39.0
    assert totals["points_unspent"] == -1.0
    assert totals["available_points"] != totals["points_unspent"]


def test_totals_carries_every_6e_field():
    doc = _doc(base_points=270, disad_points=40, experience=5,
               disads_used=40, complications_shortfall=0.0,
               spendable_points=275.0, total_points=276.0,
               points_unspent=-1.0)
    totals = doc["totals"]
    assert totals["base_points"] == 270
    assert totals["complication_points"] == 40
    assert totals["experience"] == 5
    assert totals["complications_taken"] == 40
    assert totals["complications_shortfall"] == 0.0
    assert totals["spendable_points"] == 275.0
    assert totals["total_points"] == 276.0
    assert totals["points_unspent"] == -1.0
