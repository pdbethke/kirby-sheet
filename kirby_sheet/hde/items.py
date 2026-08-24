"""The generic per-item tokens.

``getGeneralString`` (HTMLWriter.java:3977-4307), the part of it the shipped
6E template uses. These tokens appear inside every section's item block and
mean "of THIS object", which is why they are resolved against one object at a
time rather than across the document.

Only what the shipped template names is ported. The tokens left out --
MODIFIERS, ATTRIBUTE_VALUE's reflection loop, the type filters, IF_RANGED and
the rest -- are named here so their absence is a recorded decision rather than
an oversight; adding one is a matter of transcribing its lines.
"""
from __future__ import annotations

from kirby_cost.util.rounder import round_up

from kirby_sheet.engine import get_long_value, swap_long_value, swap_value


def apply(block: str, obj) -> str:
    """Resolve one item's generic tokens within its block."""
    block = _conditional(block, "IFNAME", _is_named(obj))
    block = _conditional(block, "IS_SEPARATOR", _is_separator(obj))
    block = _conditional(block, "IS_LIST", _is_named_list(obj))
    block = _conditional(block, "IS_NOT_LIST", not _is_list(obj))
    block = _conditional(block, "IS_NOT_SEPARATOR", not _is_separator(obj))

    option = getattr(obj, "selected_option", None)
    for tag, value in (
        ("NAME", getattr(obj, "name", "") or ""),
        ("XMLID", getattr(obj, "xmlid", "") or ""),
        ("LEVELS", str(getattr(obj, "levels", 0) or 0)),
        ("DISPLAY", getattr(obj, "display", "") or ""),
        ("INPUT", getattr(obj, "input", "") or ""),
        ("ALIAS", getattr(obj, "alias", "") or ""),
        ("TEXT", _text(obj)),
        ("NOTES", _notes(obj)),
        ("OPTION", getattr(option, "display", "") or "" if option else ""),
        ("OPTION_ALIAS", getattr(option, "alias", "") or "" if option else ""),
        ("OPTION_ID", getattr(option, "xmlid", "") or "" if option else ""),
        ("ACTIVE_COST", str(round_up(getattr(obj, "active_cost", 0) or 0))),
    ):
        block = swap_value(f"<!--{tag}-->", value, block)
    return block


def _conditional(block: str, tag: str, keep: bool) -> str:
    """Keep or strip every `<!--TAG-->…<!--/TAG-->` block.

    Java loops with getLongValue/swapLongValue until none remain rather than
    replacing once, because a template may use the same conditional twice.
    """
    open_tag, close_tag = f"<!--{tag}-->", f"<!--/{tag}-->"
    while True:
        body = get_long_value(open_tag, close_tag, block)
        if body is None:
            return block
        block = swap_long_value(open_tag, close_tag, body if keep else "", block)


def _is_named(obj) -> bool:
    """Java tests `getName().trim().length() > 0` -- whitespace is unnamed."""
    return bool((getattr(obj, "name", "") or "").strip())


def _is_list(obj) -> bool:
    from kirby_cost.objects.list import List
    return isinstance(obj, List)


def _is_named_list(obj) -> bool:
    """IS_LIST: a List container that has an alias (HTMLWriter.java:4108)."""
    return _is_list(obj) and bool((getattr(obj, "alias", "") or "").strip())


def _is_separator(obj) -> bool:
    """IS_SEPARATOR: a List container with a BLANK alias -- a bare rule
    between rows rather than a named group (HTMLWriter.java:4142)."""
    return _is_list(obj) and not (getattr(obj, "alias", "") or "").strip()


def _text(obj) -> str:
    """TEXT is the nameless column-2 output, plus the parent list's suffix
    when the object hangs off one (HTMLWriter.java:4237-4240)."""
    text = getattr(obj, "nameless_column2_output", "") or ""
    parent = getattr(obj, "parent", None)
    if parent is not None and hasattr(parent, "column2_suffix"):
        text += parent.column2_suffix(obj)
    return text


def _notes(obj) -> str:
    """HTMLWriter.java:4284-4291. Notes when the object asks for them,
    otherwise a quantity marker, otherwise nothing."""
    if getattr(obj, "include_notes_in_printout", False):
        return getattr(obj, "output_notes", None) or getattr(obj, "notes", "") or ""
    quantity = getattr(obj, "quantity", 1) or 1
    if quantity > 1:
        return f"(x{quantity} number of items)"
    return ""
