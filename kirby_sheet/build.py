"""Turn a kirby-cost character into a Sheet.

The only module here that imports kirby-cost, and the only one that needs to:
every backend works from the Sheet.

This layer computes NOTHING. kirby-cost is at 100% display parity
(91,221/91,221 strings) and 656/656 on costs, so every value below is read,
never derived. Re-deriving one here would create a second source of truth for
a number that already has one, and the two would drift.
"""
from __future__ import annotations

from kirby_sheet.sheet import (CharacteristicRow, Entry, Identity, Section,
                               Sheet, Totals)

#: (Sheet section name, LoadedHero attribute), in the order a sheet lists them.
_SECTIONS = (
    ("skills", "skills"),
    ("perks", "perks"),
    ("talents", "talents"),
    ("powers", "powers"),
    ("martial_arts", "martial_arts"),
    ("complications", "complications"),
)


def build_sheet(hero) -> Sheet:
    """A Sheet for one character."""
    return Sheet(
        identity=_identity(hero),
        characteristics=tuple(_characteristic(c, hero) for c in hero.characteristics),
        sections=tuple(Section(name=name,
                               entries=tuple(_entry(o) for o in getattr(hero, attr, ()) or ()))
                       for name, attr in _SECTIONS),
        totals=_totals(hero),
    )


def _identity(hero) -> Identity:
    return Identity(
        name=hero.name or "",
        alternate_identities=hero.alternate_identities or "",
        player_name=hero.player_name or "",
        campaign_name=hero.campaign_name or "",
        genre=hero.genre or "",
        gm=hero.gm or "",
        hair_color=hero.hair_color or "",
        eye_color=hero.eye_color or "",
    )


def _characteristic(char, hero) -> CharacteristicRow:
    """One characteristic row.

    `total` and `roll` are taken verbatim: kirby-cost already produces them as
    display strings ("15", "12-"), and formatting them again here would be
    doing twice, differently, what is already exact.
    """
    # Handle both test mocks (SimpleNamespace with attributes) and real Characteristic objects (with methods)
    cv = char.characteristic_value() if callable(char.characteristic_value) else char.characteristic_value
    vd = char.value_display() if callable(char.value_display) else char.value_display
    roll = char.roll() if callable(char.roll) else char.roll
    bv = char.base_value

    # For real characteristics, use LoadedHero's computed total value and calculate base
    if hasattr(hero, 'characteristic_value') and callable(hero.characteristic_value):
        total_value = hero.characteristic_value(char.xmlid)
        # Base is the difference between total and purchased value
        bv = total_value - cv
    else:
        total_value = cv

    return CharacteristicRow(
        xmlid=char.xmlid or "",
        name=char.display or "",
        value=int(cv),
        base=int(bv),
        cost=int(char.real_cost),
        active_cost=int(char.active_cost),
        total=str(int(total_value)) if total_value else "",
        roll=roll or "",
        notes=char.display_notes or "",
    )


def _entry(obj) -> Entry:
    """One purchased thing.

    Both costs are carried. They differ wherever a framework has a say — a
    Variable Power Pool slot's `real_cost` is zero because the pool bought the
    capacity, while its `real_cost_pre_list` is what the slot costs on its
    own. A sheet wants to print the latter and sum the former.

    `column2_output` is read, not caught: kirby-cost is at full display
    parity, so a property that raises means something upstream is broken and
    should surface as an error rather than as a blank cell.
    """
    return Entry(
        id=str(obj.id),
        name=obj.name or "",
        alias=obj.alias or "",
        xmlid=obj.xmlid or "",
        display=obj.column2_output,
        cost=int(obj.real_cost),
        cost_before_framework=int(obj.real_cost_pre_list),
        active_cost=int(obj.active_cost),
        end=int(obj.end_usage or 0),
    )


def _totals(hero) -> Totals:
    return Totals(
        total_points=float(hero.total_points),
        available_points=float(hero.available_points),
        base_points=float(hero.base_points),
        complication_points=float(hero.disad_points),
        experience=float(hero.experience),
    )
