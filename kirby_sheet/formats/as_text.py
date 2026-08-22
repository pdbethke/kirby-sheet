"""The sheet as plain text — the format a person actually reads at a table.

Everything a display string carries is HD's markup (`kirby_sheet.text` strips
it) and HD's own whitespace (never collapsed — see that module's docstring).
This backend adds only line breaks and column alignment on top of what
kirby-cost already computed; it derives no number that Sheet does not already
carry, in keeping with `build.py`'s rule that this package computes nothing.
"""
from __future__ import annotations

import textwrap

from kirby_sheet.sheet import Entry, Prose, Section, Sheet
from kirby_sheet.text import plain_text

#: The characteristics table's header row. Columns: total value, name, cost,
#: roll, notes -- in the order `build.py` fills a CharacteristicRow.
_CHAR_HEADER = f"{'Val':>4}  {'Char':<6} {'Cost':>5}  {'Roll':<4}  Notes"

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

    return "\n".join(lines)


def _header(identity, width: int) -> list[str]:
    rule = "=" * width
    out = [rule, identity.name.upper().center(width).rstrip()]
    if identity.alternate_identities:
        out.append(identity.alternate_identities.center(width).rstrip())
    out.append(rule)
    return out


def _characteristics(rows, width: int) -> list[str]:
    out = [_CHAR_HEADER, "-" * width]
    for row in rows:
        # `total` and `roll` are already display strings from kirby-cost
        # (build.py's docstring: "verbatim") -- printed as-is, not reformatted.
        notes = plain_text(row.notes)
        line = (f"{row.total:>4}  {row.name:<6} {_fmt_num(row.cost):>5}  "
                f"{row.roll:<4}")
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
    label = "Cost   END"
    inner_width = width - 2
    heading = section.name.upper().ljust(inner_width - len(label)) + label
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
        out.extend(textwrap.wrap(plain_text(text), width=width,
                                 replace_whitespace=False) or [""])

    notes = [note for note in prose.notes if note]
    if notes:
        out.append("")
        out.append("NOTES")
        out.append("-" * width)
        for note in notes:
            out.extend(textwrap.wrap(plain_text(note), width=width,
                                     replace_whitespace=False) or [""])
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
