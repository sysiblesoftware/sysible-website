"""The published manuals must say what the markdown says.

Two defects this catches, both silent and both already shipped once:

1. A bullet that wrapped onto a second line ENDED its list and came back as a
   paragraph starting mid-sentence. The published SLOP manual read:

       • Manage — Restart, Stop, Start and Recreate that product's containers, so a

       wedged service can be recovered without a shell on the host.

   Twenty-five of those across the four manuals. Nothing complained, because the
   HTML was still valid HTML.

2. The .html files are generated from the .md files and COMMITTED. Editing a
   manual and forgetting to re-run the generator publishes the old text with no
   sign that it is old.

Run: pytest tests/
"""
import functools
import importlib.util
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]


def _generator():
    spec = importlib.util.spec_from_file_location(
        "generate_manuals", REPO / "tools" / "generate_manuals.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MANUALS = sorted((REPO / "manuals").glob("*.md"))
MANUALS = [p for p in MANUALS if p.name != "README.md"]


def test_there_are_manuals_to_check():
    assert MANUALS, "no manual sources found — this suite would pass vacuously"


def test_a_wrapped_bullet_stays_one_bullet():
    g = _generator()
    html, _toc = g.render(
        "## H\n\n"
        "- **Manage** — Restart, Stop, Start and Recreate that product's containers, so a\n"
        "  wedged service can be recovered without a shell on the host.\n"
        "- Second bullet.\n",
        "slop")
    assert html.count("<li>") == 2, f"the wrapped line became its own item: {html}"
    assert "so a wedged service can be recovered" in html, \
        f"the continuation line was lost or split out of the bullet: {html}"
    assert not re.search(r"</ul>\s*<p>wedged", html), \
        "a wrapped bullet still closes its list and reappears as a paragraph"


def test_a_blank_line_still_ends_the_list():
    """Lazy continuation must not swallow the paragraph AFTER a list."""
    g = _generator()
    html, _toc = g.render("## H\n\n- One.\n- Two.\n\nA new paragraph.\n", "slop")
    assert "<p>A new paragraph.</p>" in html, html
    assert html.count("<li>") == 2, html


def test_a_nested_bullet_is_not_swallowed_as_a_continuation():
    g = _generator()
    html, _toc = g.render("## H\n\n- Parent.\n  - Child.\n- Sibling.\n", "slop")
    assert html.count("<li>") == 3, f"a nested bullet was folded into its parent: {html}"


def test_a_table_right_after_a_bullet_is_still_a_table():
    g = _generator()
    html, _toc = g.render(
        "## H\n\n- A bullet.\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n", "slop")
    assert "<table>" in html, html
    assert "<li>A bullet.</li>" in html, html


@pytest.mark.parametrize("src", MANUALS, ids=lambda p: p.name)
def test_the_committed_html_matches_its_markdown(src):
    """Regenerating must be a no-op. When it is not, the site is serving text
    that no longer matches the source anyone edits."""
    g = _generator()
    out = REPO / f"{src.stem}-manual.html"
    assert out.exists(), f"{src.name} has no generated manual at {out.name}"
    before = out.read_text(encoding="utf-8")
    try:
        g.build(src)
        after = out.read_text(encoding="utf-8")
    finally:
        out.write_text(before, encoding="utf-8")
    # The generator stamps today's date into the cover and the footer, so a
    # byte comparison fails on every day but the one the manuals were last
    # built on — a test that cries wolf daily is a test people turn off. The
    # date is the one thing allowed to differ; everything else is the content.
    norm = functools.partial(re.compile(r"\d{4}-\d{2}-\d{2}").sub, "<date>")
    assert norm(after) == norm(before), (
        f"{out.name} is out of date with {src.name} — re-run "
        f"`python3 tools/generate_manuals.py` and commit the result")


@pytest.mark.parametrize("out", sorted(REPO.glob("*-manual.html")),
                         ids=lambda p: p.name)
def test_no_published_manual_has_a_bullet_torn_in_half(out):
    t = out.read_text(encoding="utf-8")
    torn = re.findall(r"</li>\n(?:</ul>\n)?<p>[a-z(]\S*[^<]{0,60}", t)
    assert not torn, (
        f"{out.name} has {len(torn)} bullet(s) broken mid-sentence: {torn[:3]}")
