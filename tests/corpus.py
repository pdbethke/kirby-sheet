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

#: variable -> what it should name. KIRBY_SHEET_HDE, which points at a
#: user-supplied template, arrives in Milestone 2 — this milestone's gate
#: renders the bundled minimal.hde, so nothing here would read it.
INPUTS = {
    "KIRBY_SHEET_HDC": "a .hdc character to render",
    "KIRBY_SHEET_ORACLE": "the hd6cli.sh wrapper from kirby-hd-oracle",
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
