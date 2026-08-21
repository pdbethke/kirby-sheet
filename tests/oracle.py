"""Running HD's own exporter, and normalising what neither side can pin.

The oracle is `hd6cli.sh --export <template.hde> <char.hdc>`, added to
kirby-hd-oracle at 7e384ae. It runs the real HTMLWriter out of the headless
jar, so what comes back is what Hero Designer would have written.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from tests.corpus import oracle_path

#: Values neither side can agree on, blanked in BOTH outputs before comparing.
#: Two come off the wall clock, one off a file's mtime, one off its path.
#: Everything else is expected to match byte for byte.
_VOLATILE = (
    re.compile(r"\d{4}\d{2}\d{2}\d{6}"),                      # EXPORT_ID
    re.compile(r"[A-Z][a-z]{2}, \d{1,2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2}"),
)


def normalise(text: str) -> str:
    """Blank the environment-dependent values. Nothing else is touched."""
    for pattern in _VOLATILE:
        text = pattern.sub("<PINNED>", text)
    return text


def oracle_export(template: Path, character: Path) -> str | None:
    """HD's own output, or None when the oracle is not configured."""
    cli = oracle_path()
    if cli is None:
        return None
    result = subprocess.run(
        [str(cli), "--export", str(template), str(character)],
        capture_output=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"oracle failed ({result.returncode}): "
            f"{result.stderr.decode('utf-8', 'replace')[:400]}")
    return result.stdout.decode("utf-8", errors="replace")
