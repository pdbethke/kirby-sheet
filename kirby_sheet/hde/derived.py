"""PER Roll, PRE Attack and the Mental/Power Defence totals.

``generateOutput`` HTMLWriter.java:323-336 (the two rolls) and :2267-2392 (the
two defence totals).

The defence totals are summed here rather than read off the hero for the same
reason the point aggregates are: HTMLWriter sums them itself, walking powers
and equipment. Every figure summed is one the engine reports.
"""
from __future__ import annotations

from kirby_cost.objects.characteristics.intelligence import Intelligence
from kirby_cost.objects.characteristics.presence import Presence
from kirby_cost.util.rounder import round_half_up

from kirby_sheet.engine import swap_value

#: 5E adds EGO/5 to Mental Defence when the character owns a Mental Defence
#: power; 6E never does (HTMLWriter.java:2271, `if (!is6E)`). This backend
#: targets 6E only, so that branch is not ported -- and `add_ego` is therefore
#: permanently False, which is why the EGO arm of the 6E code below is dead.
IS_6E = True


def apply(text: str, hero) -> str:
    """Fill PER_ROLL, PRE_ATTACK and the two defence totals."""
    text = _rolls(text, hero)
    text = swap_value("<!--MENTAL_DEFENSE_TOTAL-->", _mental_defence(hero), text)
    text = swap_value("<!--POWER_DEFENSE_TOTAL-->", _power_defence(hero), text)
    return text


def _characteristic(hero, xmlid: str):
    for characteristic in hero.characteristics or ():
        if characteristic.xmlid == xmlid:
            return characteristic
    return None


def _rolls(text: str, hero) -> str:
    """HTMLWriter.java:323-336.

    Java emits "" when the characteristic is absent rather than raising, and
    that branch is reproduced: a character built without INT or PRE is a
    legitimate document, not an error.
    """
    intelligence = _characteristic(hero, "INT")
    per_roll = Intelligence.per_roll(intelligence, hero) if intelligence else ""
    text = swap_value("<!--PER_ROLL-->", per_roll, text)

    presence = _characteristic(hero, "PRE")
    pre_attack = Presence.pre_attack(presence, hero) if presence else ""
    return swap_value("<!--PRE_ATTACK-->", pre_attack, text)


def _mental_defence(hero) -> str:
    """HTMLWriter.java:2267-2327.

    A bare MentalDefense is constructed for its base levels -- Java does the
    same (`new MentalDefense(new Element("MENTALDEFENSE"))`) -- then every
    characteristic's own md levels are added.
    """
    from kirby_cost.objects.powers.mental_defense import MentalDefense

    try:
        total = MentalDefense().md_levels
    except Exception:  # noqa: BLE001 -- Java's bare construction cannot fail;
        total = 0      # if ours can, an absent base is closer than a crash.
    for characteristic in hero.characteristics or ():
        total += getattr(characteristic, "md_levels", 0) or 0
    return str(total)


def _power_defence(hero) -> str:
    """HTMLWriter.java:2352-2392.

    PowerDefense contributes its levels; ForceField contributes only its
    POWDLEVELS, not its levels -- the power's PD/ED share is not Power
    Defence. CompoundPower children are walked, in powers and in equipment.
    """
    from kirby_cost.objects.powers.compound_power import CompoundPower
    from kirby_cost.objects.powers.force_field import ForceField
    from kirby_cost.objects.powers.power_defense import PowerDefense

    def contribution(item) -> int:
        if isinstance(item, PowerDefense):
            return item.levels
        if isinstance(item, ForceField):
            return getattr(item, "powd_levels", 0) or 0
        return 0

    total = 0
    for source in (hero.powers or (), getattr(hero, "equipment", ()) or ()):
        for item in source:
            if isinstance(item, CompoundPower):
                for child in item.powers:
                    total += contribution(child)
            else:
                total += contribution(item)
    return str(total)
