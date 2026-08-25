"""The generic per-item tokens (getGeneralString, HTMLWriter.java:3977).

No oracle and no character: these run everywhere.
"""
from types import SimpleNamespace

from kirby_sheet.hde.items import apply


def _option(xmlid="OPT-XMLID", alias="OPT-ALIAS", display="OPT-DISPLAY"):
    return SimpleNamespace(xmlid=xmlid, alias=alias, display=display)


def stub(**overrides):
    """EVERY field a DIFFERENT value.

    Equal stub values make a crossed wire between two tokens invisible, and
    that mistake has shipped in this project before. Costs are distinct and
    deliberately not round.
    """
    fields = dict(
        display="DISPLAY-VALUE", name="NAME-VALUE", xmlid="XMLID-VALUE",
        alias="ALIAS-VALUE", input="INPUT-VALUE", levels=7,
        nameless_column2_output="TEXT-VALUE", selected_option=_option(),
        active_cost=13.0, real_cost=3.0, parent=None, parent_id="",
        quantity=1, include_notes_in_printout=False, notes="NOTES-VALUE",
    )
    fields.update(overrides)
    return SimpleNamespace(**fields)


def test_each_token_takes_its_own_field():
    out = apply("<!--DISPLAY-->|<!--XMLID-->|<!--ALIAS-->|<!--INPUT-->|"
                "<!--LEVELS-->|<!--TEXT-->", stub())
    assert out == "DISPLAY-VALUE|XMLID-VALUE|ALIAS-VALUE|INPUT-VALUE|7|TEXT-VALUE"


def test_the_option_tokens_are_not_crossed():
    out = apply("<!--OPTION-->|<!--OPTION_ALIAS-->|<!--OPTION_ID-->", stub())
    assert out == "OPT-DISPLAY|OPT-ALIAS|OPT-XMLID"


def test_an_object_with_no_option_yields_empty_strings_not_a_crash():
    out = apply("<!--OPTION-->|<!--OPTION_ALIAS-->|<!--OPTION_ID-->",
                stub(selected_option=None))
    assert out == "||"


def test_ifname_block_is_kept_when_the_object_is_named():
    assert apply("<!--IFNAME--><!--NAME--><!--/IFNAME-->", stub()) == "NAME-VALUE"


def test_ifname_block_is_stripped_when_the_object_is_unnamed():
    """HD emits `name: ` with nothing after it: the BLOCK goes, the literal
    text around it stays."""
    assert apply("name: <!--IFNAME--><!--NAME--><!--/IFNAME-->",
                 stub(name="")) == "name: "


def test_a_whitespace_only_name_counts_as_unnamed():
    """Java tests getName().trim().length() > 0, not just null."""
    assert apply("<!--IFNAME--><!--NAME--><!--/IFNAME-->", stub(name="   ")) == ""


def test_active_cost_is_rounded_up_like_hd():
    assert apply("<!--ACTIVE_COST-->", stub(active_cost=12.25)) == "13"


def test_is_separator_and_is_list_are_stripped_for_an_ordinary_object():
    """Both blocks belong to List containers. An ordinary power is neither,
    so both must vanish -- leaving them would print `separator: true` on
    every row."""
    out = apply("<!--IS_SEPARATOR-->sep<!--/IS_SEPARATOR-->"
                "<!--IS_LIST-->lst<!--/IS_LIST-->", stub())
    assert out == ""
