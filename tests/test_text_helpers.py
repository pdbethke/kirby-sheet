"""Turning HD's markup into something a terminal can print."""
from kirby_sheet.text import plain_text


def test_strips_italics():
    assert plain_text("<i>Iron Grasshopper:</i>  Leaping +69m") == "Iron Grasshopper:  Leaping +69m"


def test_strips_bold():
    assert plain_text("Killing Attack <b>plus</b> Flash") == "Killing Attack plus Flash"


def test_preserves_hd_double_spaces():
    """"Language:  Creole" has two spaces because HD emits two, proved
    deliberate by the byte-fidelity work. A stripper that normalises
    whitespace is silently wrong."""
    assert plain_text("Language:  Creole (3 Active Points)") == "Language:  Creole (3 Active Points)"


def test_decodes_entities_if_one_ever_appears():
    """None exist in the 655-character corpus. bs4 handles them anyway, and
    this pins the behaviour so a later switch to a regex would be caught."""
    assert plain_text("Fire &amp; Ice") == "Fire & Ice"


def test_plain_text_is_unchanged():
    assert plain_text("Resistant Protection (10 PD/10 ED)") == "Resistant Protection (10 PD/10 ED)"


def test_empty_string():
    assert plain_text("") == ""


def test_a_less_than_sign_that_is_not_a_tag_survives():
    """Free text a player typed may contain "<". It must not be eaten."""
    assert "<" in plain_text("Only when STR < 20")
