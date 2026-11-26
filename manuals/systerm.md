title: SysTerm
subtitle: User & Installation Guide
version: 0.1.0
description: The Sysible terminal — a native GTK and VTE tiling terminal with splits, tabs and broadcast typing across every pane at once.

## Overview

**SysTerm** is a tiling terminal for Debian-based systems, in the spirit of
Terminator: split a window into as many shell panes as you like, arrange them in
tabs, and **broadcast** your typing to every pane at once.

It is built on **GTK 3** and **VTE** — the same widget GNOME Terminal and
Terminator use — so the terminal core is not reinvented. PTY handling, escape
sequences, rendering, URL detection and scrollback are VTE's, battle-tested and
familiar. What SysTerm adds is the tiling, the tabs, the broadcast and the
configuration.

It ships on **Sysible Workstation** and runs anywhere GTK does.

:::note
SysTerm is **v0.1** and usable daily. Splits, tabs, broadcast, per-pane font
zoom, pane zoom, configurable keys and the profile all work. See **Roadmap** for
what is not there yet.
:::

SysTerm is MIT licensed.

## Requirements

| | |
|---|---|
| Display | An X11 or Wayland session — it is a GUI application |
| Python | python3 |
| Bindings | `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-vte-2.91` |

The GTK and VTE bindings are **system packages, not pip wheels**. They cannot be
installed from PyPI, which is why every install route below goes through the
distribution's package manager.

## Installation: the installer script

The repository ships an `install.sh` that maps dependencies per package manager
— `apt`, `dnf`, `pacman`, `zypper` — and works on Debian, Ubuntu, Fedora, Arch
and openSUSE. It installs the runtime dependencies, SysTerm itself, and the
desktop entry and icons.

```sh
git clone https://github.com/sysiblesoftware/SysTerm systerm
cd systerm
sudo ./install.sh
```

| Form | What it does |
|---|---|
| `sudo ./install.sh` | Install system-wide |
| `./install.sh --user` | Install under `~/.local`, no root needed |
| `sudo ./install.sh --uninstall` | Remove it again |

The installer puts SysTerm in as a plain module plus a launcher, so no pip is
involved at all.

:::warn
The project's README also offers a one-line `curl … | sh` form. This guide does
not reproduce it. That URL fetches a script from a **branch** — mutable,
unsigned, and whatever it holds at the moment you run it — and pipes it straight
into a shell. Clone the repository and read `install.sh` before running it, on
any machine that matters.
:::

## Installation: a Debian package

This is the cleanest route on Debian and Ubuntu. A `debian/` directory ships in
the repository, so a proper `.deb` can be built. It pulls the GTK and VTE
dependencies automatically and registers the desktop entry and icon for you,
cache refresh included.

```sh
sudo apt install build-essential debhelper dh-python pybuild-plugin-pyproject
dpkg-buildpackage -us -uc -b        # produces ../systerm_0.1.0_all.deb
sudo apt install ../systerm_0.1.0_all.deb
```

`systerm` is then on `PATH`, appears in the application menu with its icon, and
removes cleanly with `sudo apt remove systerm`.

:::note
On **Sysible Workstation** none of this is needed — SysTerm is already installed.
:::

## Installation: from source

Install the bindings, then run it in place:

```sh
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
git clone https://github.com/sysiblesoftware/SysTerm systerm
cd systerm
python3 -m systerm
```

Running in place needs no install at all — there are no pip dependencies.

To get a `systerm` command without a system package, use **pipx**.
`--system-site-packages` is what lets its virtualenv import the system GTK and
VTE bindings:

```sh
sudo apt install pipx
pipx install --system-site-packages .
install -Dm644 data/systerm.desktop ~/.local/share/applications/systerm.desktop
cp -r data/icons/hicolor ~/.local/share/icons/
update-desktop-database ~/.local/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true
```

:::warn
**Not** `pip install --user .`. Debian 12 and Python 3.11 onwards mark the system
interpreter *externally managed* (PEP 668), so pip refuses with
`error: externally-managed-environment`. Use pipx, or a
`python3 -m venv --system-site-packages` you install into.
:::

## Running it

Launch `systerm` from the application menu, or run `systerm` or
`python3 -m systerm` from a shell. You start with one shell pane.

Once the desktop entry is installed, SysTerm is a normal standalone application:
launch it from Activities, pin it to the dock, or bind `systerm` to a keyboard
shortcut in your desktop settings. You never need another terminal to start it —
running `python3 -m systerm` is only a from-source convenience.

## Panes and splits

A **pane** is one shell. Split the current pane and the space divides between the
old pane and a new one.

| Action | Shortcut |
|---|---|
| Split horizontal — top and bottom | `Ctrl+Shift+O` |
| Split vertical — side by side | `Ctrl+Shift+E` |
| Close pane | `Ctrl+Shift+W` |
| Cycle pane focus | `Ctrl+Shift+→` / `Ctrl+Shift+←` |
| Zoom pane to fill the tab (toggle) | `Ctrl+Shift+X` |

**Zoom** is a toggle, not a new window: the focused pane expands to fill the tab
and the others are hidden until you press it again. It is for reading a long
build log in a layout you do not want to disturb.

Splits nest, so a pane can be split again and again to build the layout you want.

## Tabs and windows

| Action | Shortcut |
|---|---|
| New tab | `Ctrl+Shift+T` |
| Close tab | `Ctrl+Shift+Q` |
| Next / previous tab | `Ctrl+PageDown` / `Ctrl+PageUp` |
| New window | `Ctrl+Shift+N` |

Each tab holds its own pane layout. Broadcast is scoped to the **window**, so
tabs are a way to keep a set of panes out of a broadcast.

## Broadcast

This is the feature SysTerm exists for.

Press **`Ctrl+Shift+B`** and the window gains an **amber frame**. Every keystroke
now goes to *every pane in the window* at once — run the same command across a
row of `ssh` sessions, upgrade a dozen machines in one go, tail the same file on
every node. Press it again to disarm.

:::warn
The amber border is the safety cue. While it is showing, every pane receives
everything you type — including `rm`, including a password typed into the one
pane you thought was focused. Check for the frame before typing anything
destructive, and disarm as soon as you are done.
:::

Broadcast goes to all panes in the current window. Broadcasting to a chosen
subset is on the roadmap; for now, put panes you want excluded in another tab or
another window.

## Font size and appearance

| Action | Shortcut |
|---|---|
| Font bigger | `Ctrl++` |
| Font smaller | `Ctrl+-` |
| Reset font | `Ctrl+0` |

Zoom is **per pane**, so one pane can be enlarged for a log while the rest stay
as they were.

## The context menu

**Right-click any pane** for the same actions as the shortcuts — Split
Horizontally, Split Vertically, Open Tab, Open Window, Copy, Paste, Zoom,
Broadcast and Close — each listed with its keyboard shortcut, so the menu
doubles as a reminder of the bindings.

## Reference: default keybindings

| Action | Shortcut |
|---|---|
| Split horizontal (top/bottom) | `Ctrl+Shift+O` |
| Split vertical (side by side) | `Ctrl+Shift+E` |
| New tab | `Ctrl+Shift+T` |
| New window | `Ctrl+Shift+N` |
| Close pane | `Ctrl+Shift+W` |
| Close tab | `Ctrl+Shift+Q` |
| Copy | `Ctrl+Shift+C` |
| Paste | `Ctrl+Shift+V` |
| Next tab | `Ctrl+PageDown` |
| Previous tab | `Ctrl+PageUp` |
| Cycle pane focus | `Ctrl+Shift+→` / `Ctrl+Shift+←` |
| Zoom pane to fill tab (toggle) | `Ctrl+Shift+X` |
| **Broadcast to all panes (toggle)** | `Ctrl+Shift+B` |
| Font bigger / smaller / reset | `Ctrl++` / `Ctrl+-` / `Ctrl+0` |

Copy and paste are `Ctrl+Shift+C` and `Ctrl+Shift+V` because plain `Ctrl+C` has
to keep meaning SIGINT in a terminal.

## Configuration

On first run SysTerm writes a commented default to
`~/.config/systerm/config.ini`. Edit it and **restart** to apply — configuration
is file-only for now; a preferences UI is on the roadmap.

```ini
[profile]
font = Monospace 12
background = #141414
foreground = #d0d0d0
scrollback_lines = 20000

[keys]
toggle-broadcast = <Primary><Shift>a
```

| Section | What it sets |
|---|---|
| `[profile]` | Font, background and foreground colours, scrollback depth, cursor |
| `[keys]` | Any binding, in GTK accelerator syntax |

In GTK accelerator syntax `<Primary>` means Ctrl, so the example above rebinds
broadcast to `Ctrl+Shift+A`. Every action in the keybindings table can be
rebound the same way.

## Troubleshooting

**The icon does not show in the application menu.** Two usual causes.

1. **Menu cache.** Re-run the two cache commands from the pipx install above,
   then log out and back in — or `killall -HUP gnome-shell` on X11. New entries
   rarely appear live.
2. **No SVG loader.** GTK renders themed icons through gdk-pixbuf, and without
   `librsvg2-common` an SVG icon silently fails. SysTerm ships **PNG** icons from
   16 to 256 px as well as the SVG for exactly this reason, so the raster icon
   resolves even with no SVG loader. Check with
   `gdk-pixbuf-query-loaders | grep -qi svg` if you want the scalable one too.

**`error: externally-managed-environment`.** You used `pip install`. See the
warning under **Installation: from source** — use pipx or a venv.

**`ModuleNotFoundError: gi`.** The GTK bindings are missing, or you are in a
virtualenv that cannot see system packages. Install `python3-gi`,
`gir1.2-gtk-3.0` and `gir1.2-vte-2.91`, and create virtualenvs with
`--system-site-packages`.

**I typed into one pane and it went everywhere.** Broadcast was armed. Look for
the amber frame; `Ctrl+Shift+B` disarms it.

**A config change did nothing.** Configuration is read at start. Restart SysTerm.

## Security notes

- **Broadcast is indiscriminate.** While armed, every pane in the window receives
  every keystroke, including secrets. The amber frame is the only indication —
  make a habit of checking for it.
- **Scrollback holds whatever scrolled past**, including anything a command
  printed. `scrollback_lines` controls how much is kept.
- **The one-line installer pipes a remote script into a shell.** Prefer the
  Debian package or a checkout you have read on any machine that matters.
- SysTerm runs as your user with no elevated privileges of its own. A shell in a
  pane has exactly the rights you do.

## Roadmap

Not yet present, and listed so the gaps are explicit rather than discovered:

- Directional focus with `Alt`+arrows, and drag-to-resize handles.
- Saved layouts and named profiles.
- A preferences UI — configuration is file-only today.
- Session groups: broadcast to a *subset* of panes rather than all.
- An optional C and VTE port for a leaner single binary.

## Reference: files and paths

| Path | What it is |
|---|---|
| `~/.config/systerm/config.ini` | Your configuration, written with comments on first run |
| `data/systerm.desktop` | The desktop entry, in the repository |
| `data/icons/hicolor/` | Icons, PNG from 16 to 256 px plus an SVG |
| `debian/` | Packaging rules for building a `.deb` |

## Reference: commands

| Command | What it does |
|---|---|
| `systerm` | Launch it |
| `python3 -m systerm` | Launch from a checkout, with nothing installed |
| `sudo ./install.sh` | Install system-wide |
| `./install.sh --user` | Install under `~/.local`, no root |
| `sudo ./install.sh --uninstall` | Remove it |
| `sudo apt remove systerm` | Remove the Debian package |
