"""LoadedHero -> Sheet. Selection and shape, never arithmetic."""
from types import SimpleNamespace

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


def _char(xmlid="STR", **kw):
    return MockCharacteristic(xmlid=xmlid, **kw)


def _obj(**kw):
    base = dict(id=1, name="", alias="Growth", xmlid="GROWTH",
                column2_output="Growth ...", real_cost=29, real_cost_pre_list=29,
                active_cost=44, end_usage=0)
    base.update(kw)
    return SimpleNamespace(**base)


def _hero(**kw):
    base = dict(name="Bokor", alternate_identities="", player_name="", campaign_name="",
                genre="", gm="", hair_color="", eye_color="",
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


def test_characteristic_numbers_are_ints_not_floats():
    s = build_sheet(_hero(characteristics=[_char(characteristic_value=15.0, real_cost=5.0)]))
    row = s.characteristics[0]
    assert isinstance(row.value, int) and isinstance(row.cost, int)


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


def test_an_object_whose_display_raises_is_reported_not_swallowed():
    """kirby-cost is at 100% display parity, so a raising property means
    something is genuinely broken upstream. Hiding it behind a default would
    turn a bug into a blank cell on a sheet."""
    class Exploding(SimpleNamespace):
        @property
        def column2_output(self):
            raise AttributeError("boom")
    import pytest
    with pytest.raises(AttributeError):
        build_sheet(_hero(powers=[Exploding(**{k: v for k, v in vars(_obj()).items()
                                               if k != "column2_output"})]))
