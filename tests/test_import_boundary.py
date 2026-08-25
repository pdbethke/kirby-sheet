"""kirby-cost may be imported by `build.py` and `hde/` only.

Not tidiness. It is why every other module's tests run with no engine, no
template and no character file installed -- a contributor with none of Hero
Designer still gets a green run on everything except the oracle gates.

Parsed with `ast`, not grepped. A text scan flags a docstring that merely
NAMES kirby_cost -- `formats/totals_view.py` cites
`kirby_cost.io.hdc_loader.LoadedHero` to explain where a value comes from,
which is documentation doing its job, not a boundary violation. The rule is
about imports, so the guard reads imports.
"""
from __future__ import annotations

import ast
import pathlib

#: Paths, relative to kirby_sheet/, permitted to import kirby_cost.
#: `build.py` turns a character into a Sheet; `hde/` renders the .hde backend
#: straight off the engine's LoadedHero.
ALLOWED = ("build.py", "hde")

ROOT = pathlib.Path(__file__).resolve().parent.parent / "kirby_sheet"


def _imports_kirby_cost(source: str) -> bool:
    """True if the module actually imports kirby_cost, at any nesting depth.

    Function-level imports count: `build.py` imports HDCLoader inside its
    functions, and a module smuggling one into a method would be violating
    the boundary just as much as one importing at the top.
    """
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            if any(a.name.split(".")[0] == "kirby_cost" for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "kirby_cost":
                return True
    return False


def _importers(root: pathlib.Path) -> list[str]:
    found = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if relative.parts[0] in ALLOWED:
            continue
        if _imports_kirby_cost(path.read_text(encoding="utf-8")):
            found.append(str(relative))
    return found


def test_only_build_and_hde_import_kirby_cost():
    offenders = _importers(ROOT)
    assert offenders == [], f"these must not import kirby_cost: {offenders}"


def test_this_guard_is_inspecting_real_files():
    """A guard pointed at the wrong tree returns an empty list forever and
    passes for the rest of the project's life."""
    assert ROOT.is_dir(), f"{ROOT} is not a directory"
    assert len(list(ROOT.rglob("*.py"))) > 5
    build = ROOT / "build.py"
    assert build.is_file()
    assert _imports_kirby_cost(build.read_text(encoding="utf-8")), (
        "build.py no longer imports kirby_cost -- either the boundary moved "
        "or this guard is reading the wrong file")


def test_the_scan_reports_a_real_violation(tmp_path):
    """Point the scan at a tree with a known offender. Without this,
    `offenders == []` proves only that the function returns an empty list."""
    fake = tmp_path / "kirby_sheet"
    (fake / "hde").mkdir(parents=True)
    (fake / "hde" / "spine.py").write_text("import kirby_cost\n")
    (fake / "build.py").write_text("from kirby_cost.io.hdc_loader import HDCLoader\n")
    (fake / "cli.py").write_text("from kirby_cost.io.hdc_loader import HDCLoader\n")
    (fake / "text.py").write_text("import bs4\n")
    assert _importers(fake) == ["cli.py"]


def test_a_docstring_mention_is_not_a_violation(tmp_path):
    """The false positive this guard was rewritten to avoid: naming the
    engine in prose must stay allowed, or documentation gets worse to keep a
    test green."""
    fake = tmp_path / "kirby_sheet"
    fake.mkdir(parents=True)
    (fake / "totals_view.py").write_text(
        '"""Values come from kirby_cost.io.hdc_loader.LoadedHero."""\n')
    assert _importers(fake) == []


def test_a_function_level_import_is_still_a_violation(tmp_path):
    """Nesting an import inside a function must not evade the boundary."""
    fake = tmp_path / "kirby_sheet"
    fake.mkdir(parents=True)
    (fake / "sneaky.py").write_text(
        "def load(p):\n    from kirby_cost.io.hdc_loader import HDCLoader\n    return p\n")
    assert _importers(fake) == ["sneaky.py"]
