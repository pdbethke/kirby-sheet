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
        # Section-specific tokens BEFORE the generic ones. Java does the same
        # -- getPowerString fills TEXT and only then calls getGeneralString
        # (HTMLWriter.java:5095-5097) -- and it matters for the tokens the two
        # share: TEXT means the SECTION's rendering of the power, which for a
        # Compound Power uses the section's separator rather than the power's
        # own. Letting the generic pass win printed "<b>plus</b>" where HD
        # writes "plus", and the child names HD omits.
        block = extras(block, obj, hero)
        return items.apply(block, obj)

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
                           # `resolved_effect`, not `effect`: HD's getEffect()
                           # substitutes the damage-class placeholders a
                           # template writes -- [NNDDC], [STRDC], [NORMALDC]
                           # and the rest (Maneuver.java:836-846) -- and the
                           # raw field still carries them.
                           ("MANEUVER_EFFECT", "resolved_effect")):
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



def _column3(obj) -> str:
    """The END column (``getColumn3Output``, GenericObject.java:1526).

    END usage when there is any, otherwise EMPTY -- not "0". Only a handful of
    classes in kirby-cost define column3_output at all, and Power is not among
    them, so this computes it from end_usage the way Java's base class does.
    """
    # If the object HAS column3_output, its answer stands -- including when
    # that answer is EMPTY. A `if value:` fallback treated a legitimate blank
    # as "no answer" and substituted "0", which is exactly what a List
    # container and a Characteristic must NOT print.
    if hasattr(obj, "column3_output"):
        return str(_read(obj, "column3_output"))
    usage = _read(obj, "end_usage", 0) or 0
    return str(usage) if usage > 0 else ""


def _power_extras(block: str, obj, hero) -> str:
    block = _framework_flags(block, obj)
    block = swap_value("<!--TEXT-->", _text_for(obj), block)
    block = swap_value("<!--POWER_TEXT-->", _text_for(obj), block)
    block = swap_value("<!--POWER_END-->", _column3(obj), block)
    return swap_value("<!--POWER_COST-->",
                      _column1(obj, hero), block)


#: What HD joins a Compound Power's parts with when the section block does not
#: declare `<!--COMPOUND_POWER_SEPARATOR-->` (HTMLWriter.java:5008).
#:
#: Note it is PLAIN. The power's own separator is " <b>plus</b> ", and HD
#: swaps this one in for the duration of the render -- so a compound power's
#: TEXT carries no bold, while the same power's column-2 output elsewhere
#: does. Reading the power's own separator printed "<b>plus</b>" where Hero
#: Designer writes "plus".
COMPOUND_SEPARATOR = " plus "


def _text_for(obj) -> str:
    """TEXT for one power (HTMLWriter.java:5083-5092).

    A Compound Power is rendered with the SECTION's compound separator rather
    than its own; everything else takes its nameless output unchanged.
    """
    from kirby_cost.objects.powers.compound_power import CompoundPower
    if not isinstance(obj, CompoundPower):
        return str(_read(obj, "nameless_column2_output"))
    original = obj.list_separator
    obj.list_separator = COMPOUND_SEPARATOR
    try:
        return str(_read(obj, "nameless_column2_output"))
    finally:
        obj.list_separator = original


def _equipment_extras(block: str, obj, hero) -> str:
    block = _framework_flags(block, obj)
    block = swap_value("<!--TEXT-->", _text_for(obj), block)
    block = swap_value("<!--EQUIPMENT_END-->", _column3(obj), block)
    return swap_value("<!--EQUIPMENT_COST-->",
                      _column1(obj, hero, equipment=True), block)


def _column1(obj, hero, *, equipment: bool = False) -> str:
    """``getColumn1Output`` (GenericObject.java:1477).

    The real cost, except for equipment carrying a price, which prints money
    in the campaign's units instead. That is the same `EQUIPMENTCOSTUNITS`
    that sits beside `EQUIPMENTALLOWED` in the RULES element.
    """
    from kirby_cost.util.rounder import round_up
    if equipment:
        # EQUIPMENT DOES NOT PRINT A POINT COST. GenericObject.java:1477-1495:
        # a piece of equipment with a price prints that price in the campaign's
        # money units, and one WITHOUT a price prints NOTHING at all. It never
        # prints its real cost -- equipment is bought with money, not points,
        # which is the whole reason the section exists.
        #
        # `_is_equipment` on the object is not consulted because the loader
        # never sets it (see the note on XMLAttr("PRICE") in kirby-cost's
        # base.py). The SECTION is the fact: this is the equipment renderer.
        price = float(_read(obj, "price", 0) or 0)
        value = _money(price, hero) if price else ""
        return value + _column1_suffix(obj)
    value = _read(obj, "column1_output")
    if not value:
        value = str(round_up(_read(obj, "real_cost", 0) or 0))
    return str(value) + _column1_suffix(obj)


def _money(price: float, hero) -> str:
    """A priced item's cost in the campaign's units (GenericObject.java:1479-1492).

    UNEXERCISED by the corpus: every HSEG item carries PRICE="0.0", so the
    branch above takes the empty path and this is never reached. It is written
    from the Java rather than left to raise, but it has never been compared
    against Hero Designer and should not be trusted until it has been.
    """
    attrs = getattr(hero, "rules_attrs", None) or {}
    places = int(attrs.get("EQUIPMENTCOSTDECIMALPLACES", 0) or 0)
    units = attrs.get("EQUIPMENTCOSTUNITS", "$")
    rendered = f"{price:.{places}f}"
    prefix = str(attrs.get("EQUIPMENTUNITSPREFIX", "Yes")).upper().startswith("Y")
    return f"{units}{rendered}" if prefix else f"{rendered}{units}"


def _column1_suffix(obj) -> str:
    """``getColumn1Suffix`` (GenericObject.java:1499).

    The parent decides it. A Multipower marks a fixed slot with "f", so its
    cost prints as "1f" rather than "1" -- without this, every fixed slot in
    every multipower is one character wrong and the byte diff never closes.
    """
    parent = getattr(obj, "parent", None)
    if parent is None or not hasattr(parent, "column1_suffix"):
        return ""
    try:
        return parent.column1_suffix(obj) or ""
    except Exception:  # noqa: BLE001 -- a parent that cannot answer adds nothing
        return ""
