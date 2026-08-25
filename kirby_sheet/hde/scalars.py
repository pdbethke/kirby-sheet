"""Identity and the point aggregates.

``generateOutput`` HTMLWriter.java:314-322 (identity), :1268-1295 (height and
weight) and :2163-2262 (the points block), applied in that order.

**The sums here are not a violation of "this layer computes nothing".**
CHARACTERISTIC_POINTS, POWER_POINTS and the rest have no counterpart on
LoadedHero -- HTMLWriter sums them itself, over each object's real cost,
through Rounder.roundUp. This puts the arithmetic exactly where Hero Designer
puts it. What it must never do is re-derive one of those costs; every value
summed below is read from the engine.

Height and weight are the same story: HD formats them in the exporter, not the
model, so the formatting belongs here. The model keeps the float.
"""
from __future__ import annotations

from kirby_cost.util.rounder import round_half_up, round_up

from kirby_sheet.engine import swap_value

#: This backend targets the 6E template only (5E and the is6E branches are
#: out of scope by design, see the spec). Java reads it from the active
#: template; here it is a constant so the branch it selects is visible rather
#: than hidden behind a lookup that can only answer one way.
IS_6E = True


def _sum_real_cost(hero, attribute: str) -> float:
    """Total real cost of a section, or 0.0 when the section is absent."""
    return sum(o.real_cost for o in getattr(hero, attribute, ()) or ())


def apply(text: str, hero) -> str:
    """Fill the identity, height/weight and points tokens, in Java's order."""
    text = swap_value("<!--CHARACTER_NAME-->", hero.name, text)
    text = swap_value("<!--ALTERNATE_IDS-->", hero.alternate_identities, text)
    text = swap_value("<!--PLAYER_NAME-->", hero.player_name, text)
    text = swap_value("<!--CAMPAIGN_NAME-->", hero.campaign_name, text)
    text = swap_value("<!--GENRE-->", hero.genre, text)
    text = swap_value("<!--GM-->", hero.gm, text)
    text = swap_value("<!--HAIR_COLOR-->", hero.hair_color, text)
    text = swap_value("<!--EYE_COLOR-->", hero.eye_color, text)

    text = _height_and_weight(text, hero)
    text = _points(text, hero)
    return text


def _height_and_weight(text: str, hero) -> str:
    """HTMLWriter.java:1268-1295, the NON-metric branch.

    Metric is a user preference (`getPrefs().isMetric()`). The oracle runs
    with it off and this backend does not model preferences, so only the
    imperial branch is ported; HEIGHT_METRIC/WEIGHT_METRIC are not tokens the
    shipped 6E template uses.

    `round_half_up` is Rounder.roundHalfUp, and the distinction is
    load-bearing: Bokor's 96.4567 inches must become 97 (`8' 1"`), which
    Python's own round() gets wrong at 96 (`8' 0"`). HD's rounder works to a
    digit count first, and that is what carries it over the half.
    """
    inches_total = round_half_up(hero.height)
    pounds = round_half_up(hero.weight)
    feet, inches = inches_total // 12, inches_total % 12
    text = swap_value("<!--HEIGHT-->", f"{feet}' {inches}\"", text)
    text = swap_value("<!--WEIGHT-->", f"{pounds} lbs", text)
    return text


def _points(text: str, hero) -> str:
    """HTMLWriter.java:2163-2262.

    The experience arithmetic is transcribed rather than simplified, clamps
    included: `expSpent` adds the Complications back under 6E and both figures
    floor at zero. For Bokor that is 276 - (270+40) = -34, +40 = 6 spent, and
    5 - 6 = -1 -> 0 unspent, which is what HD prints.
    """
    experience = hero.experience
    base = hero.base_points
    disad = hero.disad_points
    total_spent = round_up(hero.total_points)
    disads_used = hero.disads_used

    exp_spent = total_spent - (base + disads_used)
    if IS_6E:
        exp_spent += disads_used
    exp_spent = max(exp_spent, 0)
    unspent = max(experience - exp_spent, 0)

    skills = _sum_real_cost(hero, "skills")
    perks = _sum_real_cost(hero, "perks")
    talents = _sum_real_cost(hero, "talents")
    # Java calls getManeuvers(); kirby-cost exposes the same list as both
    # `maneuvers` and `martial_arts`. Following Java's name.
    maneuvers = _sum_real_cost(hero, "maneuvers")
    powers = _sum_real_cost(hero, "powers")
    characteristics = _sum_real_cost(hero, "characteristics")

    text = swap_value("<!--EARNED_EXP-->", str(experience), text)
    text = swap_value("<!--SPENT_EXP-->", str(exp_spent), text)
    text = swap_value("<!--UNSPENT_EXP-->", str(unspent), text)
    text = swap_value("<!--BASE_POINTS-->", str(base), text)
    text = swap_value("<!--DISAD_POINTS-->", str(disads_used), text)
    text = swap_value("<!--DISAD_POINTS_ALLOWED-->", str(disad), text)
    text = swap_value("<!--TOTAL_POINTS-->", str(total_spent), text)
    text = swap_value("<!--CHARACTERISTIC_POINTS-->",
                      str(round_up(characteristics)), text)
    text = swap_value("<!--SKILL_PERK_TALENT_MARTIAL_ART_POINTS-->",
                      str(round_up(skills + perks + talents + maneuvers)), text)
    text = swap_value("<!--POWER_POINTS-->", str(round_up(powers)), text)
    return text
