"""An .hde export template, loaded the way HTMLWriter loads one."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from kirby_sheet.engine import get_long_value, swap_long_value

_OPEN = "<!--FILE_EXTENSION-->"
_CLOSE = "<!--/FILE_EXTENSION-->"


@dataclass
class Template:
    """The template text, after the load-time edits Java makes to it."""

    text: str
    file_extensions: list[str] = field(default_factory=list)

    @classmethod
    def from_path(cls, path: str | os.PathLike) -> "Template":
        """Read a .hde exactly as ``new HTMLWriter(File)`` does.

        Two things happen at load time and both matter:

        The charset is the platform default (HTMLWriter.java:207,
        ``new String(data)`` with no encoding). On the oracle that is UTF-8,
        and the shipped templates are ISO-8859 — so their non-ASCII bytes are
        INVALID and Java replaces them with U+FFFD. Decoding as latin-1 here
        would be correct and would fail the byte diff, so this reproduces the
        mangling instead. It follows that fidelity is against HD as
        configured: real HD on Windows would use windows-1252 and render
        those bytes properly.

        Then ``getFileExtensions()`` (HTMLWriter.java:3901) collects every
        FILE_EXTENSION block and REMOVES it from the template. It is called
        from the constructor, so no caller ever sees an unstripped template.
        """
        raw = Path(path).read_bytes().decode("utf-8", errors="replace")
        extensions: list[str] = []
        while True:
            found = get_long_value(_OPEN, _CLOSE, raw)
            if found is None:
                break
            extensions.append(found.strip().upper())
            raw = swap_long_value(_OPEN, _CLOSE, "", raw)
        return cls(text=raw, file_extensions=extensions)
