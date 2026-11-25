# Sysible brand kit

Canonical logo exports. Transparent PNGs unless noted.

| to regenerate | run |
|---|---|
| composed, text-bearing assets (company lockup, org avatar, README badges) | `node branding/render-brand.js` — edit `sysible-brand.src.html` first |
| site OG social cards | `python3 branding/render-cards.py` |

`render-brand.js --check` fails if any committed asset differs from the source,
which is the guard that was missing: this file used to say "re-render with
Chromium" without providing anything to re-render with, so the SES avatar that
went live on the GitHub org was composed by hand elsewhere and never came back
here. The committed avatar had been stale ever since. Each asset now has
exactly one owner — `render-cards.py` no longer writes the README badges.

| File | Use |
|------|-----|
| `sysible-mark.svg` | **Canonical Sysible mark** — dark rounded-square tile, thin green ring, Sora “S” + green underline. Source for every derived export. |
| `sysible-controller-mark.svg` | **Sysible Controller mark** — same tile with the hub-and-nodes topology. |
| `sysible-lockup-dark.png` | Horizontal mark + wordmark, for **dark** backgrounds (near-white text). README banners, dark UI. |
| `sysible-lockup-light.png` | Same lockup for **light** backgrounds (navy text). |
| `sysible-avatar-512.png` | Square 512×512 **mark only** on the dark ground (safe for circular crop). |
| `ses-lockup-dark.png` / `-light.png` | **The SES company lockup**, horizontal, transparent. The company mark: GitHub README banners, anywhere the company rather than a product is being named. Mirrored into `.github/sysible-logo-*.png` for this repo's own README. |
| `ses-lockup.svg` | The same lockup as vector, `currentColor` so one file serves both themes. Source for anything that can take an SVG — the site header, the generated manuals. |
| `sysible-profile-512.png` / `-1024.png` | SES lockup **stacked** on the dark ground. GitHub **org avatar** — upload the 512 by hand; an avatar is an account setting, not a file in a repo. The tagline is sized to survive GitHub's circular crop, so do not enlarge it without re-checking the crop. |
| `sysible-social-1280x640.png` | 1280×640 **Sysible** social / Open Graph card — **Enterprise Software** tagline. Mirrored at site root as `social-card.png`. |
| `sysible-controller-1280x640.png` | 1280×640 **Sysible Controller** social card — controller mark + **IT Infrastructure Management** tagline. Mirrored at site root as `controller-card.png`. |

## Marks (no hexagon)
Every product icon is a **dark rounded-square tile + a thin 2px green ring (#6ddb73)** with a glyph:
- **Sysible** → Sora SemiBold **“S”** in ink white, with a short green underline.
- **Sysible Controller** → **hub-and-nodes**: a central green hub, six satellite nodes
  (alternating white / blue), thin connector lines.

The retired hexagon / nested-core / honeycomb marks are gone. Backgrounds are
**topographic contour** fields, never honeycomb.

## Brand hierarchy
- **Sysible Enterprise Software / SES** (the company) → the SES lockup, tagline
  **Enterprise Software**. This is the mark that goes on the org, the site
  header and anything company-level.
- **Sysible** → the "S" tile, the house mark, used where a product is not being
  named specifically.
- **Sysible Controller** (the product) → tagline **IT Infrastructure Management**, hub-and-nodes mark.

## Palette (locked)
- Ink / white `#eceff3`
- **Accent green `#6ddb73`** — the one accent (rings, underlines, small elements). Older greens
  (`#63c869`, `#43a047`, `#37933f`, …) are reconciled to this.
- Secondary blue `#7aa2ff` — used sparingly (nodes, links, subtle glow); never primary.
- Field grounds `#0d1117` / `#0a0d13` (dark navy). Tile gradient `#161d29` → `#0a0d13`.
- Muted text `#8a93a0`.

## Type
- **Sora** (SIL OFL) — self-hosted from `../fonts/` (`Sora-variable.woff2`, `Sora.ttf`;
  license in `../fonts/OFL.txt`). Display / wordmark weight = **SemiBold**, tight tracking,
  uppercase for lockups with a thin green underline accent.
- Mono: `ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace`.

## Tone
Professional, engineered, restrained. Green is an accent, not a large saturated fill.
Dark, precise, topographic.
