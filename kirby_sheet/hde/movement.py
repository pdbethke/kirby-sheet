"""The eight movement modes and their totals.

``swapMovementString`` (HTMLWriter.java:5432), called once per mode from
:2119-2126.

Each mode is an ``<!--IF_X-->…<!--/IF_X-->`` block. A character with none of
that mode has the block STRIPPED WHOLE, so no line appears at all -- which is
why a mode Bokor lacks produces no `flight:` line rather than an empty one.
Emitting the key with a blank value would be a diff.

Non-combat movement is the combat figure times a multiplier, which is 2 unless
an Improved Noncombat Movement adder raises it. A NONONCOMBAT modifier takes
the levels out of the multiplied part entirely: they are added AFTER the
multiplication, so they contribute to the combat figure but never double.
"""
from __future__ import annotations

from kirby_sheet.engine import (get_long_value, swap_all_long_values,
                                swap_long_value, swap_value)

#: In Java's order (HTMLWriter.java:2119-2126). Order does not affect the
#: result here -- each mode owns its own block -- but it is Java's, and the
#: rule in this package is to follow it rather than judge when it is safe not to.
MODES = ("RUNNING", "SWIMMING", "LEAPING", "FLIGHT", "GLIDING", "SWINGING",
         "TELEPORTATION", "TUNNELING")

#: 6E prints metres; 5E prints inches. This backend targets 6E only.
UNIT = "m"


def apply(text: str, hero) -> str:
    for xmlid in MODES:
        text = _one_mode(text, xmlid, hero)
    return text


def _find(objects, xmlid: str):
    for obj in objects or ():
        if (getattr(obj, "xmlid", "") or "").upper() == xmlid:
            return obj
    return None


def _one_mode(text: str, xmlid: str, hero) -> str:
    open_tag, close_tag = f"<!--IF_{xmlid}-->", f"<!--/IF_{xmlid}-->"
    if get_long_value(open_tag, close_tag, text) is None:
        return text

    primary = secondary = 0          # levels that DO get the noncombat multiplier
    primary_flat = secondary_flat = 0  # NONONCOMBAT levels, added after it
    nc_levels = 0
    nc_adder = None

    def take(move, from_characteristic: bool) -> None:
        """One contributing object. Characteristics use their characteristic
        value; powers use their levels, and only when they affect the total."""
        nonlocal primary, secondary, primary_flat, secondary_flat
        nonlocal nc_levels, nc_adder
        if not from_characteristic and not move.affect_total:
            return
        # int, as Java's counters are: `int primary` cannot take a double, so
        # getCharacteristicValue() is already whole there. Python's returns a
        # float, and "12.0m" is not "12m".
        amount = int(move.characteristic_value(hero) if from_characteristic
                     else move.levels)
        if _find(move.assigned_modifiers, "NONONCOMBAT") is not None:
            if from_characteristic or move.affect_primary:
                primary_flat += amount
            secondary_flat += amount
            return
        improved = _find(move.assigned_adders, "IMPROVEDNONCOMBAT")
        if improved is not None:
            nc_adder = improved
            nc_levels += improved.levels
        if from_characteristic or move.affect_primary:
            primary += amount
        secondary += amount

    from kirby_cost.objects.powers.compound_power import CompoundPower
    for power in hero.powers or ():
        if isinstance(power, CompoundPower):
            for child in power.powers:
                if (getattr(child, "xmlid", "") or "").upper() == xmlid:
                    take(child, from_characteristic=False)
        elif (getattr(power, "xmlid", "") or "").upper() == xmlid:
            take(power, from_characteristic=False)

    for characteristic in hero.characteristics or ():
        if (characteristic.xmlid or "").upper() == xmlid:
            take(characteristic, from_characteristic=True)

    multiplier = 2
    if nc_levels > 0:
        multiplier = nc_levels * nc_adder.level_multiplier
        if nc_adder.level_power != 1:
            multiplier = int(nc_adder.level_multiplier
                             * nc_adder.level_power ** nc_levels)

    primary_nc = primary * multiplier + primary_flat
    secondary_nc = secondary * multiplier + secondary_flat
    primary += primary_flat
    secondary += secondary_flat

    if primary == secondary == primary_nc == secondary_nc == 0:
        return swap_all_long_values(open_tag, close_tag, "", text)

    total = _pair(primary, secondary)
    total_nc = _pair(primary_nc, secondary_nc)

    while True:
        body = get_long_value(open_tag, close_tag, text)
        if body is None:
            return text
        for tag, value in (
            ("PRIMARY", f"{primary}{UNIT}"),
            ("SECONDARY", f"{secondary}{UNIT}"),
            ("PRIMARY_NUMBER", str(primary)),
            ("SECONDARY_NUMBER", str(secondary)),
            ("TOTAL", total),
            ("PRIMARY_NONCOMBAT", f"{primary_nc}{UNIT}"),
            ("SECONDARY_NONCOMBAT", f"{secondary_nc}{UNIT}"),
            ("PRIMARY_NONCOMBAT_NUMBER", str(primary_nc)),
            ("SECONDARY_NONCOMBAT_NUMBER", str(secondary_nc)),
            ("TOTAL_NONCOMBAT", total_nc),
        ):
            body = swap_value(f"<!--{xmlid}_{tag}-->", value, body)
        text = swap_long_value(open_tag, close_tag, body, text)


def _pair(primary: int, secondary: int) -> str:
    """One figure, or "primary/secondary" when the two differ."""
    if primary == secondary:
        return f"{primary}{UNIT}"
    return f"{primary}{UNIT}/{secondary}{UNIT}"
