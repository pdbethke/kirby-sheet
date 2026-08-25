"""Render a HERO Designer character through HD's own .hde export templates.

Hero Designer has no plain-text exporter. `util/HTMLWriter.java` is the only
writer it has, and it substitutes ``<!--TOKEN-->`` markers into an export
template. This package reproduces that, byte for byte, so a sheet rendered
here is the sheet HD would have rendered.

It ships no Hero Games content. Point it at a template you already have.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    #: Read from the installed distribution rather than restated here.
    #: A hardcoded literal drifts, and this one did: it still said "0.1.0"
    #: when pyproject said 0.2.0 and the wheel published to PyPI as 0.2.0, so
    #: anything reading kirby_sheet.__version__ got the wrong answer off a
    #: correctly-built package. kirby-cost and kirby-combat already derive it
    #: for exactly this reason.
    __version__ = _version("kirby-sheet")
except PackageNotFoundError:  # not installed (e.g. a source checkout on sys.path)
    __version__ = "0.0.0+unknown"
