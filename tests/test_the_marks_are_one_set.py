"""Every product mark must be the same drawing on every page that draws it.

The marks are inline SVG, hand-copied into each page's <defs>. There are 22
copies of 6 marks across 8 pages and no single source of truth, so the only
thing keeping them equal is that nobody edited one of them. Two had already
drifted when this was written:

  * #mark-slep on index.html was missing the green play triangle that slep.html
    draws, so the Engineering Platform had one logo on the homepage and a
    different one on its own page.
  * #mark-slop's badge ring was #43a047 on both pages it appears on, while
    every other mark's ring is the brand green #6ddb73 -- the family rule the
    file's own comment states ("Same badge, same ring, same green rule; only
    the glyph differs").

This parses the <defs> as XML rather than matching tags with a regex: nested
<g> elements made every regex attempt at this quietly wrong, in both directions.
"""
import pathlib
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
BRAND_GREEN = "#6ddb73"


def _marks(path):
    """{mark id: canonical serialisation} for one page."""
    text = path.read_text(encoding="utf-8")
    out = {}
    # The <defs> block, wrapped in a root. NOT a `<svg ...>.*?</svg>` match:
    # non-greedy truncates the sprite mid-structure and greedy swallows the
    # inline icons, and both produced a parser that silently found nothing.
    for m in re.finditer(r"<defs>.*?</defs>", text, re.S):
        if 'id="mark-' not in m.group(0):
            continue
        frag = '<svg xmlns="%s">%s</svg>' % (SVG_NS, m.group(0))
        try:
            root = ET.fromstring(frag)
        except ET.ParseError as e:
            raise AssertionError(
                "%s: the <defs> sprite is not well-formed (%s). Unbalanced "
                "tags here do not fail to render -- the browser nests the "
                "marks instead, so one <use> draws several logos stacked."
                % (path.name, e))
        for g in root.iter(f"{{{SVG_NS}}}g"):
            gid = g.get("id", "")
            if gid.startswith("mark-"):
                for c in g.iter():
                    c.tail = None
                out[gid] = ET.tostring(g, encoding="unicode")
    return out


ALL = {p.name: _marks(p) for p in sorted(ROOT.glob("*.html"))}
BY_ID = defaultdict(dict)
for page, marks in ALL.items():
    for mid, body in marks.items():
        BY_ID[mid][page] = body


def test_the_pages_actually_define_marks():
    """A parser that silently returns nothing would make every test below pass."""
    assert len(BY_ID) >= 5, f"only found {sorted(BY_ID)} — the parser is wrong"
    assert sum(len(v) for v in BY_ID.values()) >= 15, "too few copies found to be checking anything"


@pytest.mark.parametrize("mark", sorted(BY_ID))
def test_one_mark_is_one_drawing(mark):
    pages = BY_ID[mark]
    distinct = defaultdict(list)
    for page, body in pages.items():
        distinct[body].append(page)
    assert len(distinct) == 1, (
        f"#{mark} is drawn {len(distinct)} different ways:\n" +
        "\n".join(f"  {', '.join(sorted(p))}" for p in distinct.values()))


@pytest.mark.parametrize("mark", sorted(BY_ID))
def test_every_badge_ring_is_the_brand_green(mark):
    """The ring is the family resemblance. A mark with its own green is a
    second brand, not a product in this one."""
    body = next(iter(BY_ID[mark].values()))
    rings = re.findall(r'rx="10\.6"[^/>]*stroke="(#[0-9a-fA-F]{6})"', body)
    assert rings, f"#{mark} has no badge ring at all"
    for c in rings:
        assert c.lower() == BRAND_GREEN, (
            f"#{mark}'s ring is {c}, not the brand green {BRAND_GREEN}")
