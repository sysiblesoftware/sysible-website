#!/usr/bin/env python3
"""Stamp the icon <link> hrefs with a hash of the icon's own bytes.

WHY THIS EXISTS. The favicon was replaced twice and the tab kept showing the
old "S" tile both times, because both changes rewrote the FILE and left the URL
alone. Chrome does not re-fetch a favicon because its bytes changed; it keeps a
separate favicon database keyed by URL, and a bare /favicon.svg stays cached
long after HTTP caching would have let go. The same URL means the same icon, as
far as the browser is concerned, however many times it is redeployed.

So the URL carries a hash of the content:

    /favicon.svg?v=1a2b3c4d

Change the icon, the hash changes, the URL changes, and every browser fetches
it as a thing it has never seen. tests/test_the_icon_urls_follow_the_icons.py
fails if a file and its stamp ever disagree, so the two cannot drift silently
the way the icon and the tab did.

Run it after changing any icon:  python3 tools/stamp_icons.py
"""
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = ("favicon.svg", "icon-512.png", "apple-touch-icon.png")


def stamp(name: str) -> str:
    """First 8 hex of the file's sha256 — short enough to read in View Source,
    long enough that two versions never collide in practice."""
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:8]


def href_re(name: str) -> re.Pattern:
    """Match href="/<name>" with or without an existing ?v= stamp."""
    return re.compile(r'href="/' + re.escape(name) + r'(?:\?v=[0-9a-f]+)?"')


def main() -> int:
    stamps = {n: stamp(n) for n in ICONS}
    changed = []
    for page in sorted(ROOT.glob("*.html")):
        src = page.read_text(encoding="utf-8")
        out = src
        for name, v in stamps.items():
            out = href_re(name).sub(f'href="/{name}?v={v}"', out)
        if out != src:
            page.write_text(out, encoding="utf-8")
            changed.append(page.name)
    for name, v in stamps.items():
        print(f"  {name:<22} v={v}")
    print(f"  stamped {len(changed)} page(s)" if changed else "  all pages already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
