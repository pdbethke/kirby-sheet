"""The sheet as JSON.

This is not kirby-cost's `to_build_json`. That document says how to REBUILD a
character — xmlids, base costs, modifiers — and deliberately carries no
display strings and no computed costs. This one says what a character's sheet
SAYS. Opposite directions; a consumer wanting to reconstruct a character wants
the other one.
"""
from __future__ import annotations

import dataclasses
import json

from kirby_sheet.sheet import Sheet


def to_json(sheet: Sheet, *, indent: int | None = 2) -> str:
    """Serialise a Sheet.

    `ensure_ascii=False` because a sheet carries prose a person wrote — names,
    backgrounds, power descriptions — and escaping it to \\uXXXX makes a file
    meant to be read by humans worse for no gain. The output is UTF-8, settled
    by measurement when the .hde backend was built.

    `sections` is a LIST of named objects rather than an object keyed by name,
    so that the sheet's order survives; JSON objects do not promise order and
    a reader should not have to reconstruct it.
    """
    return json.dumps(dataclasses.asdict(sheet), indent=indent, ensure_ascii=False)
