"""generateOutput's fixed opening — the part before any character data."""
from kirby_sheet.render import render
from kirby_sheet.template import Template

PINNED = dict(app_version="headless-fork", timestamp="TS", export_id="EID",
              save_timestamp="STS", character_file="CF")


def _render(text: str) -> str:
    return render(Template(text=text), **PINNED)


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
