"""``HTMLWriter.generateOutput`` — the call order, and nothing else.

Ported from HTMLWriter.java:290 onward, in that order. **Order matters and is
not an accident of transcription:** one substitution's output can contain
another's marker, so this follows generateOutput line by line rather than
applying a dict or looping over a token table. Every region lives in its own
module; this file only says when each runs.

The five volatile values are parameters rather than being read here.
TIMESTAMP and EXPORT_ID come off the wall clock, CHARACTER_SAVE_TIMESTAMP off
the save file's mtime, CHARACTER_FILE off its path. The byte-fidelity gate has
to pin them to compare anything at all, and a function that reads the clock
itself cannot be pinned.
"""
from __future__ import annotations

from kirby_sheet.engine import swap_all_long_values, swap_value
from kirby_sheet.hde import characteristics, derived, movement, scalars
from kirby_sheet.template import Template


def generate(template: Template, hero, *, app_version: str, timestamp: str,
             export_id: str, save_timestamp: str, character_file: str) -> str:
    """Render `template` for `hero`.

    `hero` is a kirby-cost ``LoadedHero``. It is read directly rather than
    through a ``Sheet``: generateOutput reaches deep into the character
    (per-object option ids, levels, adders; characteristic-specific derived
    values), and every intermediary is a place to re-derive a value the
    engine already owns.
    """
    text = template.text
    # The two documentation blocks go first and are removed with
    # swapAllLongValues -- every occurrence, not just the first -- because a
    # template may carry more than one. (HTMLWriter.java:293-297)
    text = swap_all_long_values("<!--TEMPLATE_NAME-->", "<!--/TEMPLATE_NAME-->", "", text)
    text = swap_all_long_values("<!--TEMPLATE_DESCRIPTION-->",
                                "<!--/TEMPLATE_DESCRIPTION-->", "", text)
    text = swap_value("<!--APP_VERSION-->", app_version, text)
    text = swap_value("<!--TIMESTAMP-->", timestamp, text)
    text = swap_value("<!--EXPORT_ID-->", export_id, text)
    text = swap_value("<!--CHARACTER_SAVE_TIMESTAMP-->", save_timestamp, text)
    text = swap_value("<!--CHARACTER_FILE-->", character_file, text)
    text = scalars.apply(text, hero)
    text = characteristics.apply(text, hero)
    text = derived.apply(text, hero)
    text = movement.apply(text, hero)
    return text
