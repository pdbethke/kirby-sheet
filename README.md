# kirby-sheet

Render a HERO Designer character through HD's own `.hde` export templates —
byte for byte.

Hero Designer has no plain-text exporter. `HTMLWriter` is the only writer it
has, and it substitutes `<!--TOKEN-->` markers into an export template. This
reproduces that, so a sheet rendered here is the sheet HD would have rendered.

**Status: Milestone 1.** The template engine is complete and gated against HD
itself. Character data is not read yet — that is Milestone 2. It is not
usable as a character sheet renderer today.

## Ships no Hero Games content

No templates, no rules text, no character files. Point it at a `.hde` you
already have.

## Development

    python -m venv venv && source venv/bin/activate
    pip install -e ../kirby-cost          # ALWAYS, and first
    pip install -e ".[dev]"
    python -m pytest tests/ -q

**Install the sibling editable, and do it first.** `kirby-cost` is published,
so `pip` will happily resolve the dependency pin against PyPI and give you a
release that is behind the checkout next door — same version number, different
code. That is not a hypothetical: this package was built for a day against a
stale 0.2.2 and read a character's STR as 5 instead of 15 before anyone
noticed. Nothing fails loudly when it happens, because a stale dependency
installs perfectly.

Tests that need Hero Designer skip when it is absent:

| Variable | What it names |
|---|---|
| `KIRBY_SHEET_HDC` | a `.hdc` character |
| `KIRBY_SHEET_ORACLE` | `hd6cli.sh` from kirby-hd-oracle |

## Licence

PolyForm Noncommercial 1.0.0. Not affiliated with or endorsed by Hero Games.
