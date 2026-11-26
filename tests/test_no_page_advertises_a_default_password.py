"""The site must not claim the image ships a default password. It does not.

Three places said the login was `sysible` / `sysible` and that it "works for
both the live session and the installed system". Checked against the
Workstation image:

  * 9100-sysible-users.hook.chroot creates `sysible` with NO password hash and
    then LOCKS it, with the comment "never bake a documented static password
    into the shipped image". `passwd -l` writes '!', which no password matches.
  * The live session reaches the desktop through live-config's GDM autologin
    (username=sysible in auto/config --bootappend-live), which needs no
    credential at all.
  * root ships locked; Calamares' setRootPassword owns root on the target.
  * 9200-sysible-calamares-removeuser.hook.chroot deletes `sysible` from the
    INSTALLED system once the operator's own account exists.

So the copy was wrong twice over: the password it printed would not have
worked, and it advertised a default-credential weakness that the engineers had
deliberately designed out. That is the expensive kind of wrong on a page whose
readers are sysadmins.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob("*.html"))

# "sysible / sysible" in any markup, and "default login/password ... sysible".
CLAIMS = (
    re.compile(r"sysible\s*</(?:code|span|b)>\s*/\s*<(?:code|span|b)[^>]*>\s*sysible", re.I),
    re.compile(r"sysible\s*/\s*sysible", re.I),
    re.compile(r"default\s+(?:login|password|credential)[^.]{0,120}?password[^.]{0,40}?sysible", re.I),
)


def test_there_are_pages_to_check():
    assert len(PAGES) >= 8, f"only found {len(PAGES)} pages — the glob is wrong"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_no_default_password_is_advertised(page):
    text = page.read_text(encoding="utf-8")
    for rx in CLAIMS:
        m = rx.search(text)
        assert not m, (
            f"{page.name} advertises a default password: {m.group(0)[:90]!r}\n"
            f"The image ships `sysible` LOCKED with no password hash; the live "
            f"session uses GDM autologin and the account is removed on install.")
