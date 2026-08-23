"""The sheet as a PDF document, via `to_html` + `xhtml2pdf`.

`xhtml2pdf` is an OPTIONAL dependency (`pip install kirby-sheet[pdf]`), so
its import lives INSIDE `to_pdf`, not at module scope -- importing
`kirby_sheet.formats.as_pdf` must succeed even when it is not installed.
`xhtml2pdf` also pulls in `reportlab` transitively; do not add reportlab as
a direct dependency here.

This module does not parse HTML back out. It generates the HTML itself (via
`to_html`) and configures it for print AT GENERATION TIME with the
`stylesheet=` parameter -- so there is no need to re-parse what we just
built, and no reason for this module to import bs4. `text.py` is the only
module in this package that imports bs4; a test asserts that boundary and
this module must not be the one that breaks it.
"""
from __future__ import annotations

import io

from kirby_sheet.formats.as_html import to_html
from kirby_sheet.sheet import Sheet

#: The print stylesheet handed to xhtml2pdf. This is NOT the browser
#: stylesheet (`as_html._STYLE`) reused for print -- that CRASHES
#: xhtml2pdf. Its CSS subset computed a negative column width from the
#: browser stylesheet's table cell padding:
#
#     ValueError: <PmlTable 20 rows x 3 cols> ...
#     negative availWidth=-7.5 width=7.5 - leftPadding=11.25 - rightPadding=3.75
#
# Do not "simplify" this back to `stylesheet=None` / reusing `_STYLE`.
#
# Two more things this stylesheet does NOT contain, and must not have added
# back by someone reaching for the obvious CSS fix -- both were tried and
# both broke the actual rendered document (verified on Bokor's real
# characteristics table, not a synthetic one; `err=0` from xhtml2pdf proved
# nothing about either):
#
# - No `td, th { padding: ... }` rule. Any nonzero CSS `padding` on a cell
#   -- even a fraction of a point, nowhere near the crash above -- makes
#   xhtml2pdf silently ABANDON the `<colgroup>` widths `as_html.py` emits
#   (see `to_html`'s `print_mode`): the description/Notes column collapses
#   to a sliver and the table's last two headers print on top of each
#   other. Cell padding for the print path is the HTML `cellpadding`
#   attribute on `<table>` instead (`as_html._TABLE_OPEN`), which xhtml2pdf
#   honours without discarding column widths.
# - No `.identity-block span { margin-right/padding-right: ... }` rule.
#   xhtml2pdf's box model does not apply margin OR padding to an inline
#   `<span>` at all -- both were tried and both rendered as zero gap:
#   "Player: Peter BethkeHair: BaldEyes: Brown...". The gap for the print
#   path is non-breaking spaces joined between fields in the HTML itself
#   (`as_html._PRINT_FIELD_GAP`), not CSS.
_PRINT_CSS = """
    @page { size: letter; margin: 1.5cm; }
    body { font-family: Helvetica; font-size: 8pt; }
    h1 { font-size: 14pt; margin-bottom: 0; }
    h2 { font-size: 10pt; }
    table { width: 100%; }
    th, td { text-align: left; }
"""


def to_pdf(sheet: Sheet, *, title: str | None = None) -> bytes:
    """The sheet, rendered as a PDF document's bytes."""
    try:
        from xhtml2pdf import pisa
    except ImportError as exc:
        raise ImportError(
            "PDF output requires xhtml2pdf -- install it with "
            "`pip install kirby-sheet[pdf]`"
        ) from exc

    document = to_html(sheet, title=title, stylesheet=_PRINT_CSS)

    buffer = io.BytesIO()
    result = pisa.CreatePDF(document, dest=buffer)
    if result.err:
        name = sheet.identity.name or "(unnamed character)"
        raise RuntimeError(
            f"kirby-sheet: failed to render {name!r} as PDF "
            f"(xhtml2pdf reported {result.err} error(s))"
        )
    return buffer.getvalue()
