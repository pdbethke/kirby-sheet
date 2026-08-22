"""The view model is data and nothing else."""
import dataclasses

import pytest

from kirby_sheet.sheet import (CharacteristicRow, Entry, Identity, Prose,
                               Section, Sheet, Totals)


def test_every_class_is_a_frozen_dataclass():
    """Frozen because a backend must not be able to edit the sheet while
    rendering it — HD's own exporter mutates as it renders, and that is the
    behaviour this design deliberately does not inherit."""
    for cls in (Sheet, Identity, CharacteristicRow, Entry, Section, Totals, Prose):
        assert dataclasses.is_dataclass(cls), cls
        assert cls.__dataclass_params__.frozen, cls


def test_the_model_imports_nothing_from_kirby_cost():
    """sheet.py is the shared dependency of every backend; if it reached into
    kirby-cost, every backend would too."""
    import kirby_sheet.sheet as module
    source = open(module.__file__, encoding="utf-8").read()
    assert "kirby_cost" not in source


def test_an_entry_carries_both_costs():
    e = Entry(id="1", name="", alias="Growth", xmlid="GROWTH",
              display="Growth ...", cost=0, cost_before_framework=29,
              active_cost=44, end=0)
    assert (e.cost, e.cost_before_framework) == (0, 29)


def test_a_section_is_named_and_holds_entries():
    s = Section(name="powers", entries=(Entry(id="1", name="", alias="a",
                xmlid="A", display="a", cost=1, cost_before_framework=1,
                active_cost=1, end=0),))
    assert s.name == "powers" and len(s.entries) == 1


def test_a_list_of_entries_is_coerced_to_a_tuple():
    """The previous version of this test passed a tuple and asserted it got a
    tuple, which is true of any implementation. Passing a LIST is what
    distinguishes a model that enforces immutability from one that merely
    annotates it."""
    s = Section(name="powers", entries=[])
    assert isinstance(s.entries, tuple)


def test_a_sheets_collections_are_coerced_too():
    sheet = Sheet(characteristics=[], sections=[])
    assert isinstance(sheet.characteristics, tuple)
    assert isinstance(sheet.sections, tuple)


def test_prose_is_a_frozen_dataclass_with_tuple_notes():
    """Prose.notes is a tuple; a list passed in is coerced, following the
    pattern the other collections use."""
    p = Prose(background="B", personality="P", quote="Q", tactics="T",
              campaign_use="C", appearance="A",
              notes=["1", "2", "3"])
    assert isinstance(p.notes, tuple)
    assert p.notes == ("1", "2", "3")
