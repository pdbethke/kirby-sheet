"""The gate's own guard rails. If these are wrong, every phase gate is.

`tests/keys.py` is what every later phase is measured by, so it is tested
before it is trusted. The assertions that matter here are the ones proving
the harness can FAIL: a comparison that silently checks nothing is the exact
shape of the tests-that-could-not-fail this project keeps finding.
"""
import pytest

from tests.keys import compare, scalar_lines


def test_scalar_lines_keeps_the_whole_raw_line():
    """Raw lines, not parsed values: `flash_def:` has no space after the
    colon where `campaign: ` does, and that difference is HD's output."""
    assert scalar_lines("campaign: \nflash_def:") == {
        "campaign": "campaign: ", "flash_def": "flash_def:"}


def test_scalar_lines_ignores_indented_list_item_keys():
    """List keys repeat per item and are not addressable by name."""
    assert scalar_lines("skills:\n - cost: 3\n   xmlid: LANG") == {"skills": "skills:"}


def test_compare_rejects_an_empty_key_list():
    with pytest.raises(AssertionError, match="always passes"):
        compare({}, {}, [])


def test_compare_rejects_a_key_the_oracle_does_not_emit():
    with pytest.raises(AssertionError, match="no such keys"):
        compare({"a": "a: 1"}, {}, ["a"])


def test_compare_fails_on_a_differing_value():
    with pytest.raises(AssertionError, match="1 of 1 keys differ"):
        compare({"a": "a: 1"}, {"a": "a: 2"}, ["a"])


def test_compare_fails_when_we_emit_nothing_for_a_key():
    """The unported case: HD has the key, we left the marker in."""
    with pytest.raises(AssertionError, match="ours: None"):
        compare({}, {"a": "a: 2"}, ["a"])


def test_compare_returns_the_count_it_checked():
    assert compare({"a": "a: 1"}, {"a": "a: 1"}, ["a"]) == 1
