"""Rendering a template. Milestone 1: the fixed opening only."""
from __future__ import annotations

from kirby_sheet.engine import swap_all_long_values, swap_value
from kirby_sheet.template import Template


def render(template: Template, *, app_version: str, timestamp: str,
           export_id: str, save_timestamp: str, character_file: str) -> str:
    """``HTMLWriter.generateOutput`` up to the point it reads the character.

    Ported from HTMLWriter.java:290-313, in that order. Order matters here in
    general: one substitution's output can contain another's marker, which is
    why this follows generateOutput line by line rather than applying a dict.

    The two documentation blocks go first and are removed with
    swapAllLongValues — every occurrence, not just the first — because a
    template may carry more than one.

    The five values are parameters rather than being read here. Four of them
    are the environment-dependent tokens the design names: TIMESTAMP and
    EXPORT_ID come off the wall clock, CHARACTER_SAVE_TIMESTAMP off the save
    file's mtime, CHARACTER_FILE off its path. The byte-fidelity gate has to
    pin them to compare anything at all, and a function that reads the clock
    itself cannot be pinned.
    """
    text = template.text
    text = swap_all_long_values("<!--TEMPLATE_NAME-->", "<!--/TEMPLATE_NAME-->", "", text)
    text = swap_all_long_values("<!--TEMPLATE_DESCRIPTION-->",
                                "<!--/TEMPLATE_DESCRIPTION-->", "", text)
    text = swap_value("<!--APP_VERSION-->", app_version, text)
    text = swap_value("<!--TIMESTAMP-->", timestamp, text)
    text = swap_value("<!--EXPORT_ID-->", export_id, text)
    text = swap_value("<!--CHARACTER_SAVE_TIMESTAMP-->", save_timestamp, text)
    text = swap_value("<!--CHARACTER_FILE-->", character_file, text)
    return text
