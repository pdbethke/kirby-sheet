"""The POINTS block: the six numbers every totals area shows, formatted once.

`Totals` carries kirby-cost's 6E character-points fields verbatim (see
`build.py`'s docstring: this package computes nothing upstream of here).
This module is the one place that turns those fields into the six labelled
rows a totals area prints -- `as_html.py`'s boxed block at the top of page 1
and `as_text.py`'s footer both call `points_block_rows` rather than each
formatting the numbers for itself, so the two cannot drift into different
wording or a different arithmetic for the same character.

This is presentation only: string formatting, a "taken / matching" pairing,
and a visible "(over budget)" marker on a negative Unspent. It reads
`spendable_points`, `points_unspent` and `complications_shortfall` straight
off `Totals` -- it does not derive them. Those come from kirby-cost's own
6E properties (see kirby_cost.io.hdc_loader.LoadedHero), which implement the
printed rule (6E1 p.30, p.269): Complications never ADD points in 6E --
`base_points` already includes the Matching Complications target, and
falling short of it subtracts 1:1. `available_points` -- HD's older,
oracle-verified 5E-style figure, where Complications add to the pool --
stays on `Totals` untouched and is not part of this block; it is carried
into JSON only (see as_json.py, which serialises the whole Totals object).
"""
from __future__ import annotations

from kirby_sheet.sheet import Totals


def points_block_rows(totals: Totals) -> tuple[tuple[str, str], ...]:
    """The six (label, formatted value) rows a POINTS block shows, in order.

    - "Total Points" is `base_points` -- in 6E this is the Total Points
      figure, already inclusive of the Matching Complications target
      (6E1 p.269: "400 Total Points, including 75 points' worth of Matching
      Complications").
    - "Complications" reads `taken / matching`, which makes a shortfall
      self-evident without a separate "shortfall: 0" line that would be
      noise on nearly every sheet. When the shortfall IS non-zero, the row
      also says what it cost, because that is the case a reader needs
      explained.
    - "Unspent" is ALWAYS present, including when it is exactly 0 -- an
      omitted line would be ambiguous between "finished" and "this backend
      dropped the field again". When it is negative (an overspent
      character, a real and unclamped condition), the row is marked with
      the word "over" so the fact survives plain-text extraction (a
      `pdftotext` dump, `--text` output, a greyscale printout) and not just
      a colour a backend might add on top.
    """
    complications = (f"{_fmt_num(totals.complications_taken)} / "
                     f"{_fmt_num(totals.complication_points)} matching")
    if totals.complications_shortfall:
        complications += (f" (shortfall cost "
                          f"{_fmt_num(totals.complications_shortfall)})")

    unspent = _fmt_num(totals.points_unspent)
    if totals.points_unspent < 0:
        unspent += " -- OVER BUDGET"

    return (
        ("Total Points", _fmt_num(totals.base_points)),
        ("Experience", _fmt_signed(totals.experience)),
        ("Complications", complications),
        ("Spendable", _fmt_num(totals.spendable_points)),
        ("Spent", _fmt_num(totals.total_points)),
        ("Unspent", unspent),
    )


def _fmt_num(value: float) -> str:
    """A points value without the trailing `.0` a whole float carries."""
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def _fmt_signed(value: float) -> str:
    """Experience prints with an explicit `+` when positive -- "+5", not a
    bare "5" that could be misread as another total rather than an
    adjustment. Zero and negative values print as `_fmt_num` already would;
    a leading `-` on a negative is unambiguous on its own."""
    value = float(value)
    if value > 0:
        return f"+{_fmt_num(value)}"
    return _fmt_num(value)
