"""kirby-sheet may depend only on what sits BELOW it.

The dependency direction is one-way: build hierarchically, a lower module may
be referenced from above, never the reverse.

**This gate is an ALLOWLIST, deliberately, and it names nothing above this
layer.** A denylist has to write down what it forbids, and that writing ships —
a test whose NAME forbids a package tells any reader the package exists, which
is disclosure rather than engineering. An allowlist states this layer's position
positively, and is strictly stronger besides: it catches a consumer nobody
anticipated, which a denylist by construction cannot.

Adding a real dependency means adding it to pyproject AND to this list. That
friction is intended — a new edge in the dependency graph should be a decision,
not a drive-by import.
"""
from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "kirby_sheet"

OWN = {"kirby_sheet"}

#: Declared runtime dependencies — must match pyproject's `dependencies`.
#: `bs4` is beautifulsoup4's import name, which differs from its dist name.
DECLARED = {"kirby_cost", "bs4"}

#: Optional extras, importable only when installed. Guarded at their call
#: sites; allowed here so the gate does not fail on an optional feature.
OPTIONAL = {"xhtml2pdf", "reportlab"}

ALLOWED = OWN | DECLARED | OPTIONAL | set(sys.stdlib_module_names)


def _package_files() -> list[pathlib.Path]:
    return sorted(PACKAGE.rglob("*.py"))


def _top_level_imports(path: pathlib.Path) -> set[str]:
    """Top-level component of every absolute import. Relative imports are
    intra-package by definition and cannot point upward."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_the_package_has_files_to_check():
    """Guards the guard: an empty glob would make the real test pass while
    checking nothing."""
    assert len(_package_files()) > 5, (
        f"expected the package, found {len(_package_files())} files"
    )


def test_the_allowlist_is_not_vacuous():
    assert "kirby_cost" in ALLOWED and "os" in ALLOWED
    assert "sqlalchemy" not in ALLOWED, "the allowlist has stopped excluding anything"


def test_the_renderer_imports_only_what_sits_below_it():
    offenders = []
    for path in _package_files():
        for mod in sorted(_top_level_imports(path)):
            if mod not in ALLOWED:
                offenders.append(f"{path.relative_to(ROOT)}: imports {mod!r}")
    assert not offenders, (
        "kirby_sheet/ may import only the standard library, itself, and its "
        "declared dependencies. Anything else is a dependency on a layer at "
        "or above this one:\n" + "\n".join(offenders)
    )
