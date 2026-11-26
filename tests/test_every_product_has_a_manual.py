"""Every product in the Products menu must have a manual, and it must be reachable.

Before this, four of the six products shipped no manual at all — Workstation,
Server, SLEP and SysTerm — and the five manuals that did exist were reachable
only from whichever product page happened to link them. There was no Docs entry
in the navigation anywhere on the site, so a reader evaluating the software had
no route to documentation except guessing a URL.

A product with no manual is the gap this catches. A manual nothing links to is
the other half of it.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob("*.html"))

# Product page -> the manual slug it must have. Keyed on the nav's own hrefs.
PRODUCTS = {
    "/linux": "workstation",
    "/server": "server",
    "/controller": "controller",
    "/slep": "slep",
    "/slop": "slop",
    "/systerm": "systerm",
}


def _products_in_nav():
    """The hrefs the Products menu actually offers, from the homepage."""
    s = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<summary>Products</summary>\s*<div class="pop">(.*?)</div>', s, re.S)
    assert m, "no Products menu on the homepage"
    return set(re.findall(r'href="([^"]+)"', m.group(1)))


def test_the_products_menu_is_what_this_expects():
    """If a product is added to the nav, this test must learn about it."""
    nav = _products_in_nav()
    missing = nav - set(PRODUCTS)
    assert not missing, (
        f"the Products menu offers {sorted(missing)}, which this test does not "
        f"know about — add it to PRODUCTS with its manual slug")


@pytest.mark.parametrize("href,slug", sorted(PRODUCTS.items()))
def test_the_product_has_a_manual(href, slug):
    p = ROOT / f"{slug}-manual.html"
    assert p.is_file(), f"{href} is a product in the nav with no {slug}-manual.html"
    assert p.stat().st_size > 10_000, (
        f"{p.name} is only {p.stat().st_size} bytes — that is a stub, not a manual")


@pytest.mark.parametrize("manual", sorted(ROOT.glob("*-manual.html")), ids=lambda p: p.name)
def test_every_manual_is_reachable(manual):
    """A manual nothing links to does not exist as far as a reader is concerned."""
    linkers = [p.name for p in PAGES
               if p != manual and manual.name in p.read_text(encoding="utf-8")]
    assert linkers, f"nothing on the site links to {manual.name}"


@pytest.mark.parametrize("page", [p for p in PAGES if not p.name.endswith("-manual.html")],
                         ids=lambda p: p.name)
def test_content_pages_offer_a_docs_menu(page):
    s = page.read_text(encoding="utf-8")
    if "<nav>" not in s:
        pytest.skip("no site navigation on this page")
    assert "<summary>Docs</summary>" in s, (
        f"{page.name} has a nav but no Docs menu — the manuals are unreachable "
        f"from here")
