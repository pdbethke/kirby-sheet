"""LoadedHero -> Sheet. Selection and shape, never arithmetic."""
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from kirby_sheet.build import build_sheet, copy_hdc, sheet_from_hdc
from tests.corpus import character_path

#: copy_hdc round-trips a real character file through kirby-cost, so it
#: needs both a .hdc (KIRBY_SHEET_HDC) and kirby-cost's template
#: (KIRBY_COST_HDT). Neither ships with the repo.
_needs_character = pytest.mark.skipif(
    character_path() is None or not (os.environ.get("KIRBY_COST_HDT") or "").strip(),
    reason="needs KIRBY_SHEET_HDC and KIRBY_COST_HDT",
)


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
                eye_color="Eye-color", height=96.45669291338582,
                weight=350.5349736900354,
                background="Background-text", personality="Personality-text",
                quote="Quote-text", tactics="Tactics-text",
                campaign_use="Campaign-use-text", appearance="Appearance-text",
                notes1="Note-1", notes2="Note-2", notes3="Note-3",
                notes4="Note-4", notes5="Note-5",
                characteristics=[], powers=[], skills=[], perks=[], talents=[],
                complications=[], martial_arts=[], equipment=[],
                total_points=276.0, available_points=39.0, base_points=270,
                disad_points=40, experience=5,
                disads_used=38, complications_shortfall=2.0,
                spendable_points=273.0, points_unspent=-3.0)
    base.update(kw)
    return SimpleNamespace(**base)


def test_identity_is_carried_across():
    s = build_sheet(_hero(name="Bokor", gm="Gamemaster"))
    assert s.identity.name == "Bokor" and s.identity.gm == "Gamemaster"


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
                                            "powers", "equipment", "martial_arts", "complications"]


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


def test_the_new_6e_totals_fields_are_carried_across_and_not_truncated():
    """`complications_taken`, `complications_shortfall`, `spendable_points`
    and `points_unspent` come straight off kirby-cost's own 6E properties
    (LoadedHero.disads_used / .complications_shortfall / .spendable_points
    / .points_unspent) -- build.py reads them, it does not derive them. Every
    stub value here is distinct, and `points_unspent` is fractional-looking
    (a whole number written as a float, -3.0) so a narrowing `int()` on this
    field would not be caught by this assertion alone -- see
    test_totals_unspent_is_not_narrowed_to_an_int for that guard
    specifically, using PowerLad's real 0.5."""
    t = build_sheet(_hero()).totals
    assert t.complications_taken == 38
    assert t.complications_shortfall == 2.0
    assert t.spendable_points == 273.0
    assert t.points_unspent == -3.0


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


def test_prose_fields_are_carried():
    hero = _hero(background="B", personality="P", quote="Q", tactics="T",
                 campaign_use="C", appearance="A",
                 notes1="1", notes2="2", notes3="3", notes4="4", notes5="5")
    p = build_sheet(hero).prose
    assert p.background == "B"
    assert p.personality == "P"
    assert p.quote == "Q"
    assert p.tactics == "T"
    assert p.campaign_use == "C"
    assert p.appearance == "A"
    assert p.notes == ("1", "2", "3", "4", "5")


def test_height_and_weight_are_carried_unrounded():
    """The model carries what kirby-cost gives. 96.45669 is a real value from
    a real character; rounding it here would be a computation, and a backend
    that wants 8'0" can do that itself."""
    i = build_sheet(_hero(height=96.45669291338582, weight=350.5349736900354)).identity
    assert i.height == 96.45669291338582
    assert i.weight == 350.5349736900354


def test_equipment_is_a_section():
    names = [s.name for s in build_sheet(_hero()).sections]
    assert names == ["skills", "perks", "talents", "powers", "equipment",
                     "martial_arts", "complications"]


# --- copy_hdc: LoadedHero -> write_hdc, the .hdc round trip ---------------
#
# copy_hdc does not go through the Sheet: the Sheet is a view (display
# strings, costs, totals) and deliberately does not carry the xmlids,
# modifiers, adders, option ids and levels a rebuilt character file needs.
# kirby-cost owns round-trip fidelity as its own release gate (794/794
# characters); these tests only check that copy_hdc does not get in its way.

@_needs_character
def test_copy_hdc_returns_the_target_path_and_the_file_exists(tmp_path):
    target_path = tmp_path / "returned.hdc"

    result = copy_hdc(character_path(), target_path)

    assert Path(result) == target_path
    assert target_path.is_file()


@_needs_character
def test_the_round_tripped_character_reloads_unchanged(tmp_path):
    """kirby-cost promises semantic fidelity, not byte identity, and says so:
    hero_to_bytes normalises a UTF-16 file to a little-endian BOM "regardless
    of the byte order it arrived in", and its export gate's contract is
    "everything the document said, the export says back".

    So byte-comparing a round-trip asserts a guarantee the library explicitly
    disclaims -- a big-endian source (Ravel) and an LF-ended source (Bokor)
    both come back normalised and both are correct. What must survive is the
    character."""
    target_path = tmp_path / "roundtrip.hdc"

    copy_hdc(character_path(), target_path)

    source_sheet = sheet_from_hdc(character_path())
    target_sheet = sheet_from_hdc(target_path)

    assert target_sheet.identity.name == source_sheet.identity.name
    assert target_sheet.identity.name != ""
    assert target_sheet.totals.total_points == source_sheet.totals.total_points
    assert target_sheet.totals.available_points == source_sheet.totals.available_points
    assert len(target_sheet.characteristics) == len(source_sheet.characteristics)
    assert ([(s.name, len(s.entries)) for s in target_sheet.sections]
            == [(s.name, len(s.entries)) for s in source_sheet.sections])
    assert ([(c.xmlid, c.value, c.cost, c.total, c.roll) for c in target_sheet.characteristics]
            == [(c.xmlid, c.value, c.cost, c.total, c.roll) for c in source_sheet.characteristics])

    # Count-only comparison would pass even if every entry lost its modifiers
    # (same counts, same section names, wrong display/cost) -- compare the
    # entries themselves, not just how many of them there are.
    target_entries = [(e.display, e.cost_before_framework, e.end)
                       for s in target_sheet.sections for e in s.entries]
    source_entries = [(e.display, e.cost_before_framework, e.end)
                       for s in source_sheet.sections for e in s.entries]
    assert target_entries != []
    assert target_entries == source_entries
    assert target_sheet.prose == source_sheet.prose
    assert target_sheet.identity == source_sheet.identity


@_needs_character
def test_the_round_trip_normalises_bom_and_line_endings(tmp_path):
    """These two differences are deliberate and documented in kirby-cost.
    Pinning them here means a future change to that behaviour surfaces as a
    failing test rather than as a silent difference in someone's file."""
    target_path = tmp_path / "roundtrip.hdc"

    copy_hdc(character_path(), target_path)

    target_bytes = target_path.read_bytes()
    assert target_bytes.startswith(b"\xff\xfe")
    assert "\r\n" in target_bytes.decode("utf-16")


# --- the 6E points model, against real characters --------------------------
#
# Expected values independently verified from the HDC files (see the totals
# brief). HD's own `available_points` reports these same three characters as
# 100, 120.5 and 39 -- the 5E-style figure, which stays on Totals untouched
# but is NOT what these assertions check. `points_unspent` is the 6E figure:
# it must read 0 for Ravel (exactly on budget), 0.5 for PowerLad (a fraction
# that a narrowing int() would erase), and -1 for Bokor (over budget, and
# unclamped).

_RAVEL = Path("~/Documents/Champions/Ravel.hdc").expanduser()
_POWERLAD = Path("~/Desktop/PowerLad.hdc").expanduser()

_needs_ravel = pytest.mark.skipif(
    not _RAVEL.is_file() or not (os.environ.get("KIRBY_COST_HDT") or "").strip(),
    reason="needs Ravel.hdc and KIRBY_COST_HDT",
)
#: Bokor, named explicitly for the same reason _RAVEL and _POWERLAD are: the
#: test below asserts HIS point totals, so it must not run against whatever
#: KIRBY_SHEET_HDC happens to point at. It did, and failed the moment the
#: env var was aimed at another character.
_BOKOR = Path("~/Documents/Champions/Bokor.hdc").expanduser()

_needs_bokor = pytest.mark.skipif(
    not _BOKOR.is_file() or not (os.environ.get("KIRBY_COST_HDT") or "").strip(),
    reason="needs Bokor.hdc and KIRBY_COST_HDT",
)

_needs_powerlad = pytest.mark.skipif(
    not _POWERLAD.is_file() or not (os.environ.get("KIRBY_COST_HDT") or "").strip(),
    reason="needs PowerLad.hdc and KIRBY_COST_HDT",
)


@_needs_ravel
def test_ravel_is_built_exactly_to_the_6e_pool():
    t = sheet_from_hdc(_RAVEL).totals
    assert t.spendable_points == 450.0
    assert t.total_points == 450.0
    assert t.points_unspent == 0.0
    assert t.available_points == 100.0   # HD's 5E-style figure, unchanged


@_needs_powerlad
def test_powerlad_has_half_a_point_unspent_not_zero():
    """399.5 spent against a 400 pool -- a narrowing int() on points_unspent
    would round 0.5 down to 0 and this would pass for the wrong reason if it
    only checked truthiness, so the exact float is asserted."""
    t = sheet_from_hdc(_POWERLAD).totals
    assert t.spendable_points == 400.0
    assert t.total_points == 399.5
    assert t.points_unspent == 0.5
    assert t.available_points == 120.5   # HD's 5E-style figure, unchanged


@_needs_bokor
def test_bokor_is_overspent_by_exactly_one_point():
    """Bokor's 6E Unspent is -1 -- negative, and must not be clamped to 0."""
    t = sheet_from_hdc(_BOKOR).totals
    assert t.base_points == 270.0
    assert t.experience == 5.0
    assert t.complications_taken == 40.0
    assert t.complication_points == 40.0
    assert t.complications_shortfall == 0.0
    assert t.spendable_points == 275.0
    assert t.total_points == 276.0
    assert t.points_unspent == -1.0
    assert t.available_points == 39.0   # HD's 5E-style figure, unchanged
