"""The sheet as plain text — the format a person actually reads at a table.

Everything a display string carries is HD's markup (`kirby_sheet.text` strips
it) and HD's own whitespace (never collapsed — see that module's docstring).
This backend adds only line breaks and column alignment on top of what
kirby-cost already computed; it derives no number that Sheet does not already
carry, in keeping with `build.py`'s rule that this package computes nothing.
"""
from __future__ import annotations

import re
import textwrap

from kirby_sheet.formats.totals_view import points_block_rows
from kirby_sheet.sheet import Entry, Identity, Prose, Section, Sheet, Totals
from kirby_sheet.text import plain_text

#: Width of the characteristic name column. "Swimming" (8 chars) is the
#: longest name kirby-cost produces; anything narrower pushes later columns
#: out of alignment (Ravel's movement rows did exactly this at width 6).
_CHAR_NAME_WIDTH = 8

#: The characteristics table's header row. Columns: total value, name, cost,
#: roll, notes -- in the order `build.py` fills a CharacteristicRow.
_CHAR_HEADER = (f"{'Val':>4}  {'Char':<{_CHAR_NAME_WIDTH}} {'Cost':>5}  "
                f"{'Roll':<4}  Notes")

#: (Identity attribute, its label), in the order the identity block lists
#: them. `name` and `alternate_identities` are handled by the header instead.
_IDENTITY_FIELDS = (
    ("player_name", "Player"),
    ("campaign_name", "Campaign"),
    ("genre", "Genre"),
    ("gm", "GM"),
    ("hair_color", "Hair"),
    ("eye_color", "Eyes"),
)

#: A pooled framework slot (Multipower/VPP slot etc.) is indented under its
#: pool. One level: kirby-cost's `hero.powers` nests no deeper than that.
_CHILD_INDENT = "    "

#: (Prose attribute, its heading), in the order a sheet lists them. `notes`
#: is handled separately -- it is a tuple of lines, not a single string.
_PROSE_FIELDS = (
    ("background", "BACKGROUND"),
    ("personality", "PERSONALITY"),
    ("quote", "QUOTE"),
    ("tactics", "TACTICS"),
    ("campaign_use", "CAMPAIGN USE"),
    ("appearance", "APPEARANCE"),
)


def to_text(sheet: Sheet, *, width: int = 78) -> str:
    """The sheet, formatted for a terminal or a monospace text file."""
    lines: list[str] = list(_header(sheet.identity, width))
    lines.extend(_identity_block(sheet.identity, width))

    lines.append("")
    lines.extend(_characteristics(sheet.characteristics, width))

    for section in sheet.sections:
        if not section.entries:
            # "an empty section is omitted entirely" -- a heading with
            # nothing under it tells a reader nothing a blank line wouldn't.
            continue
        lines.append("")
        lines.extend(_section(section, width))

    lines.extend(_prose(sheet.prose, width))
    lines.extend(_footer(sheet.totals, width))

    return "\n".join(lines)


def _header(identity, width: int) -> list[str]:
    rule = "=" * width
    out = [rule, identity.name.upper().center(width).rstrip()]
    if identity.alternate_identities:
        out.append(identity.alternate_identities.center(width).rstrip())
    out.append(rule)
    return out


def _identity_block(identity: Identity, width: int) -> list[str]:
    """The identity facts a sheet carries, printed under the header.

    Only non-empty fields print -- an empty campaign should not print an
    empty "Campaign:" label. Height and weight are formatted for reading
    (see `_fmt_height`/`_fmt_weight`) rather than printed as raw floats.
    """
    parts = [f"{label}: {value}" for attr, label in _IDENTITY_FIELDS
             if (value := getattr(identity, attr))]
    height = _fmt_height(identity.height)
    if height:
        parts.append(f"Height: {height}")
    weight = _fmt_weight(identity.weight)
    if weight:
        parts.append(f"Weight: {weight}")

    if not parts:
        return []
    return textwrap.wrap("   ".join(parts), width=width) or []


def _footer(totals: Totals, width: int) -> list[str]:
    """What the character costs -- the first thing a reader looks for.

    The six labelled numbers come from `totals_view.points_block_rows`, the
    same helper the HTML backend's boxed POINTS block uses, so the two
    cannot disagree about the arithmetic or the wording. Terminal output has
    no "page 1" to put a boxed block at the top of, so this backend keeps
    the same footer position it always has -- only the content changed.
    """
    line = "   ".join(f"{label}: {value}"
                       for label, value in points_block_rows(totals))
    return ["", "-" * width, *textwrap.wrap(line, width=width)]


def _fmt_height(inches: float) -> str:
    """Inches (kirby-cost's `Hero.height`, per HD's own `getHeight`) as
    feet'inches" -- 96.45669 becomes 8'0", not a raw float on the sheet."""
    if not inches:
        return ""
    total = round(inches)
    feet, remainder = divmod(total, 12)
    return f"{feet}'{remainder}\""


def _fmt_weight(pounds: float) -> str:
    """Pounds (kirby-cost's `Hero.weight` is already in lbs), rounded for
    display -- 350.53 becomes "351 lbs"."""
    if not pounds:
        return ""
    return f"{round(pounds)} lbs"


def _characteristics(rows, width: int) -> list[str]:
    out = [_CHAR_HEADER, "-" * width]
    for row in rows:
        # `total` and `roll` are already display strings from kirby-cost
        # (build.py's docstring: "verbatim") -- printed as-is, not reformatted.
        notes = plain_text(row.notes)
        line = (f"{row.total:>4}  {row.name:<{_CHAR_NAME_WIDTH}} "
                f"{_fmt_num(row.cost):>5}  {row.roll:<4}")
        if notes:
            line = f"{line}  {notes}"
        else:
            # No notes to append -- trim OUR column padding rather than
            # leave trailing spaces with nothing after them. `notes`, once
            # present, is appended untouched (never tidied).
            line = line.rstrip()
        out.append(line)
    return out


def _section(section: Section, width: int) -> list[str]:
    # Cost and END must sit over the columns the entry rows actually put
    # them in (0-4 and 5-9, per `_entry_lines`'s `prefix`) -- not far off to
    # the right where no number ever prints.
    label = f"{'Cost':>5}{'END':>5}"
    heading = f"{label}  {section.name.upper()}"
    out = [heading, "-" * width]
    for entry in section.entries:
        out.extend(_entry_lines(entry, width))
    return out


def _entry_lines(entry: Entry, width: int) -> list[str]:
    # cost_before_framework, not cost: a pooled slot's `cost` is 0 because
    # the pool bought the capacity, and a reader wants what it costs alone.
    indent = _CHILD_INDENT if entry.parent_id else ""
    cost = _fmt_num(entry.cost_before_framework)
    end = _fmt_num(entry.end)
    prefix = f"{indent}{cost:>5}{end:>5}  "
    text_column = len(prefix)

    display = plain_text(entry.display)
    wrap_width = max(width - text_column, 20)
    wrapped = textwrap.wrap(display, width=wrap_width,
                             replace_whitespace=False) or [""]

    lines = [prefix + wrapped[0]]
    continuation = " " * text_column
    lines.extend(continuation + rest for rest in wrapped[1:])
    return lines


def _prose(prose: Prose, width: int) -> list[str]:
    out: list[str] = []
    for attr, heading in _PROSE_FIELDS:
        text = getattr(prose, attr)
        if not text:
            continue
        out.append("")
        out.append(heading)
        out.append("-" * width)
        out.extend(_wrap_prose(plain_text(text), width))

    notes = [note for note in prose.notes if note]
    if notes:
        out.append("")
        out.append("NOTES")
        out.append("-" * width)
        for note in notes:
            out.extend(_wrap_prose(plain_text(note), width))
    return out


def _wrap_prose(text: str, width: int) -> list[str]:
    """Wrap prose paragraph by paragraph, preserving blank-line breaks.

    `textwrap.wrap(..., replace_whitespace=False)` on the whole string kept
    an embedded blank line inside one chunk, so the first word of the next
    paragraph landed alone on its own line. Splitting on blank lines first
    and wrapping each paragraph on its own -- with ordinary whitespace
    collapsing inside a paragraph -- avoids that, and re-inserts the blank
    line between paragraphs on the output side.
    """
    paragraphs = re.split(r"\n\s*\n", text)
    out: list[str] = []
    for index, paragraph in enumerate(paragraphs):
        if index:
            out.append("")
        out.extend(textwrap.wrap(paragraph, width=width) or [""])
    return out


def _fmt_num(value: float) -> str:
    """A cost/END value without the trailing `.0` a whole float carries.

    Presentation, not computation: `44.5` (a real active point cost) prints
    as `44.5`, and `29.0` prints as `29`. The underlying float is untouched.
    """
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"
