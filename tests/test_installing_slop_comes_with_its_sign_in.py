"""If a page tells you to install SLOP, it must tell you how to sign in to it.

Reported as "sysible/sysible isn't the default password for slop". The password
was right; the username is `admin`. SLOP's shipped default is admin/sysible --
set in the IdP as _DEFAULT_ADMIN_USER / _DEFAULT_ADMIN_PASSWORD, documented and
deliberately public, because "I can't find the default slop username and
password" is the support question it exists to answer.

It was stated in exactly one place on this site, and not on any of the pages
that hand someone the install command. A page that says `install-sysible slop`
and then stops has set up a web front door the reader cannot open.

This is the inverse of test_no_page_advertises_a_default_password, and the two
are not in conflict: that one forbids claiming the OS IMAGE ships a login (it
does not -- the live account is locked and removed on install); this one
requires naming the APP's documented bootstrap account wherever the app is
offered.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# A page "offers SLOP" only if it hands over an install COMMAND. Matching the
# repository name alone caught every page with the project in its footer --
# linking to SLOP is not offering to install it, and demanding sign-in details
# on a page that merely mentions it would push the credential everywhere.
OFFERS = (re.compile(r"install-sysible\s+slop", re.I),
          re.compile(r"clone\s+\S*Sysible-Linux-Operations-Platform", re.I))


def _pages_offering_slop():
    out = []
    for p in sorted(ROOT.glob("*.html")):
        s = p.read_text(encoding="utf-8")
        if any(rx.search(s) for rx in OFFERS):
            out.append(p)
    return out


PAGES = _pages_offering_slop()


def test_some_page_actually_offers_slop():
    """Guard the guard: an empty list would make everything below vacuous."""
    assert PAGES, "no page offers SLOP — the detector is wrong"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_it_names_the_account(page):
    s = page.read_text(encoding="utf-8")
    assert re.search(r"\badmin\b", s), (
        f"{page.name} tells the reader to install SLOP and never names the "
        f"account. They will try the OS login and fail — which is exactly what "
        f"was reported.")


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_it_pairs_the_account_with_its_password(page):
    """`admin` on its own is half an answer."""
    # Tag-stripped and whitespace-collapsed: the manual states it as a two-row
    # table ("Username | admin", "Password | sysible"), the pages as "admin /
    # sysible". A pattern tight enough for the prose form misses the table.
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page.read_text(encoding="utf-8")))
    assert re.search(r"admin\b.{0,60}?\bsysible", text, re.I | re.S), \
        f"{page.name} names admin but not the password that goes with it"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_it_says_the_default_is_public(page):
    """Printing a credential is only defensible because it is documented. A
    page that states it without saying so reads as a leak, and gives the reader
    no reason to change it."""
    s = page.read_text(encoding="utf-8").lower()
    assert "public" in s, \
        f"{page.name} states the default without saying it is public and must be changed"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_it_says_where_to_change_it(page):
    assert "/account" in page.read_text(encoding="utf-8"), \
        f"{page.name} does not say where to change the shipped default"
