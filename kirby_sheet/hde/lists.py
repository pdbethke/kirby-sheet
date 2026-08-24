"""The seven repeated sections, and the adders nested inside two of them.

``getSkillString`` (HTMLWriter.java:5166), ``getMartialArtsString`` (:4647),
``getPerkString`` (:4906), ``getTalentString`` (:5300), ``getPowerString``
(:4995), ``getEquipmentString`` (:3627) and ``getDisadString`` (:3554).

Each is the same shape: extract the section's block, render it once per object
through `items.apply` plus that section's own tokens, and put the accumulation
back. `repeat.render_list` is that shape; only the per-item extras differ.
"""
from __future__ import annotations

from kirby_sheet.engine import swap_value
from kirby_sheet.hde import items, repeat
from kirby_sheet.hde.items import _read


def apply(text: str, hero) -> str:
    """Render every section the template contains, in the template's order."""
    text = _section(text, "SKILLS", hero.skills, _skill_extras, hero)
    text = _section(text, "MARTIAL_ARTS", hero.martial_arts, _maneuver_extras, hero)
    text = _section(text, "PERKS", hero.perks, _perk_extras, hero)
    text = _section(text, "TALENTS", hero.talents, _talent_extras, hero)
    text = _section(text, "POWERS", hero.powers, _power_extras, hero)
    text = _section(text, "EQUIPMENT", getattr(hero, "equipment", ()), _equipment_extras, hero)
    text = _section(text, "DISADS", hero.complications, _disad_extras, hero)
    return text


def _section(text: str, tag: str, objects, extras, hero) -> str:
    def render(block: str, obj, index: int) -> str:
        block = _adders(block, obj)
        block = items.apply(block, obj)
        return extras(block, obj, hero)

    return repeat.render_list(text, f"<!--{tag}-->", f"<!--/{tag}-->",
                              list(objects or ()), render)


def _adders(block: str, obj) -> str:
    """The nested ADDERS block (``getAdderString``, HTMLWriter.java:3196).

    Rendered BEFORE the item's own tokens, because the adder block contains
    the same generic token names -- DISPLAY, ALIAS, OPTION_ID -- and resolving
    the item first would fill the adders' copies with the item's values.
    """
    def render(inner: str, adder, index: int) -> str:
        return items.apply(inner, adder)

    return repeat.render_list(block, "<!--ADDERS-->", "<!--/ADDERS-->",
                              list(getattr(obj, "assigned_adders", ()) or ()),
                              render)


def _roll(obj) -> str:
    """A section's roll token. Absent or hero-dependent rolls read as ""."""
    return str(_read(obj, "roll"))


def _skill_extras(block: str, obj, hero) -> str:
    """SKILL_ROLL and SKILL_TEXT_NO_ROLL (HTMLWriter.java:5266-5296)."""
    # NO fallback to the roll-bearing text. Java uses
    # getColumn2OutputWithoutRoll() for anything that is a Skill and the plain
    # text otherwise; falling back when the former is empty printed " 10-" on
    # skills whose whole text IS the roll, where HD prints nothing.
    from kirby_cost.objects.skills.skill import Skill
    without_roll = (_read(obj, "column2_output_without_roll")
                    if isinstance(obj, Skill)
                    else _read(obj, "nameless_column2_output"))
    block = swap_value("<!--SKILL_TEXT_NO_ROLL-->", str(without_roll), block)
    return swap_value("<!--SKILL_ROLL-->", _roll(obj), block)


def _perk_extras(block: str, obj, hero) -> str:
    return swap_value("<!--PERK_ROLL-->", _roll(obj), block)


def _talent_extras(block: str, obj, hero) -> str:
    return swap_value("<!--TALENT_ROLL-->", _roll(obj), block)


def _disad_extras(block: str, obj, hero) -> str:
    return block


def _maneuver_extras(block: str, obj, hero) -> str:
    """The IF_MANEUVER group (HTMLWriter.java:4600-4646).

    A martial-arts entry that is not a maneuver -- a bought skill sitting in
    the section -- has the whole block stripped rather than filled with blanks.
    """
    from kirby_cost.objects.martial_arts.maneuver import Maneuver
    is_maneuver = isinstance(obj, Maneuver)
    block = items._conditional(block, "IF_MANEUVER", is_maneuver)
    block = items._conditional(block, "IF_NON_MANEUVER", not is_maneuver)
    if not is_maneuver:
        return block
    for tag, attribute in (("MANEUVER_PHASE", "phase"),
                           ("MANEUVER_OCV", "ocv"),
                           ("MANEUVER_DCV", "dcv"),
                           ("MANEUVER_EFFECT", "effect")):
        block = swap_value(f"<!--{tag}-->", str(_read(obj, attribute)), block)
    return block


def _framework_flags(block: str, obj) -> str:
    """IS_MP / IS_EC / IS_VPP (HTMLWriter.java:3774-3806)."""
    from kirby_cost.objects.frameworks.elemental_control import ElementalControl
    from kirby_cost.objects.frameworks.multipower import Multipower
    from kirby_cost.objects.frameworks.vpp import VariablePowerPool
    block = items._conditional(block, "IS_MP", isinstance(obj, Multipower))
    block = items._conditional(block, "IS_EC", isinstance(obj, ElementalControl))
    return items._conditional(block, "IS_VPP", isinstance(obj, VariablePowerPool))


def _sensory(block: str, obj) -> str:
    return items._conditional(block, "IF_SENSORY",
                              bool(getattr(obj, "is_sensory", False)))


def _column3(obj) -> str:
    """The END column (``getColumn3Output``, GenericObject.java:1526).

    END usage when there is any, otherwise EMPTY -- not "0". Only a handful of
    classes in kirby-cost define column3_output at all, and Power is not among
    them, so this computes it from end_usage the way Java's base class does.
    """
    value = _read(obj, "column3_output")
    if value:
        return str(value)
    usage = _read(obj, "end_usage", 0) or 0
    return str(usage) if usage > 0 else "0"


def _power_extras(block: str, obj, hero) -> str:
    block = _framework_flags(block, obj)
    block = _sensory(block, obj)
    block = swap_value("<!--POWER_END-->", _column3(obj), block)
    return swap_value("<!--POWER_COST-->",
                      _column1(obj, hero), block)


def _equipment_extras(block: str, obj, hero) -> str:
    block = _framework_flags(block, obj)
    block = _sensory(block, obj)
    block = swap_value("<!--EQUIPMENT_END-->", _column3(obj), block)
    return swap_value("<!--EQUIPMENT_COST-->", _column1(obj, hero), block)


def _column1(obj, hero) -> str:
    """``getColumn1Output`` (GenericObject.java:1477).

    The real cost, except for equipment carrying a price, which prints money
    in the campaign's units instead. That is the same `EQUIPMENTCOSTUNITS`
    that sits beside `EQUIPMENTALLOWED` in the RULES element.
    """
    from kirby_cost.util.rounder import round_up
    value = _read(obj, "column1_output")
    if value:
        return str(value)
    return str(round_up(_read(obj, "real_cost", 0) or 0))
