"""Reporting which `.hde` tokens a template uses and which the renderer
actually resolves.

**Read and report; never write.** Authoring `.hde` templates would edge
toward replacing Hero Designer's own export tooling, which this project
deliberately does not do -- see `kirby_sheet/template.py` and the project
brief. This module only inspects.

**How "resolved" is determined.** `render()` is called on the template with
a set of harmless sentinel values, and the token set before is compared
against the token set after. Whatever disappeared is what the renderer
handles -- there is no second, hand-maintained list of "the tokens we
support" to drift out of sync with `render.py` the day someone adds one.
See `tests/test_inspect.py::test_tracks_the_renderer_not_a_hardcoded_list`
for the guard that proves this module actually measures rather than lists.

A token's identity is its bare tag NAME -- upper-cased, with any leading
`/` stripped -- not the raw `<!--TAG-->` marker text. A paired block such
as `TEMPLATE_NAME` (an opener and a matching closer) is therefore ONE
token, not two: `render()` strips the whole block as a single unit
(`swap_all_long_values`), and a person's worklist should list the thing
once, the way HD's own "343 tokens" vocabulary counts it -- by name, not
by marker occurrence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from kirby_sheet.render import render
from kirby_sheet.template import Template

#: One `<!--TAG-->` or `<!--/TAG-->` marker; group 1 is the bare tag name.
_TOKEN = re.compile(r"<!--/?([A-Za-z0-9_]+)-->")

#: Sentinel values passed to render() purely to exercise its substitutions.
#: Distinct and marker-free, so none of them can be mistaken for a token or
#: mask one being left behind.
_SENTINELS = dict(
    app_version="SENTINEL_APP_VERSION",
    timestamp="SENTINEL_TIMESTAMP",
    export_id="SENTINEL_EXPORT_ID",
    save_timestamp="SENTINEL_SAVE_TIMESTAMP",
    character_file="SENTINEL_CHARACTER_FILE",
)


def _tokens_in_order(text: str) -> tuple[str, ...]:
    """Distinct token NAMES in `text`, in first-appearance order.

    Upper-cased so that `<!--app_version-->` and `<!--APP_VERSION-->` are
    the same token -- `swap_value`/`swap_long_value` match case-insensitively
    (HTMLWriter.java), so identity here follows that, not raw spelling.
    """
    seen: dict[str, None] = {}
    for match in _TOKEN.finditer(text):
        seen.setdefault(match.group(1).upper(), None)
    return tuple(seen)


@dataclass(frozen=True)
class TemplateReport:
    """`tokens_used` is every distinct token NAME the template contains (an
    opener and its closer count as one), in first-appearance order.
    `tokens_resolved` and `tokens_unresolved` partition it: every used token
    is in exactly one of the two, in that same order."""

    tokens_used: tuple[str, ...]
    tokens_resolved: tuple[str, ...]
    tokens_unresolved: tuple[str, ...]


def inspect_template(template: Template) -> TemplateReport:
    """Measure which of `template`'s tokens `render()` actually resolves."""
    used = _tokens_in_order(template.text)
    rendered = render(template, **_SENTINELS)
    survived = set(_tokens_in_order(rendered))
    resolved = tuple(token for token in used if token not in survived)
    unresolved = tuple(token for token in used if token in survived)
    return TemplateReport(tokens_used=used, tokens_resolved=resolved,
                           tokens_unresolved=unresolved)


def describe(report: TemplateReport) -> str:
    """A human-readable summary: the counts, then the unresolved worklist."""
    lines = [
        f"{len(report.tokens_used)} tokens used, "
        f"{len(report.tokens_resolved)} resolved, "
        f"{len(report.tokens_unresolved)} unresolved",
    ]
    if report.tokens_unresolved:
        lines.append("Unresolved:")
        lines.extend(f"  {token}" for token in report.tokens_unresolved)
    return "\n".join(lines)
