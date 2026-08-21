"""Loading a .hde, including the two things Java does at load time."""
from kirby_sheet.template import Template


def test_reads_the_file(tmp_path):
    p = tmp_path / "t.hde"
    p.write_bytes(b"<html>hello</html>")
    assert Template.from_path(p).text == "<html>hello</html>"


def test_invalid_utf8_becomes_the_replacement_character(tmp_path):
    """Java reads with the platform default charset (HTMLWriter.java:207).
    On a UTF-8 JVM a latin-1 non-breaking space is invalid and becomes U+FFFD.
    Decoding as latin-1 would be *correct* and would fail the byte diff."""
    p = tmp_path / "t.hde"
    p.write_bytes(b"Cost\xa0</b>")
    assert Template.from_path(p).text == "Cost�</b>"


def test_file_extension_blocks_are_collected_and_stripped(tmp_path):
    """getFileExtensions() runs in the constructor and REMOVES the blocks
    from the template as it reads them (HTMLWriter.java:3901)."""
    p = tmp_path / "t.hde"
    p.write_bytes(b"a<!--FILE_EXTENSION--> html <!--/FILE_EXTENSION-->b")
    template = Template.from_path(p)
    assert template.file_extensions == ["HTML"]
    assert template.text == "ab"


def test_several_file_extension_blocks(tmp_path):
    p = tmp_path / "t.hde"
    p.write_bytes(b"<!--FILE_EXTENSION-->htm<!--/FILE_EXTENSION-->"
                  b"<!--FILE_EXTENSION-->html<!--/FILE_EXTENSION-->x")
    template = Template.from_path(p)
    assert template.file_extensions == ["HTM", "HTML"]
    assert template.text == "x"


def test_no_file_extension_block(tmp_path):
    p = tmp_path / "t.hde"
    p.write_bytes(b"plain")
    template = Template.from_path(p)
    assert template.file_extensions == []
    assert template.text == "plain"
