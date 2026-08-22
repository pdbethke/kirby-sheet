"""Sheet -> JSON."""
import json

from kirby_sheet.build import build_sheet
from kirby_sheet.formats.as_json import to_json
from tests.test_build import _char, _hero, _obj


def _doc(**kw):
    return json.loads(to_json(build_sheet(_hero(**kw))))


def test_it_is_valid_json():
    assert isinstance(_doc(), dict)


def test_the_top_level_shape_is_stable():
    """Consumers key off this; changing it is a breaking change."""
    assert sorted(_doc()) == ["characteristics", "identity", "sections", "totals"]


def test_identity_round_trips():
    assert _doc(name="Bokor", gm="Bill")["identity"]["name"] == "Bokor"


def test_sections_are_a_list_of_named_objects_not_a_bare_map():
    """A list keeps the sheet's ORDER, which a JSON object does not promise."""
    sections = _doc()["sections"]
    assert isinstance(sections, list)
    assert [s["name"] for s in sections] == ["skills", "perks", "talents",
                                             "powers", "martial_arts", "complications"]


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
