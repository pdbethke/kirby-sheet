"""Repetition, built from the four primitives -- not a fifth primitive.

engine.py's header already describes this shape: extract the block once with
get_long_value, render it per item, join, and put the accumulation back with
swap_long_value. These tests need no oracle and no character, which is the
point of proving the mechanism before seven sections depend on it.
"""
from kirby_sheet.hde.repeat import render_list


def _upper(block, item, index):
    return block.replace("<!--X-->", item.upper())


def test_the_block_is_rendered_once_per_item():
    out = render_list("a<!--L--> [<!--X-->]<!--/L-->b", "<!--L-->", "<!--/L-->",
                      ["p", "q"], _upper)
    assert out == "a [P] [Q]b"


def test_an_empty_item_list_removes_the_block_and_keeps_its_surroundings():
    out = render_list("a<!--L--> [<!--X-->]<!--/L-->b", "<!--L-->", "<!--/L-->",
                      [], _upper)
    assert out == "ab"


def test_a_missing_block_leaves_the_text_untouched():
    assert render_list("abc", "<!--L-->", "<!--/L-->", ["p"], _upper) == "abc"


def test_one_item_appears_once_not_twice():
    """The accumulation must REPLACE the block, not sit beside it. Getting
    this wrong renders every section doubled, which a per-key sweep cannot
    see because list keys are not addressable by name."""
    out = render_list("<!--L--><!--X--><!--/L-->", "<!--L-->", "<!--/L-->",
                      ["p"], _upper)
    assert out == "P"


def test_the_renderer_receives_the_item_index():
    out = render_list("<!--L-->[<!--X-->]<!--/L-->", "<!--L-->", "<!--/L-->",
                      ["p", "q"],
                      lambda block, item, index: block.replace("<!--X-->", str(index)))
    assert out == "[0][1]"


def test_each_item_gets_a_FRESH_copy_of_the_block():
    """A renderer that mutated a shared block would leak item 0's values into
    item 1. Substituting a token that only the first item fills would then
    show up in the second."""
    def once(block, item, index):
        return block.replace("<!--X-->", item) if index == 0 else block
    out = render_list("<!--L-->(<!--X-->)<!--/L-->", "<!--L-->", "<!--/L-->",
                      ["a", "b"], once)
    assert out == "(a)(<!--X-->)"
