"""Everything a visitor can download must come from a GitHub Release.

A release is the only artifact a user can actually rely on: it is permanent,
public without a login, signed, and carries its checksums. The alternatives all
look like downloads and are not —

  * a workflow ARTIFACT expires (30-90 days), needs a GitHub account, arrives
    as a zip, and is unsigned. ISO #93 of Sysible Server was exactly this: a
    3 GB artifact that proved a fix and could not be handed to anyone.
  * /archive/ and raw.githubusercontent.com serve whatever a branch holds right
    now, so what someone downloads twice is not the same thing twice.
  * a hard-coded releases/download/vX.Y.Z/... URL in a PAGE is correct the day
    it is typed. release-linux.json is rewritten by a scheduled workflow; the
    pages are not. That is how this site came to advertise a Workstation
    version two releases behind.

So: pages link to /releases or /releases/latest and nothing else, and the only
place a pinned asset URL may appear is the synced JSON.
"""
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PAGES = sorted(REPO.glob("*.html"))
FEED = REPO / "release-linux.json"

# Things that look like a download and are not one a user can depend on.
FORBIDDEN = {
    "a workflow run or artifact": re.compile(r"github\.com/[^\s\"']+/actions/(runs|artifacts|workflows)"),
    "an artifact download": re.compile(r"/suites/\d+/artifacts/|/artifacts/\d+"),
    "a branch tarball": re.compile(r"github\.com/[^\s\"']+/archive/"),
    "raw branch content": re.compile(r"raw\.githubusercontent\.com"),
    "a codeload tarball": re.compile(r"codeload\.github\.com"),
}


def _sources():
    for p in PAGES:
        yield p, p.read_text(encoding="utf-8")


def test_there_are_pages_to_check():
    assert PAGES, "no .html pages found — this guard would pass vacuously"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_no_page_offers_something_that_is_not_a_release(page):
    src = page.read_text(encoding="utf-8")
    bad = []
    for what, rx in FORBIDDEN.items():
        for m in rx.finditer(src):
            line = src[:m.start()].count("\n") + 1
            bad.append(f"  line {line}: {what} — {m.group(0)[:90]}")
    assert not bad, (
        f"{page.name} points a visitor at something that is not a release:\n"
        + "\n".join(bad))


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_no_page_hard_codes_an_asset_url(page):
    """A pinned asset URL in a page goes stale the next time a release is cut.

    release-linux.json carries these and a workflow rewrites it; the pages are
    not rewritten, so a URL typed into one is a promise nobody keeps.
    """
    src = page.read_text(encoding="utf-8")
    hits = [m.group(0) for m in re.finditer(r"github\.com/[^\s\"']+/releases/download/[^\s\"')]+", src)]
    assert not hits, (
        f"{page.name} hard-codes {len(hits)} asset URL(s); these belong in "
        f"release-linux.json, which is synced:\n  " + "\n  ".join(h[:110] for h in hits))


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_no_page_pins_a_release_tag(page):
    """/releases/tag/vX.Y.Z is the same staleness in a different shape."""
    src = page.read_text(encoding="utf-8")
    hits = [m.group(0) for m in re.finditer(r"github\.com/[^\s\"']+/releases/tag/[^\s\"')]+", src)]
    assert not hits, (
        f"{page.name} links to a PINNED release; use /releases/latest so it "
        f"follows:\n  " + "\n  ".join(h[:110] for h in hits))


def test_the_api_calls_ask_for_the_latest_release():
    """The pages fill their version labels from the API. It must be the
    releases endpoint — an Actions endpoint would surface builds nobody can
    download."""
    seen = 0
    for page, src in _sources():
        for n, line in enumerate(src.splitlines(), 1):
            if "api.github.com" not in line:
                continue
            seen += 1
            # The URL is built by concatenation --
            #   "https://api.github.com/repos/" + repo + "/releases/latest"
            # -- so the endpoint is on the line, not inside one string literal.
            assert "/releases/latest" in line, (
                f"{page.name}:{n} calls a GitHub API endpoint that is not the "
                f"latest release: {line.strip()[:120]}")
            assert "/actions/" not in line, (
                f"{page.name}:{n} calls an Actions endpoint; builds there are "
                f"not downloadable by a visitor: {line.strip()[:120]}")
    assert seen, "no GitHub API call found — the version labels cannot be live"


def test_every_asset_url_in_the_feed_belongs_to_the_tag_it_declares():
    """The synced feed is the one place a pinned URL is allowed, so it has to
    be internally consistent: an asset from a different release would hand
    someone the wrong ISO while the page said otherwise."""
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    tag = feed["tag"]
    urls = re.findall(r"https://github\.com/[^\s\"']+/releases/download/([^/]+)/", json.dumps(feed))
    assert urls, "the feed carries no asset URLs at all"
    wrong = sorted({u for u in urls if u != tag})
    assert not wrong, (
        f"release-linux.json declares tag {tag} but links assets from {wrong}")
