"""Reporting which `.hde` tokens a template uses and which the renderer
actually resolves.

**Read and report; never write.** Authoring `.hde` templates would edge
toward replacing Hero Designer's own export tooling, which this project
deliberately does not do -- see `kirby_sheet/template.py` and the project
brief. This module only inspects.

**What "resolved" means.** A token is "resolved" if it does NOT survive
rendering -- whichever mechanism made it disappear. Substitution
(`swap_value`) is one such mechanism; so is a paired block being stripped
whole because it names a token `render()` does not implement (see below).
For a person building a worklist, both cases mean the same thing: nothing
to do. A token is only worklist-worthy if it is still sitting in the
rendered output, unresolved.

**The report is CHARACTER-DEPENDENT, and that is why it names the character.**
`render()` needs a character, so inspection needs one too. A token sitting
inside a block the character does not trigger -- `<!--IF_FLIGHT-->` for
someone with no Flight -- is reported RESOLVED, because the block was
stripped whole and the token does not survive rendering. That is exactly this
module's definition of "resolved" (see below) and it is deliberate. But it
means the report describes THIS character's render rather than the backend's
capabilities, and a reader who does not know that would draw a false
conclusion from a short unresolved list. `describe()` therefore leads with the
character's name: a report that depends on a character must say which one.

**How it is measured.** `render()` is called on the template with the given
character and a set of harmless sentinel values, and the token set before is
compared against the token set after. Whatever disappeared is "resolved" by the definition
above -- there is no second, hand-maintained list of "the tokens we
support" to drift out of sync with `render.py` the day someone adds one.
See `tests/test_inspect.py::test_tracks_the_renderer_not_a_hardcoded_list`
for the guard that proves this module actually measures rather than lists.

**Stripping counts as resolved, and that is a deliberate choice, not a
bug.** `render()`'s `swap_all_long_values` strips a paired block such as
`TEMPLATE_NAME` or `TEMPLATE_DESCRIPTION` as a whole unit. If that block's
own text happens to *name* another token -- e.g. prose inside
`TEMPLATE_DESCRIPTION` that says "uses <!--CHARACTER_NAME-->" -- that named
token vanishes along with the block, and is reported resolved even though
it was never substituted. See
`tests/test_inspect.py::test_a_token_named_only_inside_a_stripped_block_is_reported_resolved`,
which pins this on purpose: whatever removed the token from the rendered
output, it does not survive rendering, so it needs no work either way.

**`FILE_EXTENSION` never appears in `tokens_used` at all.**
`Template.from_path` (see `kirby_sheet/template.py`) reads and REMOVES the
`FILE_EXTENSION` block before `inspect_template` ever sees `template.text`
-- mirroring Java's `HTMLWriter.getFileExtensions()` (HTMLWriter.java:3901),
which consumes and removes that block in its constructor. So a template
loaded via `Template.from_path` reports one fewer distinct token name than
its raw file text contains, by design: `inspect_template` describes
`template.text`, and `FILE_EXTENSION` is no longer part of it.

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
    """`tokens_used` is every distinct token NAME `template.text` contains
    (an opener and its closer count as one), in first-appearance order --
    note that `FILE_EXTENSION` is never among them if the template came from
    `Template.from_path`; see the module docstring. `tokens_resolved` and
    `tokens_unresolved` partition it: every used token is in exactly one of
    the two, in that same order. "Resolved" means the token does not survive
    rendering -- by substitution, or because it sat inside a block that was
    stripped whole; see the module docstring."""

    tokens_used: tuple[str, ...]
    tokens_resolved: tuple[str, ...]
    tokens_unresolved: tuple[str, ...]
    character_name: str = ""


def inspect_template(template: Template, hero) -> TemplateReport:
    """Measure which of `template`'s tokens do not survive `render()` for
    `hero` -- substituted or stripped, either counts as resolved.

    See the module docstring for why "resolved" is defined that way, and why
    the answer depends on which character is passed.
    """
    used = _tokens_in_order(template.text)
    rendered = render(template, hero, **_SENTINELS)
    survived = set(_tokens_in_order(rendered))
    resolved = tuple(token for token in used if token not in survived)
    unresolved = tuple(token for token in used if token in survived)
    return TemplateReport(tokens_used=used, tokens_resolved=resolved,
                          tokens_unresolved=unresolved,
                          character_name=getattr(hero, "name", "") or "")


def describe(report: TemplateReport) -> str:
    """A human-readable summary: the character, the counts, then the
    unresolved worklist.

    The character is named FIRST because the counts mean nothing without it --
    see the module docstring.
    """
    lines = [
        f"measured against: {report.character_name or '(unnamed character)'}",
        f"{len(report.tokens_used)} tokens used, "
        f"{len(report.tokens_resolved)} resolved, "
        f"{len(report.tokens_unresolved)} unresolved",
    ]
    if report.tokens_unresolved:
        lines.append("Unresolved:")
        lines.extend(f"  {token}" for token in report.tokens_unresolved)
    return "\n".join(lines)
