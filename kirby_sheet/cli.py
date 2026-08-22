"""The `kirby-sheet` command line.

    kirby-sheet CHAR.hdc --json [-o FILE]

One format flag exists today; `--text`, `--html`, `--hdc` and `--template`
are the same shape (a Sheet -> str function keyed by flag name), so adding
one is an entry in `_FORMATS` and a line in the mutually exclusive group --
not a restructure. None of them are stubbed in here ahead of their own
backends existing: a flag that parses and then says "not implemented"
advertises a feature this package does not have yet.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from kirby_sheet.build import sheet_from_hdc
from kirby_sheet.formats.as_json import to_json
from kirby_sheet.sheet import Sheet

#: format flag name -> renderer. The CLI's only knowledge of what backends
#: exist; everything else about a format lives in its own module.
_FORMATS: dict[str, Callable[[Sheet], str]] = {
    "json": to_json,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kirby-sheet",
        description="Render a HERO Designer character sheet.",
    )
    parser.add_argument("character", help="path to a .hdc character file")
    formats = parser.add_mutually_exclusive_group(required=True)
    for name in _FORMATS:
        formats.add_argument(f"--{name}", action="store_true",
                              help=f"write the sheet as {name.upper()}")
    parser.add_argument("-o", "--output", metavar="FILE",
                         help="write to FILE instead of stdout (UTF-8)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse has already written usage/the error to stderr; convert its
        # exit into a return so main() never raises for ordinary bad usage.
        return exc.code if isinstance(exc.code, int) else 2

    character_path = Path(args.character)
    if not character_path.is_file():
        print(f"kirby-sheet: character file not found: {character_path}",
              file=sys.stderr)
        return 1

    format_name = next(name for name in _FORMATS if getattr(args, name))
    render = _FORMATS[format_name]

    try:
        # sheet_from_hdc is the only function that touches kirby-cost. It is
        # called here rather than at module scope so that a bare `--help`
        # never pays for (or requires) a template load.
        sheet = sheet_from_hdc(character_path)
    except Exception as exc:
        print(f"kirby-sheet: {exc}", file=sys.stderr)
        return 1

    document = render(sheet)

    if args.output:
        Path(args.output).write_text(document, encoding="utf-8")
    else:
        sys.stdout.write(document)
        if not document.endswith("\n"):
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
