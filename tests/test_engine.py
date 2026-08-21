"""The four string primitives HTMLWriter is built from.

Ported from com.hero.util.HTMLWriter. Three of these tests assert behaviour
that looks like a bug and IS one; byte-for-byte means reproducing it. They are
marked so nobody later tidies them away.
"""
import pytest

from kirby_sheet.engine import (
    RunawaySubstitution,
    get_long_value,
    swap_all_long_values,
    swap_long_value,
    swap_value,
)


class TestSwapValue:
    def test_replaces_the_tag(self):
        assert swap_value("<!--X-->", "1", "a<!--X-->b") == "a1b"

    def test_replaces_every_occurrence(self):
        """A `while` loop, not an `if` (HTMLWriter.java:5643)."""
        assert swap_value("<!--X-->", "1", "<!--X-->,<!--X-->") == "1,1"

    def test_is_case_insensitive(self):
        assert swap_value("<!--x-->", "1", "a<!--X-->b") == "a1b"

    def test_none_value_becomes_empty(self):
        assert swap_value("<!--X-->", None, "a<!--X-->b") == "ab"

    def test_none_html_passes_through(self):
        assert swap_value("<!--X-->", "1", None) is None

    def test_absent_tag_is_a_no_op(self):
        assert swap_value("<!--X-->", "1", "abc") == "abc"

    def test_a_value_containing_its_own_tag_raises(self):
        """Java loops here forever. A hang produces no output to be
        byte-identical with, so this raises instead of reproducing it."""
        with pytest.raises(RunawaySubstitution):
            swap_value("<!--X-->", "<!--X-->", "a<!--X-->b")


class TestGetLongValue:
    def test_extracts_between_the_tags(self):
        assert get_long_value("<!--A-->", "<!--/A-->", "x<!--A-->mid<!--/A-->y") == "mid"

    def test_missing_open_returns_none(self):
        assert get_long_value("<!--A-->", "<!--/A-->", "no tags here") is None

    def test_missing_close_returns_none(self):
        assert get_long_value("<!--A-->", "<!--/A-->", "x<!--A-->y") is None

    def test_is_case_insensitive(self):
        assert get_long_value("<!--a-->", "<!--/a-->", "<!--A-->m<!--/A-->") == "m"

    def test_close_at_index_zero_reads_as_absent(self):
        """Java's guard is `> 0`, not `>= 0` (HTMLWriter.java:4539). When the
        closing tag resolves to index 0 — here because it is the same string
        as the opening tag, so both find the same position — Java treats it as
        absent and returns null. With `end < 0` this would instead return the
        empty string, which is why the boundary needs its own test: the
        previous version of this test used a closer positioned BEFORE the
        opener, where find returns -1 and both guards agree.
        """
        assert get_long_value("<!--A-->", "<!--A-->", "<!--A-->x") is None


class TestSwapLongValue:
    def test_replaces_the_block_including_the_closer(self):
        assert swap_long_value("<!--A-->", "<!--/A-->", "Z", "x<!--A-->m<!--/A-->y") == "xZy"

    def test_replaces_only_the_first(self):
        """An `if`, not a `while` (HTMLWriter.java:5410) — the opposite of
        swap_value, and deliberate."""
        html = "<!--A-->1<!--/A--><!--A-->2<!--/A-->"
        assert swap_long_value("<!--A-->", "<!--/A-->", "Z", html) == "Z<!--A-->2<!--/A-->"

    def test_a_lowercase_closing_tag_is_not_matched(self):
        """The guard compares the RAW end tag against upper-cased html
        (HTMLWriter.java:5411) while the index below it upper-cases the end
        tag. A lower-case closer fails the guard, so nothing is replaced."""
        html = "x<!--A-->m<!--/a-->y"
        assert swap_long_value("<!--A-->", "<!--/a-->", "Z", html) == html

    def test_none_value_becomes_empty(self):
        assert swap_long_value("<!--A-->", "<!--/A-->", None, "x<!--A-->m<!--/A-->y") == "xy"


class TestSwapAllLongValues:
    def test_replaces_every_block(self):
        html = "<!--A-->1<!--/A--><!--A-->2<!--/A-->"
        assert swap_all_long_values("<!--A-->", "<!--/A-->", "Z", html) == "ZZ"

    def test_absent_block_is_a_no_op(self):
        assert swap_all_long_values("<!--A-->", "<!--/A-->", "Z", "abc") == "abc"
