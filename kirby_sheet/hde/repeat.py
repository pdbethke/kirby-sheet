"""Rendering a repeated block, once per item.

**This is not a fifth primitive.** `engine.py`'s header already states the
shape: a list is rendered by extracting its block once with `get_long_value`,
rendering that block per item, joining, and putting the accumulation back with
`swap_long_value`. Every `get*String` helper in HTMLWriter is built this way.
Implementing it here is transcription of something already written down.

Nesting works by applying the same operation to the ITEM block before the item
block is joined -- which is how `ADDERS` renders inside `PERKS` and `DISADS`.
"""
from __future__ import annotations

from typing import Callable, Sequence

from kirby_sheet.engine import get_long_value, swap_long_value

#: (block, item, index) -> the rendered block for that item.
ItemRenderer = Callable[[str, object, int], str]


def render_list(text: str, open_tag: str, close_tag: str,
                items: Sequence, render_item: ItemRenderer) -> str:
    """Replace one `open_tag`..`close_tag` block with it rendered per item.

    An empty `items` removes the block, matching HD: a section with nothing in
    it prints its heading and no rows, not an empty row.

    A block that is not present leaves `text` untouched -- a template need not
    use every section, and a missing one is not an error.
    """
    body = get_long_value(open_tag, close_tag, text)
    if body is None:
        return text
    # A FRESH copy of the body per item. Passing one shared string would be
    # fine here because Python strings are immutable, but the contract that
    # each item starts from the unrendered block is what callers rely on, so
    # it is stated rather than left to that accident.
    rendered = "".join(render_item(body, item, index)
                       for index, item in enumerate(items))
    return swap_long_value(open_tag, close_tag, rendered, text)
