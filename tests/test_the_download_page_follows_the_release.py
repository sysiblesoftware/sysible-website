"""The version on the download pages must follow the release, not the typist.

The site has a scheduled job that rewrites release-linux.json from the newest
Sysible Workstation release. It worked. What it did not cover was the page
TEXT, and linux.html carried its version as static markup with no id, so
nothing could ever update it:

  * release-linux.json      -> v1.0.3   (synced)
  * "Latest:" pill          -> v1.0.3   (GitHub API, at runtime)
  * the big title on /linux -> 1.0.2    (typed once, in October)

Two version numbers on one page disagreeing, the larger one wrong, for as long
as nobody happened to look. These tests pin both halves of the fix: every
version string in the markup matches the synced release, AND the title is
wired so it follows a future release on its own.

Run: pytest tests/test_the_download_page_follows_the_release.py
"""
import json
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
PAGES = ("index.html", "linux.html")


@pytest.fixture(scope="module")
def release():
    return json.loads((REPO / "release-linux.json").read_text())


def _html(name):
    return (REPO / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# the markup agrees with the synced release
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_no_page_names_a_version_that_is_not_the_release(page, release):
    """Any x.y.z in the markup must be the released one. A stale number is
    not harmless even where JS later overwrites it: it is what renders before
    the fetch returns, and what renders for good if the fetch fails."""
    want = release["version"]
    html = _html(page)
    # Only Sysible Workstation versions — not a CSS value or a third-party
    # package version that happens to look the same.
    found = set(re.findall(r"\b(\d+\.\d+\.\d+)\b", html))
    def looks_like_ours(v):
        # Near a Workstation/Ignition/fallback marker, in either order.
        return bool(
            re.search(r"(?i)(workstation|ignition|LINUX_FALLBACK|linux-pill)"
                      r"[^\n]{0,200}" + re.escape(v), html)
            or re.search(r"(?i)" + re.escape(v) + r"[^\n]{0,80}ignition", html))

    # `and` binds tighter than `or`: without these parentheses the current
    # version matched the second branch and every page "failed".
    stale = {v for v in found if v != want and looks_like_ours(v)}
    assert not stale, (
        f"{page} names Workstation version(s) {sorted(stale)} but the release "
        f"is {want} — release-linux.json is synced automatically and the page "
        f"text is not, so they drift apart silently")


@pytest.mark.parametrize("page", PAGES)
def test_the_tag_in_a_page_matches_the_release(page, release):
    html = _html(page)
    tags = set(re.findall(r'"(v\d+\.\d+\.\d+)"', html))
    bad = tags - {release["tag"]}
    assert not bad, f"{page} hard-codes {sorted(bad)}, release is {release['tag']}"


# ---------------------------------------------------------------------------
# ...and it cannot go stale again
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("page", PAGES)
def test_the_version_in_the_title_is_addressable(page):
    """The whole defect was a number nothing could reach. An id is the thing
    that makes the next release update it instead of needing an edit."""
    html = _html(page)
    title = re.search(r'<div class="p-title">Sysible Workstation\s*(<span[^>]*>)', html)
    assert title, f"{page}: the download title is not in the shape this test knows"
    assert 'id="linux-pill"' in title.group(1), (
        f"{page}: the version in the download title has no id, so nothing can "
        f"update it and it will be wrong again on the next release")


@pytest.mark.parametrize("page", PAGES)
def test_something_actually_writes_that_element(page):
    """An id nothing writes to is the same stale number with extra steps."""
    html = _html(page)
    assert re.search(r'getElementById\(\s*["\']linux-pill["\']\s*\)', html), (
        f"{page}: nothing ever writes #linux-pill, so the id is decoration")


def test_the_release_json_and_the_release_it_points_at_agree(release):
    """A sync that half-ran — a new tag with the previous release's asset URLs —
    would hand visitors download links for the old ISO under the new version."""
    tag = release["tag"]
    assert release["version"] == tag.lstrip("v")
    assert release["arches"], "no architectures in release-linux.json"
    for arch, spec in release["arches"].items():
        urls = [p["url"] for p in spec["parts"]]
        urls += [spec[k]["url"] for k in ("sums", "partsSums", "reassemble")]
        for u in urls:
            assert f"/download/{tag}/" in u, (
                f"{arch}: {u} does not point at {tag} — the page would offer "
                f"the previous release's files under the new version")
        assert len(spec["parts"]) >= 1
        assert all(p["size"] > 0 for p in spec["parts"]), f"{arch} has a 0-byte part"


def test_both_architectures_are_offered(release):
    """A release published by two separate runs can land half-done; the page
    would then quietly offer one architecture."""
    assert set(release["arches"]) == {"amd64", "arm64"}, release["arches"]
