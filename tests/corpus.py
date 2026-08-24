"""Where the machine-bound inputs live, if they live anywhere.

kirby-sheet ships no Hero Games content — no templates, no characters, no
oracle. Tests that need them find them here and skip cleanly when they are
absent. A contributor with none of it must still get a green run.

Modelled on kirby-cost/tests/corpus.py, including its rule that there are no
defaults: guessing at a sibling checkout only ever worked on one machine.
"""
from __future__ import annotations

import os
from pathlib import Path

#: variable -> what it should name. KIRBY_SHEET_HDE arrived with the full
#: .hde backend: the opening milestone's gate rendered the bundled
#: minimal.hde, but the byte-fidelity gate now targets a real shipped
#: template, which this project does not ship and must be pointed at.
INPUTS = {
    "KIRBY_SHEET_HDC": "a .hdc character to render",
    "KIRBY_SHEET_ORACLE": "the hd6cli.sh wrapper from kirby-hd-oracle",
    "KIRBY_SHEET_HDE": "the .hde export template to render (pdf_format_6.hde)",
}


def _from_env(var: str) -> Path | None:
    value = (os.environ.get(var) or "").strip()
    if not value:
        return None
    path = Path(value)
    return path if path.exists() else None


def character_path() -> Path | None:
    return _from_env("KIRBY_SHEET_HDC")


def oracle_path() -> Path | None:
    return _from_env("KIRBY_SHEET_ORACLE")


def template_path() -> Path | None:
    return _from_env("KIRBY_SHEET_HDE")


def why_unavailable() -> str:
    """Which inputs are missing, and whether they were unset or mispointed.

    `_from_env` deliberately answers None for both "not set" and "set to a
    path that does not exist" — the same choice kirby-cost's corpus.py makes.
    That is safe for resolution and dangerous for reporting: a CI job whose
    oracle path moved would skip exactly like a contributor who has no Hero
    Designer, and both would read as green. Naming the difference here is what
    keeps a broken setup from looking like an intentional one.
    """
    problems = []
    for var in ("KIRBY_SHEET_ORACLE", "KIRBY_SHEET_HDC", "KIRBY_SHEET_HDE"):
        raw = (os.environ.get(var) or "").strip()
        if not raw:
            problems.append(f"{var} unset")
        elif not Path(raw).exists():
            problems.append(f"{var} points at a path that does not exist: {raw}")
    return "; ".join(problems)
