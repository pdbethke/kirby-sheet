"""The four string primitives com.hero.util.HTMLWriter is built from.

Everything HD does with an export template reduces to these. Repetition is not
a fifth primitive: a list is rendered by extracting its block once with
`get_long_value`, rendering that block per item, joining, and putting the
accumulation back with `swap_long_value`.

Several behaviours here look wrong and are faithful. Each is marked. The point
of this package is to produce the bytes HD produces, and HD's bugs are part of
its output.
"""
from __future__ import annotations

#: A `swap_value` whose replacement contains its own tag never terminates.
#: Java has the same hole and hangs; see `swap_value`.
_MAX_SUBSTITUTIONS = 100_000


class RunawaySubstitution(RuntimeError):
    """A substitution that would never terminate.

    Java loops forever when a value contains the tag it replaces. A hang
    produces no output to be byte-identical with, so this is one place the
    port deliberately differs: it raises, naming the tag, instead of spinning.
    """


def swap_value(tag: str | None, value: str | None, html: str | None) -> str | None:
    """``HTMLWriter.swapValue`` (HTMLWriter.java:5636).

    Case-insensitive, and replaces EVERY occurrence — it is a `while` loop,
    unlike `swap_long_value` below, which replaces only the first. Both are
    load-bearing.
    """
    if value is None:
        value = ""
    if tag is None or html is None:
        return html
    upper_tag = tag.upper()
    for _ in range(_MAX_SUBSTITUTIONS):
        index = html.upper().find(upper_tag)
        if index < 0:
            return html
        html = html[:index] + value + html[index + len(tag):]
    raise RunawaySubstitution(
        f"{tag!r} still present after {_MAX_SUBSTITUTIONS} substitutions — "
        f"the replacement almost certainly contains the tag")


def get_long_value(tag: str, end_tag: str, template: str) -> str | None:
    """``HTMLWriter.getLongValue`` (HTMLWriter.java:4537).

    The text between a paired tag and its closer, or None when either is
    missing. Note the end index must be strictly positive, not merely found:
    Java's guard is `> 0`, so a closing tag at position zero reads as absent.
    """
    upper = template.upper()
    start = upper.find(tag.upper())
    if start < 0:
        return None
    end = upper.find(end_tag.upper(), start)
    if end <= 0:
        return None
    return template[start + len(tag):end]


def _swap_block_once(tag: str, end_tag: str, value: str, html: str) -> str | None:
    """One block replacement, or None when the guard does not fire.

    The guard is Java's, transcribed rather than tidied. It tests the RAW
    `end_tag` against upper-cased html while the index computed below
    upper-cases it — so a lower-case closing tag fails the guard even though
    the body would have found it. See HTMLWriter.java:5410-5416.
    """
    upper = html.upper()
    start = upper.find(tag.upper())
    if start < 0:
        return None
    if upper.find(end_tag, start + len(tag)) <= 0:   # NOT end_tag.upper()
        return None
    end = upper.find(end_tag.upper(), start + len(tag))
    if end < 0:
        return None
    end += len(end_tag)
    return html[:start] + value + html[end:]


def swap_long_value(tag: str, end_tag: str, value: str | None, html: str) -> str:
    """``HTMLWriter.swapLongValue`` (HTMLWriter.java:5405).

    Replaces the FIRST block only, closer included.
    """
    if value is None:
        value = ""
    result = _swap_block_once(tag, end_tag, value, html)
    return html if result is None else result


def swap_all_long_values(tag: str, end_tag: str, value: str | None, html: str) -> str:
    """``HTMLWriter.swapAllLongValues`` (HTMLWriter.java:5378).

    As `swap_long_value`, but every block rather than the first.
    """
    if value is None:
        value = ""
    for _ in range(_MAX_SUBSTITUTIONS):
        result = _swap_block_once(tag, end_tag, value, html)
        if result is None:
            return html
        html = result
    raise RunawaySubstitution(
        f"{tag!r}..{end_tag!r} still present after {_MAX_SUBSTITUTIONS} "
        f"replacements — the replacement almost certainly contains the block")
