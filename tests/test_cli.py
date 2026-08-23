"""`kirby-sheet CHAR.hdc --json [-o FILE]`, via `main()` rather than a
subprocess -- that is the point of `main(argv) -> int`."""
from __future__ import annotations

import json
import os

import pytest

from kirby_sheet.cli import main
from tests.corpus import character_path

#: Tests that actually load a character need both a .hdc (KIRBY_SHEET_HDC)
#: and kirby-cost's template (KIRBY_COST_HDT). Neither ships with the repo.
_needs_character = pytest.mark.skipif(
    character_path() is None or not (os.environ.get("KIRBY_COST_HDT") or "").strip(),
    reason="needs KIRBY_SHEET_HDC and KIRBY_COST_HDT",
)


@_needs_character
def test_json_flag_writes_valid_json_to_stdout(capsys):
    code = main([str(character_path()), "--json"])

    assert code == 0
    doc = json.loads(capsys.readouterr().out)
    assert sorted(doc) == ["characteristics", "identity", "prose", "sections", "totals"]


@_needs_character
def test_o_writes_the_document_to_a_file_as_utf8(tmp_path, capsys):
    out_file = tmp_path / "sheet.json"

    code = main([str(character_path()), "--json", "-o", str(out_file)])

    assert code == 0
    assert capsys.readouterr().out == ""  # went to the file, not stdout
    doc = json.loads(out_file.read_bytes().decode("utf-8"))
    assert "identity" in doc


@_needs_character
def test_text_flag_writes_rendered_sheet_to_stdout(capsys):
    from kirby_sheet.build import sheet_from_hdc
    from kirby_sheet.formats.as_text import to_text

    code = main([str(character_path()), "--text"])

    assert code == 0
    out = capsys.readouterr().out
    expected = to_text(sheet_from_hdc(character_path()))
    assert out == expected or out == expected + "\n"


@_needs_character
def test_text_o_writes_the_document_to_a_file_as_utf8(tmp_path, capsys):
    from kirby_sheet.build import sheet_from_hdc
    from kirby_sheet.formats.as_text import to_text

    out_file = tmp_path / "sheet.txt"

    code = main([str(character_path()), "--text", "-o", str(out_file)])

    assert code == 0
    assert capsys.readouterr().out == ""  # went to the file, not stdout
    doc = out_file.read_bytes().decode("utf-8")
    assert doc == to_text(sheet_from_hdc(character_path()))


@_needs_character
def test_html_flag_writes_rendered_sheet_to_stdout(capsys):
    from kirby_sheet.build import sheet_from_hdc
    from kirby_sheet.formats.as_html import to_html

    code = main([str(character_path()), "--html"])

    assert code == 0
    out = capsys.readouterr().out
    expected = to_html(sheet_from_hdc(character_path()))
    assert out == expected or out == expected + "\n"


@_needs_character
def test_html_o_writes_the_document_to_a_file_as_utf8(tmp_path, capsys):
    from kirby_sheet.build import sheet_from_hdc
    from kirby_sheet.formats.as_html import to_html

    out_file = tmp_path / "sheet.html"

    code = main([str(character_path()), "--html", "-o", str(out_file)])

    assert code == 0
    assert capsys.readouterr().out == ""  # went to the file, not stdout
    doc = out_file.read_bytes().decode("utf-8")
    assert doc == to_html(sheet_from_hdc(character_path()))


def test_json_and_text_together_are_rejected(capsys):
    code = main(["--json", "--text", "somefile.hdc"])

    assert code != 0
    err = capsys.readouterr().err
    assert "not allowed with" in err.lower() or "usage" in err.lower()


def test_neither_json_nor_text_is_rejected(tmp_path, capsys):
    dummy = tmp_path / "x.hdc"
    dummy.write_text("")

    code = main([str(dummy)])

    assert code != 0
    err = capsys.readouterr().err
    assert "usage" in err.lower()


def test_missing_input_file_exits_nonzero_and_names_the_path(tmp_path, capsys):
    missing = tmp_path / "nope.hdc"

    code = main([str(missing), "--json"])

    assert code != 0
    err = capsys.readouterr().err
    assert str(missing) in err


def test_no_arguments_exits_nonzero_with_usage(capsys):
    code = main([])

    assert code != 0
    err = capsys.readouterr().err
    assert "usage" in err.lower()


@_needs_character
def test_unset_hdt_env_names_the_variable(monkeypatch, capsys):
    monkeypatch.delenv("KIRBY_COST_HDT", raising=False)

    code = main([str(character_path()), "--json"])

    assert code != 0
    err = capsys.readouterr().err
    assert "KIRBY_COST_HDT" in err


# --- --hdc: LoadedHero -> write_hdc, not through the Sheet -----------------

@_needs_character
def test_hdc_flag_without_o_is_rejected(capsys):
    code = main([str(character_path()), "--hdc"])

    assert code != 0
    err = capsys.readouterr().err
    assert "-o" in err


@_needs_character
def test_hdc_flag_with_o_writes_a_file_that_reloads_with_the_same_name(tmp_path):
    from kirby_sheet.build import sheet_from_hdc

    out_file = tmp_path / "roundtrip.hdc"
    source_sheet = sheet_from_hdc(character_path())

    code = main([str(character_path()), "--hdc", "-o", str(out_file)])

    assert code == 0
    assert out_file.is_file()
    reloaded = sheet_from_hdc(out_file)
    assert reloaded.identity.name == source_sheet.identity.name
    assert reloaded.totals.total_points == source_sheet.totals.total_points


# --- --inspect: a TEMPLATE, not a character -------------------------------

def test_inspect_flag_needs_no_character_argument(tmp_path, capsys):
    template = tmp_path / "t.hde"
    template.write_text("<!--APP_VERSION--><!--CHARACTER_NAME-->")

    code = main(["--inspect", str(template)])

    assert code == 0
    out = capsys.readouterr().out
    assert "2 tokens used" in out
    assert "1 resolved" in out
    assert "1 unresolved" in out
    assert "CHARACTER_NAME" in out


def test_inspect_flag_writes_to_a_file_with_o(tmp_path, capsys):
    template = tmp_path / "t.hde"
    template.write_text("<!--APP_VERSION-->")
    out_file = tmp_path / "report.txt"

    code = main(["--inspect", str(template), "-o", str(out_file)])

    assert code == 0
    assert capsys.readouterr().out == ""  # went to the file, not stdout
    assert "1 tokens used" in out_file.read_text(encoding="utf-8")


def test_inspect_flag_missing_template_names_the_path(tmp_path, capsys):
    missing = tmp_path / "nope.hde"

    code = main(["--inspect", str(missing)])

    assert code != 0
    err = capsys.readouterr().err
    assert str(missing) in err


def test_inspect_with_a_character_argument_is_rejected(tmp_path, capsys):
    """kirby-sheet CHAR.hdc --inspect T.hde must not silently ignore the
    character -- --inspect takes a template, not a character."""
    template = tmp_path / "t.hde"
    template.write_text("<!--APP_VERSION-->")
    character = tmp_path / "char.hdc"
    character.write_text("not really an hdc")

    code = main([str(character), "--inspect", str(template)])

    assert code != 0
    err = capsys.readouterr().err
    assert "--inspect" in err
    assert "template" in err.lower()
    assert "character" in err.lower()


def test_inspect_and_json_together_are_rejected(tmp_path, capsys):
    template = tmp_path / "t.hde"
    template.write_text("x")

    code = main(["--inspect", str(template), "--json"])

    assert code != 0
    err = capsys.readouterr().err
    assert "not allowed with" in err.lower()


def test_cli_does_not_import_kirby_cost_directly():
    """build.py is the only module in this package permitted to import
    kirby-cost -- cli.py reaches --hdc through `copy_hdc`, not through
    kirby-cost itself."""
    import kirby_sheet.cli as module
    source = open(module.__file__, encoding="utf-8").read()
    assert "kirby_cost" not in source
