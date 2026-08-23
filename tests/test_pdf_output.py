"""Sheet -> PDF, via `to_html(stylesheet=...)` + xhtml2pdf.

xhtml2pdf is an optional dependency, installed in this dev environment, so
most tests here exercise the real thing rather than mocking it -- a mocked
PDF library would only prove we called a function, not that a reader gets a
usable document. The one test that DOES simulate xhtml2pdf's absence patches
`sys.modules`, not the behaviour of `to_pdf` itself.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest

import pypdf

from kirby_sheet.formats.as_html import to_html
from kirby_sheet.sheet import (CharacteristicRow, Entry, Identity, Prose,
                               Section, Sheet, Totals)

pytest.importorskip("xhtml2pdf")
from kirby_sheet.formats.as_pdf import to_pdf  # noqa: E402


# --- fixtures ---------------------------------------------------------

def _sheet(**kw):
    base = dict(
        identity=Identity(name="Identity-name"),
        characteristics=(),
        sections=(),
        prose=Prose(),
        totals=Totals(),
    )
    base.update(kw)
    return Sheet(**base)


def _entry(**kw):
    base = dict(id="Entry-id", name="Entry-name", alias="Entry-alias",
                xmlid="Entry-xmlid", display="Display-str", cost=1.0,
                cost_before_framework=2.0, active_cost=3.0, end=4.0,
                parent_id="")
    base.update(kw)
    return Entry(**base)


def _extract_text(pdf_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() for page in reader.pages)


# --- real characters ----------------------------------------------------

#: This module's own fixture paths, named explicitly rather than routed
#: through KIRBY_SHEET_HDC -- the PDF suite needs THREE specific characters
#: at once (a name to find, PowerLad's fractional values, HD markup in a
#: real description), where every other backend's tests only ever need
#: "some" character via that one env var.
_BOKOR = Path("~/Documents/Champions/Bokor.hdc").expanduser()
_POWERLAD = Path("~/Desktop/PowerLad.hdc").expanduser()

_needs_bokor = pytest.mark.skipif(
    not _BOKOR.is_file() or not (os.environ.get("KIRBY_COST_HDT") or "").strip(),
    reason="needs Bokor.hdc and KIRBY_COST_HDT",
)
_needs_powerlad = pytest.mark.skipif(
    not _POWERLAD.is_file() or not (os.environ.get("KIRBY_COST_HDT") or "").strip(),
    reason="needs PowerLad.hdc and KIRBY_COST_HDT",
)


@_needs_bokor
def test_bytes_start_with_pdf_header():
    from kirby_sheet.build import sheet_from_hdc

    sheet = sheet_from_hdc(_BOKOR)
    pdf_bytes = to_pdf(sheet)

    assert pdf_bytes.startswith(b"%PDF-")


@_needs_bokor
def test_extracted_text_contains_the_characters_name():
    from kirby_sheet.build import sheet_from_hdc

    sheet = sheet_from_hdc(_BOKOR)
    pdf_bytes = to_pdf(sheet)

    text = _extract_text(pdf_bytes)
    assert sheet.identity.name in text
    assert sheet.identity.name == "Bokor"


@_needs_bokor
def test_bokor_renders_in_a_sane_page_count():
    """A regression guard for the print stylesheet, not a design spec: an
    earlier version of `_PRINT_CSS` built cleanly (xhtml2pdf reported
    err=0) but silently abandoned the `<colgroup>` widths under a CSS
    `padding` rule, wrapping every power description into a one-inch-wide
    ribbon -- Bokor came out at 21 pages. `err=0` and a nonzero byte count
    don't prove the layout is usable; a page count does. Bokor renders at 6
    pages with a working stylesheet -- pinned well under that, not at the
    exact number, so a future content change to Bokor.hdc doesn't make this
    flaky."""
    from kirby_sheet.build import sheet_from_hdc

    sheet = sheet_from_hdc(_BOKOR)
    pdf_bytes = to_pdf(sheet)

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) < 10


@_needs_powerlad
def test_a_fractional_cost_survives_to_the_pdf():
    """PowerLad's Iron Grasshopper is a real 44.5-point power. A narrowing
    cast turned 44.5 into 44 in this project once, displayed beside text
    reading "(45 Active Points)" -- this is the PDF backend's copy of that
    guard."""
    from kirby_sheet.build import sheet_from_hdc

    sheet = sheet_from_hdc(_POWERLAD)
    pdf_bytes = to_pdf(sheet)

    text = _extract_text(pdf_bytes)
    assert "44.5" in text


@_needs_powerlad
def test_hd_markup_does_not_leak_as_literal_tags():
    """PowerLad's powers carry HD's own `<i>` markup on their names (e.g.
    "Iron Grasshopper"). It must drive real italics in the PDF, not survive
    as literal angle brackets or entities in the extracted text -- while the
    italicised words themselves are still present."""
    from kirby_sheet.build import sheet_from_hdc

    sheet = sheet_from_hdc(_POWERLAD)
    pdf_bytes = to_pdf(sheet)

    text = _extract_text(pdf_bytes)
    assert "<i>" not in text
    assert "&lt;i&gt;" not in text
    assert "Iron Grasshopper" in text


# --- prose with markup-lookalike characters ------------------------------

def test_prose_with_angle_brackets_and_ampersand_renders_without_corrupting():
    """A stub sheet, not a real character: this needs a background containing
    `<` and `&`, not whatever a real character's background happens to
    contain. The tag-shaped fragment (`<i>tag-like</i>`) matters, not just
    the bare `<` and `&`: xhtml2pdf's parser tolerates `a < b & c` as plain
    text either way (a lone `<` followed by a space is not a tag start), so
    that string alone can't tell a correctly-escaped background from an
    unescaped one that got lucky -- a real, well-formed tag is what actually
    gets parsed as markup (and so disappears from the extracted text) if
    this backend fails to escape it."""
    sheet = _sheet(prose=Prose(
        background="a < b & c and <i>tag-like</i> text"))

    pdf_bytes = to_pdf(sheet)

    assert pdf_bytes.startswith(b"%PDF-")
    text = _extract_text(pdf_bytes)
    assert "a < b & c and <i>tag-like</i> text" in text


# --- to_html(stylesheet=...) ---------------------------------------------

def test_to_html_with_no_stylesheet_is_byte_identical_to_before():
    sheet = _sheet(
        identity=Identity(name="Bolt & Sting", player_name="Ann & Co"),
        characteristics=(CharacteristicRow(
            xmlid="STR-xmlid", name="STR", value=15.0, base=10.0, cost=5.0,
            active_cost=7.0, total="15", roll="12-", notes="<i>Note</i>"),),
        sections=(Section(name="powers", entries=(_entry(),)),),
        prose=Prose(background="a < b & c"),
        totals=Totals(total_points=123.0),
    )

    out_default = to_html(sheet)
    out_explicit_none = to_html(sheet, stylesheet=None)

    assert out_default == out_explicit_none
    # And no print-mode artefacts (colgroup, cellpadding) leak into the
    # default path.
    assert "colgroup" not in out_default
    assert "cellpadding" not in out_default


def test_to_html_stylesheet_parameter_replaces_the_style_block():
    sheet = _sheet()

    out = to_html(sheet, stylesheet="body { color: rebeccapurple; }")

    assert "<style>body { color: rebeccapurple; }</style>" in out
    assert "Georgia" not in out  # the default screen font is gone


# --- CLI ------------------------------------------------------------------

@_needs_bokor
def test_pdf_flag_without_o_is_rejected(capsys):
    from kirby_sheet.cli import main

    code = main([str(_BOKOR), "--pdf"])

    assert code != 0
    err = capsys.readouterr().err
    assert "-o" in err


@_needs_bokor
def test_pdf_flag_with_o_writes_a_real_pdf(tmp_path):
    from kirby_sheet.cli import main

    out_file = tmp_path / "sheet.pdf"

    code = main([str(_BOKOR), "--pdf", "-o", str(out_file)])

    assert code == 0
    assert out_file.read_bytes().startswith(b"%PDF-")


# --- bs4 stays out of this module ------------------------------------------

def test_as_pdf_does_not_import_bs4():
    """`text.py` is the only module in this package permitted to import
    bs4 (see its own docstring): `as_pdf.py` generates print-ready HTML at
    generation time via `to_html(stylesheet=...)` and has no reason to
    parse HTML back out. This guards that boundary directly against the
    module's actual imports (via `ast`), not a text grep -- a grep would
    also flag this file's own docstring prose that merely discusses bs4."""
    import ast

    import kirby_sheet.formats.as_pdf as module
    source = open(module.__file__, encoding="utf-8").read()
    tree = ast.parse(source)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module)

    assert not any(name == "bs4" or name.startswith("bs4.")
                   for name in imported_names)


# --- optional-dependency boundary -----------------------------------------

def test_as_pdf_imports_cleanly_without_xhtml2pdf_installed(monkeypatch):
    """`kirby_sheet.formats.as_pdf` must be importable even when xhtml2pdf
    is not -- the xhtml2pdf import lives inside `to_pdf`, not at module
    scope. Simulated by removing the already-imported module and the
    already-imported `kirby_sheet.formats.as_pdf` module from `sys.modules`
    and blocking a fresh import of xhtml2pdf, rather than uninstalling the
    real package."""
    import builtins

    real_import = builtins.__import__

    def _blocking_import(name, *args, **kwargs):
        if name == "xhtml2pdf" or name.startswith("xhtml2pdf."):
            raise ImportError("simulated: xhtml2pdf not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "xhtml2pdf", raising=False)
    monkeypatch.delitem(sys.modules, "xhtml2pdf.pisa", raising=False)
    monkeypatch.delitem(sys.modules, "kirby_sheet.formats.as_pdf", raising=False)
    monkeypatch.setattr(builtins, "__import__", _blocking_import)

    import importlib
    module = importlib.import_module("kirby_sheet.formats.as_pdf")

    with pytest.raises(ImportError) as excinfo:
        module.to_pdf(_sheet())

    assert "kirby-sheet[pdf]" in str(excinfo.value)
