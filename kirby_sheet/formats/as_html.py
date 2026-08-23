"""The sheet as a standalone HTML document.

A `Sheet` carries two KINDS of string, and this backend is the one place
that must treat them differently:

- `Entry.display` and `CharacteristicRow.notes` carry Hero Designer's own
  markup -- `<i>`, `<b>` -- measured at 16,116 and 1,034 occurrences across
  655 characters. That markup IS the correct output for an HTML document, so
  it passes through unescaped. This is the one backend where
  `kirby_sheet.text.plain_text` is not wanted -- do not import it here.
- Everything else is text a person typed: names, alternate identities,
  prose, player and campaign names. Those are escaped with `html.escape`,
  or a background containing `<` or `&` would corrupt the page.

Escaping the display strings shows a reader literal `&lt;i&gt;`; not
escaping the prose corrupts the document. Both directions are a defect, and
both are covered by a test that fails if you get it backwards.
"""
from __future__ import annotations

import html

from kirby_sheet.sheet import CharacteristicRow, Entry, Prose, Section, Sheet

#: (Identity attribute, its label), in the order the identity block lists
#: them. `name` and `alternate_identities` get their own header treatment.
_IDENTITY_FIELDS = (
    ("player_name", "Player"),
    ("campaign_name", "Campaign"),
    ("genre", "Genre"),
    ("gm", "GM"),
    ("hair_color", "Hair"),
    ("eye_color", "Eyes"),
)

#: (Prose attribute, its heading), in the order a sheet lists them. `notes`
#: is handled separately -- it is a tuple of lines, not a single string.
_PROSE_FIELDS = (
    ("background", "Background"),
    ("personality", "Personality"),
    ("quote", "Quote"),
    ("tactics", "Tactics"),
    ("campaign_use", "Campaign Use"),
    ("appearance", "Appearance"),
)

_STYLE = """
    body { font-family: Georgia, 'Times New Roman', serif; max-width: 960px;
           margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }
    h1 { margin-bottom: 0; }
    .alternate-identities { margin-top: 0; font-style: italic; color: #555; }
    table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
    th, td { border: 1px solid #ccc; padding: 0.25rem 0.5rem; text-align: left; }
    th { background: #eee; }
    tr.nested td:first-child { padding-left: 1.5rem; }
    .identity-block, .totals { margin: 1rem 0; }
    .identity-block span { margin-right: 1.5rem; }
    section.prose { margin: 1rem 0; }
    section.prose h2 { margin-bottom: 0.25rem; }
"""


def to_html(sheet: Sheet, *, title: str | None = None,
            stylesheet: str | None = None) -> str:
    """The sheet, as a complete standalone HTML document.

    `stylesheet`, when given, REPLACES the contents of the `<style>` block
    outright -- it is not merged with `_STYLE`. Omitted, behaviour is
    exactly as before this parameter existed (the `as_pdf` backend is the
    only caller that passes one, to swap in CSS xhtml2pdf's subset can
    render).

    Passing a `stylesheet` also switches the tables to declare column
    widths via a `width` attribute on each `<th>` -- xhtml2pdf (the reason
    a caller would pass one) has no browser-grade table layout algorithm,
    so an unconstrained `table { width: 100% }` hands most of a row's
    width to the narrow numeric columns and squeezes long power
    descriptions into an unreadably narrow ribbon. A browser needs no such
    hint, so the default (no `stylesheet`) path never emits one -- that
    keeps this backend's own output byte-identical to before this
    parameter existed. (An earlier version of this used `<colgroup>`
    instead; xhtml2pdf ignores it completely -- see `_TABLE_OPEN`'s
    docstring.)"""
    doc_title = title if title is not None else sheet.identity.name
    style = stylesheet if stylesheet is not None else _STYLE
    print_mode = stylesheet is not None

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append(f"<title>{html.escape(doc_title)}</title>")
    parts.append(f"<style>{style}</style>")
    parts.append("</head>")
    parts.append("<body>")

    parts.extend(_header(sheet))
    parts.extend(_identity_block(sheet, print_mode))
    parts.extend(_characteristics(sheet.characteristics, print_mode))

    for section in sheet.sections:
        if not section.entries:
            # An empty section heading tells a reader nothing a blank line
            # wouldn't -- omit it entirely, as the text backend does.
            continue
        parts.extend(_section(section, print_mode))

    parts.extend(_prose(sheet.prose))
    parts.extend(_footer(sheet.totals))

    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)


def _header(sheet: Sheet) -> list[str]:
    identity = sheet.identity
    out = [f"<h1>{html.escape(identity.name)}</h1>"]
    if identity.alternate_identities:
        out.append(f'<p class="alternate-identities">'
                    f"{html.escape(identity.alternate_identities)}</p>")
    return out


#: A visible gap between adjacent identity-block `<span>`s, for the print
#: path only. The screen stylesheet's `.identity-block span { margin-right:
#: 1.5rem; }` gives a browser that gap for free; xhtml2pdf's box model does
#: not honour margin (or padding) on an inline `<span>` at all -- verified
#: against Bokor's actual identity line, which without this ran together as
#: "Player: Peter BethkeHair: BaldEyes: Brown..." with zero pixels of
#: separation. Three non-breaking spaces, joined between fields (not
#: trailing on the last one), is what xhtml2pdf does honour.
_PRINT_FIELD_GAP = "\xa0\xa0\xa0"


def _identity_block(sheet: Sheet, print_mode: bool = False) -> list[str]:
    identity = sheet.identity
    fields = [f"<span><strong>{label}:</strong> {html.escape(str(value))}</span>"
              for attr, label in _IDENTITY_FIELDS
              if (value := getattr(identity, attr))]
    height = _fmt_height(identity.height)
    if height:
        fields.append(f"<span><strong>Height:</strong> {html.escape(height)}</span>")
    weight = _fmt_weight(identity.weight)
    if weight:
        fields.append(f"<span><strong>Weight:</strong> {html.escape(weight)}</span>")

    if not fields:
        return []
    joiner = _PRINT_FIELD_GAP if print_mode else ""
    return ['<p class="identity-block">' + joiner.join(fields) + "</p>"]


#: Column widths for the print (`xhtml2pdf`) path only -- see `to_html`'s
#: `print_mode` note. Percentages sum to 100; Notes/description columns get
#: the bulk of the row because that is where the long text lives.
#:
#: These are `width` attributes on each `<th>`, NOT a `<colgroup>`.
#: `<colgroup>` was tried first and MEASURED inert in xhtml2pdf: rendering
#: the same table with `<col style="width:8%">` and again with
#: `<col style="width:45%">` (both spellings tried, `style="width:...%"`
#: and the bare `width="...%"` attribute) produced byte-for-byte identical
#: extracted text -- the description column wrapped at exactly the same
#: point either way. A `width` attribute on `<th>` is what actually moves
#: the layout; verified the same way, with the extracted text differing
#: between two width sets. Do not reintroduce `<colgroup>` here on the
#: assumption that it is the standard-looking way to do this -- it is
#: standard-looking AND does nothing in this renderer.
_CHAR_WIDTHS = ("7%", "13%", "7%", "8%", "65%")
_SECTION_WIDTHS = ("8%", "8%", "84%")

#: The print path's cell padding is an HTML `cellpadding` attribute, not a
#: CSS `padding` rule on `td, th`. A CSS `padding` rule (even a single
#: point, well short of the negative-availWidth crash `as_pdf.py`
#: documents) makes xhtml2pdf silently abandon the declared `<th width=...>`
#: values: the Notes/description column collapses to a sliver and the last
#: two headers of the characteristics table print on top of each other.
#: Verified against Bokor's actual characteristics table, not a synthetic
#: one.
_TABLE_OPEN = '<table cellpadding="3">'


def _th_row(headers: tuple[str, ...], widths: tuple[str, ...] | None) -> str:
    """One `<tr>` of `<th>` cells. `widths`, given, puts a `width=`
    attribute on each -- the print path's mechanism for column widths (see
    `_CHAR_WIDTHS`'s docstring for why this is `width=` on `<th>` and not
    `<colgroup>`)."""
    if widths is None:
        cells = "".join(f"<th>{h}</th>" for h in headers)
    else:
        cells = "".join(f'<th width="{w}">{h}</th>'
                         for h, w in zip(headers, widths))
    return f"<tr>{cells}</tr>"


def _characteristics(rows: tuple[CharacteristicRow, ...],
                      print_mode: bool = False) -> list[str]:
    if not rows:
        return []
    out = [_TABLE_OPEN if print_mode else "<table>", "<thead>",
           _th_row(("Val", "Char", "Cost", "Roll", "Notes"),
                   _CHAR_WIDTHS if print_mode else None),
           "</thead>", "<tbody>"]
    for row in rows:
        # `total` and `roll` are already display strings from kirby-cost --
        # printed as-is, escaped like any other value a person didn't
        # necessarily type but that isn't HD markup either.
        out.append(
            "<tr>"
            f"<td>{html.escape(row.total)}</td>"
            f"<td>{html.escape(row.name)}</td>"
            f"<td>{_fmt_num(row.cost)}</td>"
            f"<td>{html.escape(row.roll)}</td>"
            # `notes` carries HD's own markup (see module docstring) --
            # unescaped, deliberately.
            f"<td>{row.notes}</td>"
            "</tr>"
        )
    out.append("</tbody>")
    out.append("</table>")
    return out


def _section(section: Section, print_mode: bool = False) -> list[str]:
    # The text backend renders this same string as the third column's
    # header (`Cost  END  SKILLS` etc) -- used here too, not left blank, so
    # the column headers agree across backends instead of drifting.
    title = section.name.replace('_', ' ').title()
    out = [f"<h2>{html.escape(title)}</h2>",
           _TABLE_OPEN if print_mode else "<table>", "<thead>",
           _th_row(("Cost", "END", html.escape(title)),
                   _SECTION_WIDTHS if print_mode else None),
           "</thead>", "<tbody>"]
    for entry in section.entries:
        out.append(_entry_row(entry))
    out.append("</tbody>")
    out.append("</table>")
    return out


def _entry_row(entry: Entry) -> str:
    # cost_before_framework, not cost: a pooled slot's `cost` is 0 because
    # the pool bought the capacity -- the reader wants what it costs alone.
    row_class = ' class="nested"' if entry.parent_id else ""
    return (
        f"<tr{row_class}>"
        f"<td>{_fmt_num(entry.cost_before_framework)}</td>"
        f"<td>{_fmt_num(entry.end)}</td>"
        # `display` carries HD's own markup -- unescaped, deliberately.
        # It also carries HD's double spaces (e.g. after "Name:  Power" --
        # 32/46/26 such runs measured across Bokor/Ravel/PowerLad). Those
        # bytes are preserved exactly here and NOT collapsed by this
        # backend; a browser renders runs of whitespace inside <td> as one
        # space per normal HTML whitespace rules, and HD's own HTML export
        # puts the same strings in the same kind of cell -- so what a
        # reader sees matches HD's own output. This is not a bug to "fix"
        # by touching the bytes; it is the browser's whitespace handling,
        # matching HD's.
        f"<td>{entry.display}</td>"
        "</tr>"
    )


def _prose(prose: Prose) -> list[str]:
    out: list[str] = []
    for attr, heading in _PROSE_FIELDS:
        text = getattr(prose, attr)
        if not text:
            continue
        out.append('<section class="prose">')
        out.append(f"<h2>{heading}</h2>")
        out.append(f"<p>{_escaped_paragraphs(text)}</p>")
        out.append("</section>")

    notes = [note for note in prose.notes if note]
    if notes:
        out.append('<section class="prose">')
        out.append("<h2>Notes</h2>")
        for note in notes:
            out.append(f"<p>{_escaped_paragraphs(note)}</p>")
        out.append("</section>")
    return out


def _escaped_paragraphs(text: str) -> str:
    # Prose is text a person typed -- escaped, then newlines turned into
    # <br> so paragraph breaks a player wrote survive as line breaks.
    return html.escape(text).replace("\n", "<br>")


def _footer(totals) -> list[str]:
    return [
        '<p class="totals">'
        f"<strong>Total:</strong> {_fmt_num(totals.total_points)} &nbsp; "
        f"<strong>Base:</strong> {_fmt_num(totals.base_points)} &nbsp; "
        f"<strong>Complications:</strong> {_fmt_num(totals.complication_points)} &nbsp; "
        f"<strong>Experience:</strong> {_fmt_num(totals.experience)}"
        "</p>"
    ]


def _fmt_height(inches: float) -> str:
    """Inches (kirby-cost's `Hero.height`) as feet'inches" -- 96.45669
    becomes 8'0", not a raw float on the sheet."""
    if not inches:
        return ""
    total = round(inches)
    feet, remainder = divmod(total, 12)
    return f"{feet}'{remainder}\""


def _fmt_weight(pounds: float) -> str:
    """Pounds, rounded for display -- 350.53 becomes "351 lbs"."""
    if not pounds:
        return ""
    return f"{round(pounds)} lbs"


def _fmt_num(value: float) -> str:
    """A cost/END value without the trailing `.0` a whole float carries."""
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"
