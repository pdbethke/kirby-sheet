"""Which .hde tokens a template uses, and which the renderer resolves.

`inspect_template` must MEASURE against `render()`, not carry its own list of
implemented tokens -- see `test_tracks_the_renderer_not_a_hardcoded_list`,
which breaks the renderer's substitution and asserts the report follows it
down. A report that cannot be made to fail by breaking the thing it reports
on is not proving anything.

A token's identity is its bare tag name, upper-cased, with any leading `/`
stripped -- not the raw `<!--TAG-->` marker text. That is what makes a
paired block such as TEMPLATE_NAME (opener + closer) count as ONE token
resolved, not two: it is one thing the renderer either strips as a whole or
does not, and it is one line item on a person's worklist, not two.
"""
from __future__ import annotations

from kirby_sheet.inspect import TemplateReport, describe, inspect_template

#: These fixtures use only opening-region tokens, which do not read the
#: character. None proves that: anything reading it would raise here.
NO_HERO = None
from kirby_sheet.template import Template


def test_template_with_only_implemented_tokens_has_no_unresolved():
    template = Template(text="v=<!--APP_VERSION--> t=<!--TIMESTAMP-->")

    report = inspect_template(template, NO_HERO)

    assert report.tokens_unresolved == ()
    assert set(report.tokens_resolved) == {"APP_VERSION", "TIMESTAMP"}


def test_an_unimplemented_token_is_reported_unresolved():
    template = Template(text="name: <!--CHARACTER_NAME-->")

    report = inspect_template(template, NO_HERO)

    assert report.tokens_unresolved == ("CHARACTER_NAME",)
    assert report.tokens_resolved == ()


def test_tokens_used_counts_each_token_once():
    template = Template(text="<!--APP_VERSION--> and again <!--APP_VERSION-->")

    report = inspect_template(template, NO_HERO)

    assert report.tokens_used == ("APP_VERSION",)


def test_a_token_named_only_inside_a_stripped_block_is_reported_resolved():
    """This is INTENDED, not a bug: TEMPLATE_DESCRIPTION's block is stripped
    whole by swap_all_long_values, so CHARACTER_NAME -- named only in its
    prose, never implemented by render() -- disappears along with it and is
    reported resolved. "Resolved" here means "does not survive rendering",
    and that is true regardless of whether substitution or stripping is what
    removed it -- for a worklist, a token that isn't in the output needs no
    work either way. See the module docstring for the ruling."""
    template = Template(
        text="<!--TEMPLATE_DESCRIPTION-->uses <!--CHARACTER_NAME--><!--/TEMPLATE_DESCRIPTION--> body"
    )

    report = inspect_template(template, NO_HERO)

    assert report.tokens_used == ("TEMPLATE_DESCRIPTION", "CHARACTER_NAME")
    assert report.tokens_resolved == ("TEMPLATE_DESCRIPTION", "CHARACTER_NAME")
    assert report.tokens_unresolved == ()


def test_a_paired_block_counts_as_one_token_not_two():
    """TEMPLATE_NAME's opener and closer are the same token: render() strips
    the whole block as a unit, and a worklist should not list a thing twice
    because it has two markers."""
    template = Template(text="<!--TEMPLATE_NAME-->Sheet<!--/TEMPLATE_NAME-->")

    report = inspect_template(template, NO_HERO)

    assert report.tokens_used == ("TEMPLATE_NAME",)
    assert report.tokens_resolved == ("TEMPLATE_NAME",)


def test_mixed_case_token_spellings_fold_to_one_token():
    """HD's swap_value matches case-insensitively (engine.py:39 reproduces
    that), so <!--APP_VERSION--> and <!--app_version--> name the same token,
    not two -- a template author mixing case should not double-count."""
    template = Template(text="<!--APP_VERSION--> and <!--app_version-->")

    report = inspect_template(template, NO_HERO)

    assert report.tokens_used == ("APP_VERSION",)
    assert report.tokens_resolved == ("APP_VERSION",)


def test_the_three_tuples_are_consistent():
    template = Template(
        text="<!--APP_VERSION--><!--CHARACTER_NAME--><!--TIMESTAMP--><!--STR-->"
    )

    report = inspect_template(template, NO_HERO)

    assert set(report.tokens_used) == set(report.tokens_resolved) | set(report.tokens_unresolved)
    assert set(report.tokens_resolved) & set(report.tokens_unresolved) == set()


def test_tokens_used_preserves_first_appearance_order():
    template = Template(text="<!--STR--><!--CHARACTER_NAME--><!--STR--><!--APP_VERSION-->")

    report = inspect_template(template, NO_HERO)

    assert report.tokens_used == ("STR", "CHARACTER_NAME", "APP_VERSION")


def test_template_report_is_frozen():
    report = TemplateReport(tokens_used=(), tokens_resolved=(), tokens_unresolved=())
    try:
        report.tokens_used = ("x",)
    except Exception:
        pass
    else:
        raise AssertionError("TemplateReport must be immutable")


def test_describe_states_the_counts():
    template = Template(
        text="<!--APP_VERSION--><!--CHARACTER_NAME--><!--STR-->"
    )
    report = inspect_template(template, NO_HERO)

    text = describe(report)

    assert "3 tokens used" in text
    assert "1 resolved" in text
    assert "2 unresolved" in text


def test_describe_lists_the_unresolved_tokens():
    template = Template(text="<!--APP_VERSION--><!--CHARACTER_NAME-->")

    text = describe(inspect_template(template, NO_HERO))

    assert "CHARACTER_NAME" in text
    assert "APP_VERSION" not in text.split("Unresolved:")[-1]


def test_tracks_the_renderer_not_a_hardcoded_list(monkeypatch):
    """The strongest proof available: break render()'s actual substitution
    and watch the report follow it down, rather than a list kept in sync by
    hand. APP_VERSION is chosen because it is a single `swap_value` call --
    breaking it cannot accidentally break TEMPLATE_NAME/DESCRIPTION too."""
    import kirby_sheet.render as render_module

    template = Template(text="<!--APP_VERSION--><!--CHARACTER_NAME-->")

    # Before: APP_VERSION resolves, CHARACTER_NAME (genuinely unimplemented,
    # not merely absent from render()'s source text -- it never appears
    # there at all) does not.
    before = inspect_template(template, NO_HERO)
    assert "APP_VERSION" in before.tokens_resolved
    assert "CHARACTER_NAME" in before.tokens_unresolved

    original_render = render_module.render

    def broken_render(template, hero, **kwargs):
        # Simulate APP_VERSION no longer being substituted -- as if the
        # swap_value("<!--APP_VERSION-->", ...) call were deleted from
        # render(). Any other real behaviour is left alone.
        text = original_render(template, hero, **kwargs)
        return text.replace(kwargs["app_version"], "<!--APP_VERSION-->", 1) \
            if kwargs["app_version"] not in ("", None) else text

    # Patch the name inspect.py actually calls, not the module it came from.
    import kirby_sheet.inspect as inspect_module
    monkeypatch.setattr(inspect_module, "render", broken_render)

    after = inspect_module.inspect_template(template, NO_HERO)
    assert "APP_VERSION" in after.tokens_unresolved
    assert "APP_VERSION" not in after.tokens_resolved
