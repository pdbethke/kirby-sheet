"""The `.hde` backend: HTMLWriter.generateOutput, ported.

One module per region of generateOutput, called from `spine.py` in Java's own
order. This package and `build.py` are the only modules in kirby-sheet
permitted to import kirby-cost; see tests/test_import_boundary.py.
"""
