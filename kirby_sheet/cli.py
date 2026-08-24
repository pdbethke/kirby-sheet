"""The `kirby-sheet` command line.

    kirby-sheet CHAR.hdc --json [-o FILE]

One format flag exists today; `--text`, `--html` and `--template` are the
same shape (a Sheet -> str function keyed by flag name), so adding one is an
entry in `_FORMATS` and a line in the mutually exclusive group -- not a
restructure. None of them are stubbed in here ahead of their own backends
existing: a flag that parses and then says "not implemented" advertises a
feature this package does not have yet.

`--hdc` is not one of those: it does not render a Sheet at all. It runs
`LoadedHero -> write_hdc` (`copy_hdc` in `build.py`, the only module here
permitted to import kirby-cost) and writes a binary UTF-16 `.hdc` document,
so it is handled separately from `_FORMATS` and requires `-o` -- there is no
useful way to write that document to a terminal or down a text pipe.

`--pdf` is handled the same way as `--hdc`, for the same reason: `to_pdf`
returns `bytes`, not `str` -- `_FORMATS` is typed `Callable[[Sheet], str]`
-- and a PDF written down a terminal or a text pipe is as useless as a
`.hdc` file would be. It requires `-o` for that reason too.

`--inspect` is not one of those either: it takes a TEMPLATE path as its
flag value AND a character positionally. It reports which tokens a `.hde`
template uses and which the renderer resolves (`kirby_sheet.inspect`).
The character is not optional -- rendering requires one, and the answer
depends on it, because a token inside a block the character does not
trigger is reported resolved.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from kirby_sheet.build import copy_hdc, hero_from_hdc, sheet_from_hdc
from kirby_sheet.formats.as_html import to_html
from kirby_sheet.formats.as_json import to_json
from kirby_sheet.formats.as_pdf import to_pdf
from kirby_sheet.formats.as_text import to_text
from kirby_sheet.inspect import describe, inspect_template
from kirby_sheet.sheet import Sheet
from kirby_sheet.template import Template

#: format flag name -> renderer. The CLI's only knowledge of what backends
#: exist; everything else about a format lives in its own module.
_FORMATS: dict[str, Callable[[Sheet], str]] = {
    "json": to_json,
    "text": to_text,
    "html": to_html,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kirby-sheet",
        description="Render a HERO Designer character sheet.",
    )
    # Not required here at the positional level: --inspect takes a template
    # instead of a character, so there is nothing to require a character
    # for in that mode. Its absence is enforced by hand in main() for every
    # other mode.
    parser.add_argument("character", nargs="?",
                         help="path to a .hdc character file")
    formats = parser.add_mutually_exclusive_group()
    for name in _FORMATS:
        formats.add_argument(f"--{name}", action="store_true",
                              help=f"write the sheet as {name.upper()}")
    formats.add_argument("--hdc", action="store_true",
                          help="write a HERO Designer .hdc file (requires -o)")
    formats.add_argument("--pdf", action="store_true",
                          help="write the sheet as a PDF (requires -o)")
    formats.add_argument("--inspect", metavar="TEMPLATE",
                          help="report which tokens TEMPLATE (a .hde file) "
                               "uses and which the renderer resolves for the "
                               "given character")
    parser.add_argument("-o", "--output", metavar="FILE",
                         help="write to FILE instead of stdout (UTF-8)")
    return parser


def _run_inspect(args: argparse.Namespace) -> int:
    """`--inspect TEMPLATE CHARACTER`: which of TEMPLATE's tokens resolve.

    A character is REQUIRED. Rendering needs one, and the answer depends on
    it: a token inside a block the character does not trigger is reported
    resolved because the block was stripped. See `kirby_sheet/inspect.py`.
    """
    template_path = Path(args.inspect)
    if not template_path.is_file():
        print(f"kirby-sheet: template file not found: {template_path}",
              file=sys.stderr)
        return 1

    try:
        template = Template.from_path(template_path)
    except Exception as exc:
        print(f"kirby-sheet: {exc}", file=sys.stderr)
        return 1

    character_path = Path(args.character)
    if not character_path.is_file():
        print(f"kirby-sheet: character file not found: {character_path}",
              file=sys.stderr)
        return 1
    document = describe(inspect_template(template, hero_from_hdc(character_path)))

    if args.output:
        Path(args.output).write_text(document, encoding="utf-8")
    else:
        sys.stdout.write(document)
        if not document.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)

        if args.inspect:
            if not args.character:
                parser.error("--inspect needs a character as well as a "
                             "template: which tokens resolve depends on the "
                             "character being rendered")
            return _run_inspect(args)

        if not args.character:
            parser.error("the following arguments are required: character")

        if not (args.hdc or args.pdf or any(getattr(args, name) for name in _FORMATS)):
            parser.error("one of the arguments " +
                         " ".join(f"--{name}" for name in _FORMATS) +
                         " --hdc --pdf --inspect is required")
    except SystemExit as exc:
        # argparse has already written usage/the error to stderr (whether
        # from parse_args itself or from parser.error() above); convert its
        # exit into a return so main() never raises for ordinary bad usage.
        return exc.code if isinstance(exc.code, int) else 2

    character_path = Path(args.character)
    if not character_path.is_file():
        print(f"kirby-sheet: character file not found: {character_path}",
              file=sys.stderr)
        return 1

    if args.hdc:
        if not args.output:
            print("kirby-sheet: --hdc requires -o FILE "
                  "(a .hdc file is UTF-16 binary; writing it to stdout is "
                  "not useful)", file=sys.stderr)
            return 2
        try:
            # copy_hdc is the only function that touches kirby-cost here,
            # same as sheet_from_hdc below -- it does not build a Sheet at
            # all, so it is called on its own path rather than through
            # _FORMATS.
            copy_hdc(character_path, args.output)
        except Exception as exc:
            print(f"kirby-sheet: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.pdf:
        if not args.output:
            print("kirby-sheet: --pdf requires -o FILE "
                  "(a PDF is binary; writing it to stdout is not useful)",
                  file=sys.stderr)
            return 2
        try:
            # sheet_from_hdc is the only function that touches kirby-cost,
            # same as the _FORMATS path below -- to_pdf itself never does.
            sheet = sheet_from_hdc(character_path)
            document = to_pdf(sheet)
        except Exception as exc:
            print(f"kirby-sheet: {exc}", file=sys.stderr)
            return 1
        Path(args.output).write_bytes(document)
        return 0

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
