"""Rendering a template.

The public entry point. The body lives in `kirby_sheet.hde`, one module per
region of ``HTMLWriter.generateOutput``; see `kirby_sheet/hde/spine.py` for
the call order and why that order is load-bearing.
"""
from __future__ import annotations

from kirby_sheet.hde import spine
from kirby_sheet.template import Template


def render(template: Template, hero, *, app_version: str, timestamp: str,
           export_id: str, save_timestamp: str, character_file: str) -> str:
    """``HTMLWriter.generateOutput`` (HTMLWriter.java:290).

    `hero` is a kirby-cost ``LoadedHero``, taken positionally as Java takes it.
    """
    return spine.generate(template, hero, app_version=app_version,
                          timestamp=timestamp, export_id=export_id,
                          save_timestamp=save_timestamp,
                          character_file=character_file)
