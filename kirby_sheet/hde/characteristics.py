"""The paired ``<!--STR-->...<!--/STR-->`` characteristic blocks.

``getGeneralCharString`` (HTMLWriter.java:3917) and its callers from :1298
onward, one block per characteristic.

**Why this cannot be a flat substitution.** The block body carries GENERIC
sub-tokens -- TOTAL, COST, ROLL, NOTES -- that recur in every block and mean
"of THIS characteristic". They are resolved inside the block, against the
characteristic that names it, and only then is the block put back.

Java's loop shape is transcribed rather than tidied: extract the block body,
render it, then replace the WHOLE tagged region (open tag + body + close tag)
with the rendered body, and look again. That is how a template naming the same
characteristic twice gets both occurrences.
"""
from __future__ import annotations

from kirby_cost.objects.characteristics.physical_defense import PhysicalDefense
from kirby_cost.objects.characteristics.strength import Strength
from kirby_cost.util.rounder import round_half_up, round_up

from kirby_sheet.engine import get_long_value, swap_value

#: (token name in the template, xmlid on the hero), in the order the shipped
#: 6E template lists them. OCV and DCV are spelled OCV_CHAR / DCV_CHAR in the
#: template because the bare names belong to combat levels elsewhere.
BLOCKS = (
    ("STR", "STR"), ("DEX", "DEX"), ("CON", "CON"), ("INT", "INT"),
    ("EGO", "EGO"), ("PRE", "PRE"), ("OCV_CHAR", "OCV"), ("DCV_CHAR", "DCV"),
    ("OMCV", "OMCV"), ("DMCV", "DMCV"), ("SPD", "SPD"), ("PD", "PD"),
    ("ED", "ED"), ("REC", "REC"), ("END", "END"), ("BODY", "BODY"),
    ("STUN", "STUN"),
)


def apply(text: str, hero) -> str:
    """Render every characteristic block the template contains."""
    by_xmlid = {c.xmlid: c for c in hero.characteristics or ()}
    for token, xmlid in BLOCKS:
        text = _one_characteristic(text, token, by_xmlid.get(xmlid), hero)
    return text


def _one_characteristic(text: str, token: str, ch, hero) -> str:
    """Render every occurrence of one characteristic's block.

    An ABSENT characteristic has its block stripped whole, matching Java's
    `ch == null` branch (HTMLWriter.java:1303). Leaving the markers would put
    them in the output; substituting empty strings would leave the key lines
    behind. Java removes the block, so this does.
    """
    open_tag, close_tag = f"<!--{token}-->", f"<!--/{token}-->"
    while True:
        body = get_long_value(open_tag, close_tag, text)
        if body is None:
            return text
        original = open_tag + body + close_tag
        if ch is None:
            return swap_value(original, "", text)
        rendered = _general(body, ch, hero)
        if token == "STR":
            rendered = _strength(rendered, token, ch, hero)
        elif token in ("PD", "ED"):
            rendered = _defense(rendered, token, ch, hero)
        text = swap_value(original, rendered, text)


def _general(body: str, ch, hero) -> str:
    """``getGeneralCharString`` (HTMLWriter.java:3917).

    Both the prefixed forms (`<!--STR_COST-->`) and the bare generic forms
    (`<!--COST-->`) are filled, prefixed first, exactly as Java does. Only the
    generic forms appear in the shipped 6E template, but a user template may
    use either and the order between them is Java's.
    """
    value = str(round_half_up(ch.characteristic_value(hero)))
    primary = round_half_up(ch.get_primary_value(hero))
    secondary = round_half_up(ch.get_secondary_value(hero))
    base = str(round_half_up(ch.get_base_value(hero)))
    cost = str(round_up(ch.real_cost))
    active = str(round_up(ch.active_cost))
    total = ch.value_display(hero)
    roll = ch.roll(hero)
    notes = ch.display_notes

    for tag, replacement in (
        ("VAL", value), ("NAME", ch.display), ("PRIMARY", str(primary)),
        ("SECONDARY", str(secondary)),
        ("SECONDARY_INCREASE", str(secondary - primary)),
        ("BASE", base), ("COST", cost), ("TOTAL", total), ("ROLL", roll),
        ("NOTES", notes), ("ACTIVE_COST", active),
    ):
        body = swap_value(f"<!--{ch.xmlid}_{tag}-->", replacement, body)
        body = swap_value(f"<!--{tag}-->", replacement, body)
    return body


def _strength(body: str, token: str, ch, hero) -> str:
    """STR_DICE, STR_LIFT and STR_END (HTMLWriter.java:1312-1368)."""
    body = swap_value(f"<!--{token}_DICE-->",
                      Strength.hth_damage_string(ch, hero), body)
    body = swap_value(f"<!--{token}_LIFT-->", _lift(ch, hero), body)
    primary = Strength.primary_end(ch, hero)
    secondary = Strength.secondary_end(ch, hero)
    end = f"{primary}/{secondary}" if primary != secondary else str(primary)
    return swap_value(f"<!--{token}_END-->", end, body)


def _lift(ch, hero) -> str:
    """The lift string (HTMLWriter.java:1314-1352).

    kirby-cost owns the lift VALUES; the units and the one-decimal formatting
    are HTMLWriter's, so they live here. The primary/secondary pair collapses
    to a single figure when the two are equal, which is Java's rule.
    """
    def scale(kilograms: float) -> tuple[float, str]:
        if kilograms >= 1_000_000:
            return kilograms / 1_000_000, "ktons"
        if kilograms >= 10_000:
            return kilograms / 1_000, "tons"
        return kilograms, "kg"

    first = Strength.primary_lift(ch, hero)
    second = Strength.secondary_lift(ch, hero)
    value1, units1 = scale(first)
    value2, units2 = scale(second)
    lift = f"{value1:.1f}{units1}"
    if first != second:
        lift += f"/{value2:.1f}{units2}"
    return lift


def _defense(body: str, token: str, ch, hero) -> str:
    """PD/ED resistant and non-resistant totals (HTMLWriter.java:1578-1604).

    Each is a primary/secondary pair that collapses to one figure when equal.
    """
    res1 = PhysicalDefense.resistant_total(ch, True, hero)
    res2 = PhysicalDefense.resistant_total(ch, False, hero)
    non1 = PhysicalDefense.nonresistant_total(ch, True, hero)
    non2 = PhysicalDefense.nonresistant_total(ch, False, hero)
    resistant = f"{res1}/{res2}" if res1 != res2 else str(res1)
    nonresistant = f"{non1}/{non2}" if non1 != non2 else str(non1)
    body = swap_value(f"<!--{token}_NONRESISTANT_TOTAL-->", nonresistant, body)
    body = swap_value(f"<!--{token}_RESISTANT_TOTAL-->", resistant, body)
    body = swap_value(f"<!--{token}_RESISTANT_PRIMARY-->", str(res1), body)
    return swap_value(f"<!--{token}_RESISTANT_SECONDARY-->", str(res2), body)
