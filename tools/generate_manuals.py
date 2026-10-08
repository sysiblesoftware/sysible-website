#!/usr/bin/env python3
"""Render the product manuals from Markdown into the site's manual template.

controller-manual.html was produced once by a `tools/generate_docs.py` that is in
no repository, so its footer credits a script nobody can run and the only way to
change the page was to edit 25KB of hand-written HTML. Three more manuals written
that way would be three more of those, drifting apart in styling the moment one
of them is touched.

So: one template here, one Markdown file per product in ../manuals, and no
dependencies. The site has no Python build step and should not gain one — this is
the standard library and nothing else, so a clone of the repo can regenerate the
manuals with no install.

    python3 tools/generate_manuals.py              # all of them
    python3 tools/generate_manuals.py slop         # just one

Screenshots are SLOTS. A manual writes

    :::shot portal-signed-in
    The portal after signing in: one card per app, each with a live health dot.
    :::

and the generator looks for manuals/shots/<product>/<slot>.png. If it is there it
is inlined as a data URI, so the page stays a single self-contained file like the
Controller's. If it is not, a dashed placeholder is drawn naming the exact file to
drop in — which is the state this ships in, and is meant to be obvious on the page
rather than a silent gap.
"""
from __future__ import annotations

import base64
import html
import mimetypes
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "manuals"
SHOTS = SRC / "shots"

# ---------------------------------------------------------------- the template
# Lifted from controller-manual.html so every manual on the site looks like the
# one that already exists, plus the .shot-slot rule the placeholders need.
CSS = """
:root{--navy:#1a2744;--blue:#2f6fed;--ink:#202733;--dim:#5b6573;--hair:#e2e6ee;
--bg:#eef1f6;--paper:#fff;--green:#2f9e44;--amber:#e0a93c;--red:#e05656;--code:#f4f6fa;}
*{box-sizing:border-box;}
@font-face{font-family:"Sora";font-style:normal;font-weight:100 800;font-display:swap;src:url("/fonts/Sora-variable.woff2") format("woff2"),url("/fonts/Sora.ttf") format("truetype");}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.6;font-size:15px;
font-family:"Sora",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.page{max-width:900px;margin:0 auto 28px;background:var(--paper);padding:52px 60px;
box-shadow:0 0 40px rgba(0,0,0,.08);}
.cover{text-align:center;padding:90px 40px;background:linear-gradient(155deg,#15352a 0%,#0f1a2e 55%,#0b0e14 100%);color:#fff;}
.cover h1{font-size:40px;margin:0 0 8px;} .cover .sub{font-size:18px;opacity:.9;}
.cover .meta{margin-top:34px;font-size:13px;opacity:.8;}
h2{color:var(--navy);border-bottom:2px solid var(--hair);padding-bottom:6px;margin-top:38px;font-size:24px;}
h3{color:var(--navy);margin-top:26px;font-size:18px;}
h4{color:var(--navy);margin:20px 0 4px;font-size:15.5px;}
a{color:var(--blue);text-decoration:none;} a:hover{text-decoration:underline;}
code{background:var(--code);border:1px solid var(--hair);border-radius:4px;padding:1px 5px;font-size:13px;}
pre{background:#1e2430;color:#e6e9ef;border-radius:8px;padding:14px 16px;overflow:auto;font-size:13px;}
pre code{background:none;border:none;color:inherit;padding:0;}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px;}
th,td{border:1px solid var(--hair);padding:8px 10px;text-align:left;vertical-align:top;}
th{background:#f6f8fc;}
.toc{columns:2;font-size:14px;} .toc a{display:block;padding:2px 0;}
.note{border-left:4px solid var(--blue);background:#f3f7ff;padding:10px 14px;border-radius:0 6px 6px 0;margin:14px 0;}
.note.warn{border-left-color:var(--amber);background:#fff9ec;}
.note.role{border-left-color:var(--green);background:#f2fbf4;}
ol li,ul li{margin:4px 0;}
.pill{display:inline-block;background:#eef2fb;color:var(--blue);border-radius:10px;padding:1px 9px;font-size:12px;font-weight:600;}
.shot{margin:18px 0;text-align:center;}
.shot img{max-width:100%;border:1px solid var(--hair);border-radius:8px;box-shadow:0 2px 14px rgba(0,0,0,.10);}
.shot figcaption{color:var(--dim);font-size:13px;margin-top:6px;}
/* An empty slot is meant to be loud: a quiet gap is one nobody fills. */
.shot-slot{border:2px dashed #c3cbdb;border-radius:8px;background:#f7f9fd;color:var(--dim);
padding:30px 18px;font-size:13px;}
.shot-slot b{display:block;color:var(--navy);font-size:14px;margin-bottom:4px;}
.shot-slot code{background:#fff;}
footer{max-width:900px;margin:0 auto 40px;text-align:center;color:var(--dim);font-size:12px;}
@media print{body{background:#fff;} .page{box-shadow:none;margin:0;} .shot-slot{display:none;}}
"""

# The real cover mark, lifted verbatim from controller-manual.html so every manual
# carries the same logo rather than an approximation of it.
MARK = '<svg viewBox="-24 -26 48 52" width="96" height="104" role="img" aria-label="Sysible"><defs><linearGradient id="tgCover" x1="0" y1="-25" x2="0" y2="25" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#161d29"/><stop offset="1" stop-color="#0a0d13"/></linearGradient></defs><rect x="-23" y="-25" width="46" height="50" rx="12" fill="url(#tgCover)"/><rect x="-21.8" y="-23.8" width="43.6" height="47.6" rx="10.6" fill="none" stroke="#6ddb73" stroke-width="1.6"/><path transform="translate(-13.124 11.274) scale(0.039 -0.039)" d="M338.5 -19Q242 -19 175.25 12.0Q108.5 43 73.75 97.25Q39 151.5 39 221H178Q178 191.5 194.0 164.25Q210 137 245.25 120.0Q280.5 103 338.5 103Q391 103 425.75 117.75Q460.5 132.5 477.75 157.25Q495 182 495 213Q495 251.5 462.0 275.0Q429 298.5 359.5 304.5L295.5 310Q190.5 319 128.0 375.5Q65.5 432 65.5 525Q65.5 594.5 98.5 645.0Q131.5 695.5 191.0 723.25Q250.5 751 330.5 751Q413.5 751 473.75 722.0Q534 693 566.75 640.5Q599.5 588 599.5 517H460.5Q460.5 546.5 446.25 572.0Q432 597.5 403.25 613.25Q374.5 629 330.5 629Q288.5 629 260.5 614.75Q232.5 600.5 218.5 576.75Q204.5 553 204.5 525Q204.5 491 229.5 465.5Q254.5 440 308.5 435.5L372.5 430Q451 423.5 509.75 396.5Q568.5 369.5 601.25 323.75Q634 278 634 213Q634 144 597.75 91.5Q561.5 39 495.25 10.0Q429 -19 338.5 -19Z" fill="#eceff3"/><rect x="-11" y="15.4" width="22" height="2.9" rx="1.45" fill="#6ddb73"/></svg>'


# --------------------------------------------------------------------- inline
def _inline(text: str) -> str:
    """Inline Markdown. Code spans are extracted FIRST and put back last, so a
    `*` or `_` inside `code` is never read as emphasis."""
    spans: list[str] = []

    def stash(m):
        spans.append(html.escape(m.group(1)))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # Single asterisks too. Four places in the manuals had been written in plain
    # Markdown's *emphasis* and were coming out as literal asterisks in the
    # published HTML, which is the sort of thing nobody re-reads a shipped manual
    # to find. ** is consumed above, so nothing here can see a bold marker; the
    # boundary guards stop a lone asterisk eating the rest of a paragraph.
    text = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<i>\1</i>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{spans[int(m.group(1))]}</code>", text)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-")
    return s or "section"


def _shot(product: str, slot: str, caption: str) -> str:
    """A screenshot, or a loud placeholder naming the file that would fill it."""
    cap = _inline(caption)
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        f = SHOTS / product / (slot + ext)
        if f.is_file():
            mime = mimetypes.guess_type(f.name)[0] or "image/png"
            data = base64.b64encode(f.read_bytes()).decode("ascii")
            return (f'<figure class="shot" data-shot="{html.escape(slot)}">'
                    f'<img alt="{cap}" src="data:{mime};base64,{data}"/>'
                    f"<figcaption>{cap}</figcaption></figure>")
    rel = f"manuals/shots/{product}/{slot}.png"
    # No figcaption here: the caption is already inside the placeholder, and
    # printing it twice reads as two different things to look at.
    return (f'<figure class="shot" data-shot="{html.escape(slot)}">'
            f'<div class="shot-slot"><b>Screenshot to come</b>{cap}<br><br>'
            f"Drop it at <code>{rel}</code> and re-run "
            f"<code>python3 tools/generate_manuals.py {product}</code>.</div>"
            f"</figure>")


# ---------------------------------------------------------------------- blocks
def render(md: str, product: str) -> tuple[str, list[tuple[str, str]]]:
    """Markdown subset -> (html, [(anchor, title)] for the contents list)."""
    out: list[str] = []
    toc: list[tuple[str, str]] = []
    lines = md.split("\n")
    i, n = 0, len(lines)
    list_stack: list[str] = []

    def close_lists(to: int = 0):
        while len(list_stack) > to:
            out.append(f"</{list_stack.pop()}>")

    while i < n:
        line = lines[i]

        # fenced code
        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            body = []
            while i < n and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            close_lists()
            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(body))}</code></pre>")
            continue

        # ::: blocks — shot / note / warn / role
        m = re.match(r"^:::\s*(shot|note|warn|role)\s*(.*)$", line)
        if m:
            kind, arg = m.group(1), m.group(2).strip()
            i += 1
            body = []
            while i < n and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            i += 1
            close_lists()
            text = " ".join(x.strip() for x in body).strip()
            if kind == "shot":
                out.append(_shot(product, arg or _slug(text)[:40], text))
            else:
                cls = "note" if kind == "note" else f"note {kind}"
                out.append(f'<div class="{cls}">{_inline(text)}</div>')
            continue

        # tables
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            close_lists()
            def cells(row):
                return [c.strip() for c in row.strip().strip("|").split("|")]
            head = cells(line)
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(cells(lines[i]))
                i += 1
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{_inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
                                 for r in rows)
                       + "</tbody></table>")
            continue

        # headings
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            close_lists()
            level, title = len(m.group(1)), m.group(2).strip()
            anchor = _slug(title)
            if level == 2:
                toc.append((anchor, title))
                out.append(f'<h2 id="{anchor}">{_inline(title)}</h2>')
            else:
                out.append(f'<h{level} id="{anchor}">{_inline(title)}</h{level}>')
            i += 1
            continue

        # lists (one level of nesting is plenty for a manual)
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            depth = 1 if len(m.group(1)) >= 2 else 0
            tag = "ul" if m.group(2) in ("-", "*") else "ol"
            while len(list_stack) > depth + 1:
                out.append(f"</{list_stack.pop()}>")
            if len(list_stack) == depth + 1 and list_stack[depth] != tag:
                out.append(f"</{list_stack.pop()}>")
            if len(list_stack) <= depth:
                out.append(f"<{tag}>")
                list_stack.append(tag)
            out.append(f"<li>{_inline(m.group(3))}</li>")
            i += 1
            continue

        if not line.strip():
            close_lists()
            i += 1
            continue

        # paragraph
        close_lists()
        para = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(
                r"^(#{2,4}\s|```|:::|\s*([-*]|\d+\.)\s)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append(f"<p>{_inline(' '.join(x.strip() for x in para))}</p>")

    close_lists()
    return "\n".join(out), toc


def meta_of(md: str) -> tuple[dict, str]:
    """Leading `key: value` lines, then a blank line, then the body."""
    meta, lines = {}, md.split("\n")
    i = 0
    while i < len(lines) and lines[i].strip() and ":" in lines[i] and not lines[i].startswith("#"):
        k, v = lines[i].split(":", 1)
        meta[k.strip().lower()] = v.strip()
        i += 1
    return meta, "\n".join(lines[i:]).lstrip("\n")


def build(path: Path) -> Path:
    product = path.stem
    meta, body = meta_of(path.read_text(encoding="utf-8"))
    html_body, toc = render(body, product)
    title = meta.get("title", product.title())
    sub = meta.get("subtitle", "Administrator & User Guide")
    version = meta.get("version", "1.0.0")
    stamp = meta.get("date", date.today().isoformat())

    # Numbered, so the contents and the headings agree without the author
    # maintaining two lists that drift.
    # Two authoring mistakes that render as something subtly wrong rather than
    # failing, so they are worth saying out loud at build time.
    for _a, t in toc:
        if re.match(r"^\d+[.)]\s", t):
            print(f"  ! {product}: section {t!r} is numbered by hand — the generator "
                  f"numbers them, so this will render as '1. 1. …'", file=sys.stderr)
    slots = re.findall(r'data-shot="([^"]+)"', html_body)
    for dup in {x for x in slots if slots.count(x) > 1}:
        print(f"  ! {product}: two screenshot slots are both called {dup!r} — "
              f"one image cannot fill both", file=sys.stderr)

    toc_html = "".join(
        f'<a href="#{a}">{idx}. {html.escape(t)}</a>' for idx, (a, t) in enumerate(toc, 1))
    numbered = html_body
    for idx, (a, t) in enumerate(toc, 1):
        numbered = numbered.replace(f'<h2 id="{a}">', f'<h2 id="{a}">{idx}. ', 1)

    out = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
        f"<title>{html.escape(title)} — {html.escape(sub)}</title>"
        '<link rel="icon" type="image/svg+xml" href="/favicon.svg">'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta name="description" content="{html.escape(meta.get("description", title))}">'
        f"<style>{CSS}</style></head><body>"
        f'<div class="cover"><span class="cover-mark">{MARK}</span>'
        f'<h1>{html.escape(title)}</h1><div class="sub">{html.escape(sub)}</div>'
        f'<div class="meta">Version {html.escape(version)} · {html.escape(stamp)}</div></div>'
        f'<div class="page"><h2>Contents</h2><div class="toc">{toc_html}</div></div>'
        f'<div class="page">{numbered}</div>'
        f'<footer>{html.escape(title)} v{html.escape(version)} — generated {stamp} by '
        "tools/generate_manuals.py<div style=\"margin-top:14px;opacity:.8\">The Sysible Linux "
        "platforms are products of <b>Sysible Enterprise&nbsp;Software</b> (SES).</div>"
        "</footer></body></html>"
    )
    dest = ROOT / f"{product}-manual.html"
    dest.write_text(out, encoding="utf-8")
    return dest


def main(argv: list[str]) -> int:
    wanted = argv[1:]
    srcs = sorted(SRC.glob("*.md"))
    srcs = [p for p in srcs if p.stem != "README"]
    if wanted:
        srcs = [p for p in srcs if p.stem in wanted]
        if not srcs:
            print(f"no manual named {wanted} in {SRC}", file=sys.stderr)
            return 2
    for p in srcs:
        dest = build(p)
        # The CLASS, not the string: "shot-slot" also appears four times in the
        # stylesheet, which made a manual with five empty slots report nine.
        missing = dest.read_text(encoding="utf-8").count('<div class="shot-slot">')
        note = f" ({missing} screenshot slot(s) still empty)" if missing else ""
        print(f"  {p.name} -> {dest.name}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
