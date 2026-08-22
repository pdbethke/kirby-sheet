"""LoadedHero -> Sheet. Selection and shape, never arithmetic."""
from types import SimpleNamespace

import pytest

from kirby_sheet.build import build_sheet


class MockCharacteristic:
    """Stub characteristic matching the shape of real kirby-cost Characteristic."""
    def __init__(self, xmlid="STR", display="STR", characteristic_value=5.0, get_base_value=10.0,
                 real_cost=5.0, active_cost=5.0, value_display="15", roll="12-",
                 display_notes="", **kw):
        self.xmlid = xmlid
        self.display = display
        self._characteristic_value = characteristic_value
        self._get_base_value = get_base_value
        self.real_cost = real_cost
        self.active_cost = active_cost
        self._value_display = value_display
        self._roll = roll
        self.display_notes = display_notes
        for k, v in kw.items():
            setattr(self, k, v)

    def characteristic_value(self):
        return self._characteristic_value

    def get_base_value(self):
        return self._get_base_value

    def value_display(self):
        return self._value_display

    def roll(self):
        return self._roll


def _char(xmlid="STR-xmlid", **kw):
    """Every numeric field differs, so a test can tell which is which. A stub
    whose values coincide cannot detect two fields being swapped. `xmlid` and
    `display` are also distinct from each other, so a test can tell whether
    the row's `name` came from `char.display` or from `char.xmlid`."""
    base = dict(xmlid=xmlid, display="Strength-display",
                characteristic_value=15.0,   # distinct
                get_base_value=10.0,         # distinct
                real_cost=5.0,               # distinct
                active_cost=7.0,             # distinct
                value_display="15", roll="12-", display_notes="")
    base.update(kw)
    return MockCharacteristic(**base)


def _obj(**kw):
    """Every field differs from every other, including the ones that are
    easy to leave untested (`id`, `end`, `parent_id`) and the ones a swap
    could hide behind (`alias` vs `xmlid`)."""
    base = dict(id=1, name="Entry-name", alias="Entry-alias", xmlid="ENTRY-XMLID",
                column2_output="Growth ...", real_cost=29, real_cost_pre_list=31,
                active_cost=44, end_usage=3, parent_id="")
    base.update(kw)
    return SimpleNamespace(**base)


def _hero(**kw):
    base = dict(name="Bokor", alternate_identities="Alt-identities",
                player_name="Player-name", campaign_name="Campaign-name",
                genre="Genre", gm="GM-name", hair_color="Hair-color",
                eye_color="Eye-color",
                characteristics=[], powers=[], skills=[], perks=[], talents=[],
                complications=[], martial_arts=[],
                total_points=276.0, available_points=39.0, base_points=270,
                disad_points=40, experience=5)
    base.update(kw)
    return SimpleNamespace(**base)


def test_identity_is_carried_across():
    s = build_sheet(_hero(name="Bokor", gm="Bill"))
    assert s.identity.name == "Bokor" and s.identity.gm == "Bill"


def test_a_characteristic_row_takes_its_display_strings_verbatim():
    """total and roll are already exact strings in kirby-cost. Reformatting
    them here would be re-deriving a value that has a source of truth."""
    s = build_sheet(_hero(characteristics=[_char(value_display="15", roll="12-")]))
    assert (s.characteristics[0].total, s.characteristics[0].roll) == ("15", "12-")


def test_characteristic_numbers_are_floats_not_truncated():
    """A narrowing `int()` cast is a computation, and this layer does none.
    LEAPING's real_cost of -1.5 must survive as -1.5, not become -1."""
    s = build_sheet(_hero(characteristics=[_char(xmlid="LEAPING",
                                                  characteristic_value=15.5,
                                                  get_base_value=10.5,
                                                  real_cost=-1.5,
                                                  active_cost=44.5)]))
    row = s.characteristics[0]
    assert (row.value, row.base, row.cost, row.active_cost) == (15.5, 10.5, -1.5, 44.5)
    assert isinstance(row.value, float) and isinstance(row.cost, float)


def test_entry_numbers_are_floats_not_truncated():
    """Power Lad's Leaping: real_cost_pre_list=44.5 and active_cost=44.5.
    `int()` would silently turn both into 44, breaking the one arithmetic
    relationship a reader checks -- that entries sum to the total."""
    s = build_sheet(_hero(powers=[_obj(real_cost=44.5, real_cost_pre_list=44.5,
                                       active_cost=44.5, end_usage=0.5)]))
    e = s.sections[[x.name for x in s.sections].index("powers")].entries[0]
    assert (e.cost, e.cost_before_framework, e.active_cost, e.end) == (44.5, 44.5, 44.5, 0.5)


def test_an_entry_carries_both_costs_distinctly():
    """A pooled slot costs the character nothing and costs 29 on its own."""
    s = build_sheet(_hero(powers=[_obj(real_cost=0, real_cost_pre_list=29)]))
    e = s.sections[[x.name for x in s.sections].index("powers")].entries[0]
    assert (e.cost, e.cost_before_framework) == (0, 29)


def test_display_is_kirby_costs_column2_output_verbatim():
    s = build_sheet(_hero(powers=[_obj(column2_output="Growth (+15 STR)")]))
    e = s.sections[[x.name for x in s.sections].index("powers")].entries[0]
    assert e.display == "Growth (+15 STR)"


def test_every_section_is_present_even_when_empty():
    s = build_sheet(_hero())
    assert [x.name for x in s.sections] == ["skills", "perks", "talents",
                                            "powers", "martial_arts", "complications"]


def test_totals_are_carried_across():
    s = build_sheet(_hero(total_points=276.0, available_points=39.0))
    assert (s.totals.total_points, s.totals.available_points) == (276.0, 39.0)


def test_each_characteristic_field_takes_its_own_source():
    """A type check cannot catch two fields being swapped, and every other
    test here would pass if `value` held the base and `base` held the current
    value. Each stub value is distinct so this test can tell them apart."""
    row = build_sheet(_hero(characteristics=[_char()])).characteristics[0]
    assert row.xmlid == "STR-xmlid"       # char.xmlid, not char.display
    assert row.name == "Strength-display"  # char.display, not char.xmlid
    assert row.value == 15          # characteristic_value(), not base
    assert row.base == 10           # get_base_value(), not the current value
    assert row.cost == 5            # real_cost, not active_cost
    assert row.active_cost == 7     # active_cost, not real_cost
    assert row.total == "15"        # value_display(), verbatim
    assert row.roll == "12-"        # roll(), verbatim


def test_each_identity_field_takes_its_own_source():
    """Every field of _hero() is distinct, so a test can tell two fields
    apart if they were swapped -- as `hair_color`/`eye_color` were."""
    i = build_sheet(_hero()).identity
    assert i.name == "Bokor"
    assert i.alternate_identities == "Alt-identities"
    assert i.player_name == "Player-name"
    assert i.campaign_name == "Campaign-name"
    assert i.genre == "Genre"
    assert i.gm == "GM-name"
    assert i.hair_color == "Hair-color"
    assert i.eye_color == "Eye-color"


def test_each_totals_field_takes_its_own_source():
    """base_points and complication_points are distinct in the stub, so a
    swap between them (as `disad_points`/`base_points` were) is caught."""
    t = build_sheet(_hero()).totals
    assert t.total_points == 276.0
    assert t.available_points == 39.0
    assert t.base_points == 270
    assert t.complication_points == 40
    assert t.experience == 5


def test_each_entry_metadata_field_takes_its_own_source():
    """`alias` and `xmlid` are distinct in the stub, so swapping them (as
    they were) is caught; `end` is exercised here for the first time."""
    s = build_sheet(_hero(powers=[_obj()]))
    e = s.sections[[x.name for x in s.sections].index("powers")].entries[0]
    assert e.id == "1"
    assert e.name == "Entry-name"
    assert e.alias == "Entry-alias"
    assert e.xmlid == "ENTRY-XMLID"
    assert e.end == 3


def test_an_entry_carries_its_parents_id():
    """kirby-cost: a framework slot's `parent_id` matches its pool's `id`.
    A top-level entry (no `parent_id` at all) carries "" instead."""
    s = build_sheet(_hero(powers=[_obj(id=7, parent_id="3")]))
    e = s.sections[[x.name for x in s.sections].index("powers")].entries[0]
    assert e.parent_id == "3"

    top_level = SimpleNamespace(**{k: v for k, v in vars(_obj(id=9)).items()
                                   if k != "parent_id"})
    s2 = build_sheet(_hero(powers=[top_level]))
    e2 = s2.sections[[x.name for x in s2.sections].index("powers")].entries[0]
    assert e2.parent_id == ""


def test_an_object_whose_display_raises_is_reported_not_swallowed():
    """kirby-cost is at 100% display parity, so a raising property means
    something is genuinely broken upstream. Hiding it behind a default would
    turn a bug into a blank cell on a sheet."""
    class Exploding(SimpleNamespace):
        @property
        def column2_output(self):
            raise AttributeError("boom")
    with pytest.raises(AttributeError):
        build_sheet(_hero(powers=[Exploding(**{k: v for k, v in vars(_obj()).items()
                                               if k != "column2_output"})]))
