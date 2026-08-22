"""The one place this package parses HTML.

kirby-cost's display strings carry Hero Designer's markup, because HD renders
to HTML. Text output has to strip it — but only text output: the .hde backend
renders INTO HTML, where those tags are correct, so stripping upstream in the
view model would break byte-fidelity against HD.

bs4 rather than a regex: it does not break on nested or malformed markup and
decodes entities for free. Measured across 655 characters, the corpus contains
only <i> and <b> and no entities — so this is insurance, deliberately bought.
"""
from __future__ import annotations

from bs4 import BeautifulSoup


def plain_text(markup: str) -> str:
    """HD's markup as printable text, with its whitespace intact."""
    if not markup:
        return ""
    return BeautifulSoup(markup, "html.parser").get_text()
