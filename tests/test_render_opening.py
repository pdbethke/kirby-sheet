"""generateOutput's fixed opening — the part before any character data."""
from kirby_sheet.render import render
from tests.stub_hero import stub_hero
from kirby_sheet.template import Template

PINNED = dict(app_version="headless-fork", timestamp="TS", export_id="EID",
              save_timestamp="STS", character_file="CF")


#: These templates carry only opening-region tokens, so nothing the later
#: phases substitute appears in them -- but the whole pipeline still runs, so
#: a hero-shaped object is required. Distinct stub values throughout; see
#: tests/stub_hero.py.
NO_HERO = stub_hero()


def _render(text: str) -> str:
    return render(Template(text=text), NO_HERO, **PINNED)


def test_template_name_block_is_removed():
    assert _render("a<!--TEMPLATE_NAME-->Sheet<!--/TEMPLATE_NAME-->b") == "ab"


def test_template_description_block_is_removed():
    assert _render("a<!--TEMPLATE_DESCRIPTION-->words<!--/TEMPLATE_DESCRIPTION-->b") == "ab"


def test_every_template_name_block_is_removed():
    """swapAllLongValues, not swapLongValue (HTMLWriter.java:293)."""
    text = "<!--TEMPLATE_NAME-->1<!--/TEMPLATE_NAME-->x<!--TEMPLATE_NAME-->2<!--/TEMPLATE_NAME-->"
    assert _render(text) == "x"


def test_the_four_volatile_tokens_are_filled():
    text = ("<!--APP_VERSION-->|<!--TIMESTAMP-->|<!--EXPORT_ID-->|"
            "<!--CHARACTER_SAVE_TIMESTAMP-->|<!--CHARACTER_FILE-->")
    assert _render(text) == "headless-fork|TS|EID|STS|CF"


def test_unknown_tokens_are_left_alone():
    """Milestone 2 fills these in. Until then they must survive untouched, so
    the gate reports them as diffs rather than silently blanking them."""
    assert _render("<!--STR-->") == "<!--STR-->"


def test_the_substitution_order_is_load_bearing():
    """The order in render() is HD's order (HTMLWriter.java:290-313), and it
    is observable: a value that itself contains a later token's marker gets
    that marker substituted by the later call.

    APP_VERSION is applied BEFORE TIMESTAMP, so an app_version of
    "<!--TIMESTAMP-->" is injected first and then replaced, giving "TS|TS".
    Reverse the two calls and the injected marker arrives too late to be
    replaced, leaving "<!--TIMESTAMP-->|TS". Every other test here uses inert
    values and passes under any permutation.
    """
    out = render(
        Template(text="<!--APP_VERSION-->|<!--TIMESTAMP-->"),
        NO_HERO,
        app_version="<!--TIMESTAMP-->",
        timestamp="TS",
        export_id="EID",
        save_timestamp="STS",
        character_file="CF",
    )
    assert out == "TS|TS"
