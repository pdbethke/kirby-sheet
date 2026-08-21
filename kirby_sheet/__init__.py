"""Render a HERO Designer character through HD's own .hde export templates.

Hero Designer has no plain-text exporter. `util/HTMLWriter.java` is the only
writer it has, and it substitutes ``<!--TOKEN-->`` markers into an export
template. This package reproduces that, byte for byte, so a sheet rendered
here is the sheet HD would have rendered.

It ships no Hero Games content. Point it at a template you already have.
"""

__version__ = "0.1.0"
