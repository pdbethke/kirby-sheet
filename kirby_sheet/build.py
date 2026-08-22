"""Turn a kirby-cost character into a Sheet.

The only module here that imports kirby-cost, and the only one that needs to:
every backend works from the Sheet.

This layer computes NOTHING. kirby-cost is at 100% display parity
(91,221/91,221 strings) and 656/656 on costs, so every value below is read,
never derived. Re-deriving one here would create a second source of truth for
a number that already has one, and the two would drift.
"""
from __future__ import annotations

import os

from kirby_sheet.sheet import (CharacteristicRow, Entry, Identity, Prose,
                               Section, Sheet, Totals)

#: (Sheet section name, LoadedHero attribute), in the order a sheet lists them.
_SECTIONS = (
    ("skills", "skills"),
    ("perks", "perks"),
    ("talents", "talents"),
    ("powers", "powers"),
    ("equipment", "equipment"),
    ("martial_arts", "martial_arts"),
    ("complications", "complications"),
)


def build_sheet(hero) -> Sheet:
    """A Sheet for one character."""
    return Sheet(
        identity=_identity(hero),
        characteristics=tuple(_characteristic(c) for c in hero.characteristics),
        sections=tuple(Section(name=name,
                               entries=tuple(_entry(o) for o in getattr(hero, attr, ()) or ()))
                       for name, attr in _SECTIONS),
        prose=_prose(hero),
        totals=_totals(hero),
    )


def sheet_from_hdc(path: str | os.PathLike) -> Sheet:
    """Load a character file and build its Sheet.

    Here rather than in the CLI so that `build.py` remains the only module in
    this package that imports kirby-cost. That is not tidiness: it is why
    every other module's tests run without a character file, a template, or
    the engine installed.
    """
    from kirby_cost.io.hdc_loader import HDCLoader
    hero = HDCLoader().load_file(str(path))
    return build_sheet(hero)


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
        height=float(hero.height or 0.0),
        weight=float(hero.weight or 0.0),
    )


def _characteristic(char) -> CharacteristicRow:
    """One characteristic row.

    `total` and `roll` are taken verbatim: kirby-cost already produces them as
    display strings ("15", "12-"), and formatting them again here would be
    doing twice, differently, what is already exact.
    """
    return CharacteristicRow(
        xmlid=char.xmlid or "",
        name=char.display or "",
        value=float(char.characteristic_value()),
        base=float(char.get_base_value()),
        cost=float(char.real_cost),
        active_cost=float(char.active_cost),
        total=char.value_display() or "",
        roll=char.roll() or "",
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
        cost=float(obj.real_cost),
        cost_before_framework=float(obj.real_cost_pre_list),
        active_cost=float(obj.active_cost),
        end=float(obj.end_usage or 0),
        parent_id=str(getattr(obj, "parent_id", "") or ""),
    )


def _totals(hero) -> Totals:
    return Totals(
        total_points=float(hero.total_points),
        available_points=float(hero.available_points),
        base_points=float(hero.base_points),
        complication_points=float(hero.disad_points),
        experience=float(hero.experience),
    )


def _prose(hero) -> Prose:
    """Prose fields from kirby-cost hero."""
    notes = (
        getattr(hero, "notes1", "") or "",
        getattr(hero, "notes2", "") or "",
        getattr(hero, "notes3", "") or "",
        getattr(hero, "notes4", "") or "",
        getattr(hero, "notes5", "") or "",
    )
    return Prose(
        background=hero.background or "",
        personality=hero.personality or "",
        quote=hero.quote or "",
        tactics=hero.tactics or "",
        campaign_use=hero.campaign_use or "",
        appearance=hero.appearance or "",
        notes=notes,
    )
