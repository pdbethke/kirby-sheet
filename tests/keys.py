"""Comparing our output against Hero Designer's, one key at a time.

`pdf_format_6.hde` is a flat `key: value` document, which is what makes a
phased port gateable at all: a phase can prove the keys it implements without
waiting for the whole document to match. That was the reason for choosing this
template as the target -- an HTML sheet would have offered no such seam.

RAW LINES, not parsed values. `flash_def:` has no space after the colon where
`campaign: ` does. That is HD's output and not ours to normalise, so the
comparison keeps the whole line and a difference in that space fails.

TOP-LEVEL keys only. List-item keys are indented and repeat once per item, so
they are not addressable by name; sections are proven by body comparison in
test_hde_lists.py and by whole-document fidelity in test_byte_fidelity.py.

Chosen over a shrinking-diff metric deliberately. A diff that is still
shrinking can shrink for reasons unrelated to the phase under test, and a key
claimed but rendered wrong would hide inside it.
"""
from __future__ import annotations

import re

from kirby_sheet.render import render
from kirby_sheet.template import Template
from tests.corpus import character_path, template_path
from tests.oracle import normalise, oracle_export

#: A top-level `key:` line -- column zero, no leading whitespace.
_KEY = re.compile(r"^([a-z_][a-z_0-9]*):")

#: What the byte-fidelity gate already pins, so our output and HD's can be
#: compared at all. `normalise()` collapses HD's real values to the same
#: string. character_file is NOT here: it is per-character, so `both()`
#: supplies it.
PINNED = dict(app_version="headless-fork", timestamp="<PINNED>",
              export_id="<PINNED>", save_timestamp="<PINNED>")


def scalar_lines(document: str) -> dict[str, str]:
    """key -> the entire raw line, for every top-level `key:` line."""
    found: dict[str, str] = {}
    for line in document.splitlines():
        match = _KEY.match(line)
        if match:
            found[match.group(1)] = line
    return found


def both(keys: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """(ours, HD's) as key -> raw line, for the configured template.

    `keys` is not used to filter -- both sides are returned whole. It is taken
    so that callers read as "give me these keys from both", and so a future
    change could narrow the work without touching call sites.
    """
    from kirby_cost.io.hdc_loader import HDCLoader
    character, template = character_path(), template_path()
    hero = HDCLoader().load_file(str(character))
    ours = render(Template.from_path(template), hero,
                  character_file=character.name, **PINNED)
    theirs = oracle_export(template, character)
    return scalar_lines(normalise(ours)), scalar_lines(normalise(theirs))


def compare(ours: dict[str, str], theirs: dict[str, str], keys: list[str]) -> int:
    """Assert every named key matches. Returns how many were compared.

    The empty-keys guard is the point of this function. A comparison over zero
    keys passes trivially, which is exactly the shape of the sixteen
    tests-that-could-not-fail this project has already found. Callers assert
    the returned count for the same reason.
    """
    assert keys, "no keys named - a comparison over zero keys always passes"
    absent = [k for k in keys if k not in theirs]
    assert not absent, (
        f"the oracle emits no such keys: {absent} -- the key names in this "
        f"test are wrong, or the template changed")
    differing = {k: (ours.get(k), theirs[k]) for k in keys if ours.get(k) != theirs[k]}
    assert not differing, "\n".join(
        [f"{len(differing)} of {len(keys)} keys differ:"]
        + [f"  {k}\n    ours: {o!r}\n    HD:   {t!r}"
           for k, (o, t) in differing.items()])
    return len(keys)
