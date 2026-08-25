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


def _read(obj, attribute: str, default=""):
    """An attribute's value, calling it when kirby-cost exposes it as a method.

    The engine is inconsistent about this -- `display` is a property on one
    class and a zero-argument method on another -- and passing a bound method
    into swap_value fails with "can only concatenate str (not method)". Java
    has no such split: every one of these is a getter.
    """
    value = getattr(obj, attribute, default)
    if callable(value):
        try:
            value = value()
        except TypeError:
            return default
    return default if value is None else value


def apply(block: str, obj) -> str:
    """Resolve one item's generic tokens within its block."""
    block = _conditional(block, "IFNAME", _is_named(obj))
    block = _conditional(block, "IS_SEPARATOR", _is_separator(obj))
    block = _conditional(block, "IS_LIST", _is_named_list(obj))
    block = _conditional(block, "IS_NOT_LIST", not _is_list(obj))
    block = _conditional(block, "IS_NOT_SEPARATOR", not _is_separator(obj))
    block = _list_item(block, obj)
    block = _filter_by_type(block, obj)

    option = getattr(obj, "selected_option", None)
    for tag, value in (
        ("NAME", _read(obj, "name")),
        # The DOCUMENT's xmlid, not the class's. HD prints what the file
        # said, and a Multipower's file says GENERIC_OBJECT.
        ("XMLID", _read(obj, "document_xmlid") or _read(obj, "xmlid")),
        ("LEVELS", str(_read(obj, "levels", 0) or 0)),
        ("DISPLAY", _read(obj, "display")),
        ("INPUT", _read(obj, "input")),
        ("ALIAS", _read(obj, "alias")),
        ("TEXT", _text(obj)),
        ("NOTES", _notes(obj)),
        ("OPTION", _read(option, "display") if option else ""),
        ("OPTION_ALIAS", _read(option, "alias") if option else ""),
        ("OPTION_ID", _read(option, "xmlid") if option else ""),
        ("ACTIVE_COST", str(round_up(_read(obj, "active_cost", 0) or 0))),
        ("COST", str(round_up(_read(obj, "real_cost", 0) or 0))),
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
    return bool((_read(obj, "name")).strip())


def _is_list(obj) -> bool:
    from kirby_cost.objects.list import List
    return isinstance(obj, List)


def _is_named_list(obj) -> bool:
    """IS_LIST: a List container that has an alias (HTMLWriter.java:4108)."""
    return _is_list(obj) and bool((_read(obj, "alias")).strip())


def _is_separator(obj) -> bool:
    """IS_SEPARATOR: a List container with a BLANK alias -- a bare rule
    between rows rather than a named group (HTMLWriter.java:4142)."""
    return _is_list(obj) and not (_read(obj, "alias")).strip()


def _text(obj) -> str:
    """TEXT is the nameless column-2 output, plus the parent list's suffix
    when the object hangs off one (HTMLWriter.java:4237-4240)."""
    text = _read(obj, "nameless_column2_output")
    parent = getattr(obj, "parent", None)
    if parent is not None and hasattr(parent, "column2_suffix"):
        text += parent.column2_suffix(obj)
    return text


def _notes(obj) -> str:
    """HTMLWriter.java:4284-4291. Notes when the object asks for them,
    otherwise a quantity marker, otherwise nothing."""
    if getattr(obj, "include_notes_in_printout", False):
        return _read(obj, "output_notes") or _read(obj, "notes")
    quantity = getattr(obj, "quantity", 1) or 1
    if quantity > 1:
        return f"(x{quantity} number of items)"
    return ""


def _list_item(block: str, obj) -> str:
    """IS_LIST_ITEM / IFLIST and their LISTPREFIX (HTMLWriter.java:4174-4210).

    An object hanging off a List or an Enhancer keeps the block and gets the
    parent's column-2 prefix; anything else has it stripped. The enhancer
    takes precedence over the parent list, which is Java's order.
    """
    parent = getattr(obj, "enhancer_applied", None) or getattr(obj, "parent", None)
    for tag in ("IS_LIST_ITEM", "IFLIST"):
        open_tag, close_tag = f"<!--{tag}-->", f"<!--/{tag}-->"
        while True:
            body = get_long_value(open_tag, close_tag, block)
            if body is None:
                break
            if parent is not None and hasattr(parent, "column2_prefix"):
                body = swap_value("<!--LISTPREFIX-->",
                                  parent.column2_prefix(obj), body)
                block = swap_long_value(open_tag, close_tag, body, block)
            else:
                block = swap_long_value(open_tag, close_tag, "", block)
    return _conditional(block, "IS_NOT_LIST_ITEM", parent is None)


#: The nine type filters getGeneralString applies, in Java's order
#: (HTMLWriter.java:3982-3990). Only IF_SENSORY appears in the shipped 6E
#: template, but they are one mechanism and porting one of nine would be an
#: arbitrary line to draw.
TYPE_FILTERS = ("ATTACK", "DEFENSE", "MOVEMENT", "MENTAL", "SPECIAL",
                "ADJUSTMENT", "SENSORY", "SENSEAFFECTING", "BODYAFFECTING")


def _filter_by_type(block: str, obj) -> str:
    """``filterByType`` (HTMLWriter.java:212-227), applied for each type.

    Keeps `<!--IF_X-->…<!--/IF_X-->` when the object's TYPES contain X and
    strips it otherwise. The types come from the template, so this asks the
    object what it is rather than guessing from its xmlid.
    """
    types = {str(x).upper() for x in (getattr(obj, "types", ()) or ())}
    for name in TYPE_FILTERS:
        block = _conditional(block, f"IF_{name}", name in types)
    return block
