"""A changed icon must mean a changed URL.

The favicon was replaced twice and the browser tab kept showing the old "S"
tile both times. Neither attempt was wrong about the FILE -- favicon.svg,
icon-512.png and apple-touch-icon.png were all correctly redrawn and correctly
deployed, and the Cloudflare Pages deploys for both went green. What neither
attempt changed was the URL.

Chrome does not re-fetch a favicon because its bytes changed. It keeps a
favicon database of its own, keyed by URL, which outlives an ordinary cache
clear. A bare /favicon.svg is the same URL today as last week, so the tab kept
the icon it already had. Reporting it as "you didn't change the favicon" was a
perfectly fair reading: the thing on screen had not changed.

So the href now carries a hash of the file's own bytes, stamped by
tools/stamp_icons.py, and this guard fails if any page's stamp has drifted from
the file it names.
"""
import hashlib
import pathlib
import re
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = ("favicon.svg", "icon-512.png", "apple-touch-icon.png")
PAGES = sorted(ROOT.glob("*.html"))
# Any href to one of the icons, with or without a stamp.
REF = re.compile(r'href="/(' + "|".join(re.escape(i) for i in ICONS) + r')(\?v=([0-9a-f]+))?"')


def _stamp(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:8]


def test_there_are_pages_and_icons_to_check():
    """A guard that silently checks nothing is worse than no guard."""
    assert PAGES, "no .html pages found — this guard would pass vacuously"
    for name in ICONS:
        assert (ROOT / name).is_file(), f"{name} is referenced by the site but missing"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_every_icon_href_is_stamped_with_the_current_file(page):
    src = page.read_text(encoding="utf-8")
    refs = REF.findall(src)
    if not refs:
        pytest.skip(f"{page.name} references no icons")
    problems = []
    for name, _q, got in refs:
        want = _stamp(name)
        if not got:
            problems.append(
                f"  /{name} has NO ?v= stamp. A bare icon URL is the same URL "
                f"forever, so a browser that has cached the old icon never "
                f"fetches the new one.")
        elif got != want:
            problems.append(
                f"  /{name}?v={got} is stale — the file now hashes to {want}. "
                f"Run: python3 tools/stamp_icons.py")
    assert not problems, f"{page.name}:\n" + "\n".join(problems)


def test_the_icons_are_told_to_revalidate():
    """The stamped URL covers browsers that read the HTML. Chrome's favicon
    database and iOS both probe the BARE path, so that one must revalidate."""
    headers = (ROOT / "_headers").read_text(encoding="utf-8")
    for name in ICONS:
        block = re.search(r"^/" + re.escape(name) + r"\n((?:  .*\n)+)", headers, re.M)
        assert block, f"_headers has no rule for /{name}, so the unstamped path is cached by default"
        assert "must-revalidate" in block.group(1), (
            f"_headers does not make /{name} revalidate; a browser probing the "
            f"bare path can be served a cached icon that predates the current one")


def test_the_stamper_is_idempotent_and_agrees_with_this_guard():
    """Running the tool must be a no-op on a correctly stamped tree -- otherwise
    the tool and the guard disagree and one of them is lying."""
    import subprocess
    import sys
    before = {p: p.read_text(encoding="utf-8") for p in PAGES}
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "stamp_icons.py")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    after = {p: p.read_text(encoding="utf-8") for p in PAGES}
    changed = [p.name for p in PAGES if before[p] != after[p]]
    assert not changed, f"stamp_icons.py rewrote pages this guard considered correct: {changed}"
