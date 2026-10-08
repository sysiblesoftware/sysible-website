title: Sysible Linux Operations Platform
subtitle: Administrator & User Guide
version: 1.0.0
description: One URL, one certificate and one sign-in in front of the whole Sysible suite — plus the accounts, the update console, Flashback and the Visualizer.

## Overview

**Sysible Linux Operations Platform** (SLOP) is the front door to the Sysible
suite. It puts one URL, one TLS certificate and one sign-in in front of every
Sysible app on a host, and adds the pieces a platform needs once there is more
than one app on it: a user store, an update console, a config time machine and a
read-only window onto what everything has been doing.

It is deliberately thin. SLOP does not replace, fork or re-host the apps — it
fronts them. Each app is still its own container stack, still built from its own
official repository, and still works without SLOP in front of it.

What you get at `https://<server-ip>/`:

| Path | What is there |
|---|---|
| `/` | The **portal** — one card per installed app, each with a live health dot |
| `/controller/` | Sysible Controller |
| `/slep/` | Sysible Linux Engineering Platform |
| `/connect/` | Sysible Connect |
| `/flashback/` | **Flashback** — every version of every tracked config file |
| `/visualizer/` | **Visualizer** — activity, logs and fleet topology |
| `/login`, `/account` | Sign in, and change your own password |
| `/admin` | Administration — accounts, configuration, apps, software & services |

:::shot portal-signed-in
The portal: one card per app, each with a live health dot.
:::

### What SLOP is not

It is not a hypervisor, an orchestrator, or a replacement for the Controller. It
does not manage the apps' lifecycle beyond updating them — starting, stopping and
configuring a fleet is the Controller's job, and authoring automation is SLEP's.

## Requirements

- A 64-bit Linux host (x86-64 or arm64) you can reach on ports **80** and **443**.
- **Docker Engine** and the **compose** plugin. The installer sets both up if they
  are missing, via Docker's official script with a distribution-package fallback.
- **git**, to clone each app from its own repository.
- Root, or `sudo`. The installer re-executes itself under `sudo` if you forget.
- Roughly 10 GB of disk for the images, the app source checkouts and Flashback's
  history. A fleet with large config sets will want more.

There is **no DNS requirement and nothing to configure**. SLOP answers on whatever
address the host has.

## Installation

From a clone of the SLOP repository, on the host that will run it:

```sh
git clone https://github.com/sysiblesoftware/Sysible-Linux-Operations-Platform slop
cd slop
sudo ./install.sh
```

That brings up the whole stack. Three forms are accepted:

| Command | What it does |
|---|---|
| `sudo ./install.sh` | Apps **and** gateway — the whole stack |
| `sudo ./install.sh apps` | Only Controller, SLEP and Connect |
| `sudo ./install.sh gateway` | Only the gateway, portal, Flashback, Visualizer and updater |

The installer clones Controller, SLEP and Connect into `/opt/sysible-src/<repo>`
and brings each up through the suite's unified `sysiblectl` CLI — which it also
installs, so you can manage everything afterwards from one command. The gateway
comes up from the checkout you ran it in.

Nothing is re-hosted. Every app is cloned from its own official repository and
built from source on your host.

:::note
The installer mints one strong shared secret and wires it into the gateway and
every app. That secret is what makes single sign-on safe — see **Single sign-on**
below — so it is written into each app's compose `.env` and survives every later
rebuild.
:::

## First sign-in

Open `https://<server-ip>/` and you will be redirected to `/login`.

On first run SLOP creates one superuser. The username is `admin` unless you set
`SLOP_ADMIN_USER`. If you did not set `SLOP_ADMIN_PASSWORD`, a random password is
generated and written to a file inside the `idp` container, readable only by
root:

```sh
sudo docker compose exec idp cat /data/initial-password
```

The `idp` log tells you the same path, so start there if you are unsure:

```sh
sudo docker compose logs idp | head -20
```

The password itself is deliberately **not** in the log. A container log is kept
and `docker compose logs` replays it to anyone who can read it for as long as the
service lives, so "shown once" was never once. The file is deleted the first time
that account signs in.

You are required to change the password at first sign-in. To skip that — only on
a host where you set the password yourself — set `SLOP_ADMIN_FORCE_CHANGE=0`.

:::shot login
The sign-in page. One sign-in covers the portal and every app behind it.
:::

:::warn
Your browser will warn about the certificate on first visit. That is expected: by
default SLOP mints its own. See **TLS** for the three ways to resolve it, and do
resolve it — clicking through a warning every day teaches everyone to click
through warnings.
:::

## The portal

The portal is the root page. It shows one card per app, each with a live health
dot, so "is Connect up?" is answered without opening Connect.

The dots are not guesses. The portal calls **same-origin** health paths
(`/healthz/controller`, `/healthz/slep`, and so on) and the gateway proxies each to
that app's own health endpoint. Same-origin avoids every cross-domain and CORS
problem that a dashboard of links to other hosts would otherwise have.

A dot has three states: healthy, unhealthy, and still being checked. An app that
is not installed on this host is not shown as broken — it is simply absent.

## Accounts and roles

**Administration → Accounts** (`/admin`) is where users are created, roles are
set, passwords are reset and accounts are removed. It is superuser-only.

There are three roles, and they mean the same thing in every app behind SLOP:

| Role | Can |
|---|---|
| `superuser` | Everything, including managing accounts and updating software |
| `operator` | Do the work — run jobs, restore configs, change app state |
| `auditor` | Read. Nothing an auditor does changes anything |

:::role
The role is asserted by SLOP and enforced by each app independently. An auditor
cannot reach an operator's actions by going to an app directly, because the app
re-checks the role itself rather than trusting that the gateway already did.
:::

:::shot admin-accounts
Administration → Accounts: the user store, roles and password resets.
:::

### Your account

Any signed-in user can open **Your account** (`/account`) to change their own
password. Minimum length is 10 characters by default
(`SLOP_MIN_PASSWORD_LEN`). A sign-in lasts 12 hours (`SLOP_SESSION_TTL`).

Repeated failed sign-ins are throttled: 8 attempts per source in a rolling
5-minute window by default.

## Configuration

**Administration → Configuration** (`/admin/settings`) shows the settings this
SLOP is actually running with, each with a line on what it does — the bootstrap
admin, password policy, session lifetime, login throttling and the upstreams.

It is **read-only on purpose**. These are environment variables set on the
containers, so the file on disk and the running service can never disagree about
what is in effect: the page reports what the process holds, not what somebody
meant to set. To change one, edit the compose `.env` and recreate the stack.

:::shot admin-configuration
Administration → Configuration: the effective settings, and what each one does.
:::

## Apps

**Administration → Apps** (`/admin/apps`) hosts each app's own administration UI
in place, so the settings that belong to the Controller stay in the Controller
rather than being copied into a second screen that drifts out of date.

## Software & services

**Administration → Software & services** (`/admin/updates`) is the update console
for everything on the host: Controller, SLEP, Connect and SLOP itself.

Each product shows one line of state — up to date, an update available with the
two commits, or why it cannot be checked — plus whether its containers are
running. Each row offers:

- **Update now** — pull the checkout forward and rebuild its containers.
- **Update all** — every product that can be updated, in one sequential job, SLOP
  last. One product failing does not stop the rest.
- **Manage** — Restart, Stop, Start and Recreate that product's containers, so a
  wedged service can be recovered without a shell on the host.

:::shot admin-updates
Administration → Software & services: what is behind, and what can be done about it.
:::

An update is a real job with a live log. Availability is remembered for a few
minutes so that merely browsing the console does not query every git remote on
every page; **Check now** forces a fresh look.

:::note
Updating SLOP recreates the gateway and this console, so you are signed out
briefly while it rebuilds. That is why it is always updated **last** in a batch —
anything queued behind it would be killed mid-pull. The job is handed to a
detached helper so it survives the container it started in.
:::

### When an update is refused

A checkout with local modifications to tracked files is not updated, because a
pull would overwrite them. The row says so and names the command that shows
them. Untracked files — including the `.env` the installer writes — are not
local modifications and do not block anything.

If the console says an update is available and `git pull` on the host says
"Already up to date", check the path shown on the row: `SYSIBLE_<APP>_DIR` can
point somewhere other than `/opt/sysible-src/<repo>`, and the two of you may be
looking at different checkouts.

## Flashback

**Flashback** is the config time machine: every version of every tracked config
file on every host, with a diff, a download, a viewer and a one-click restore. It
ships inside the SLOP stack and is reached at `/flashback/`.

It has its own manual — see the [Sysible Flashback guide](/flashback-manual.html).

## Visualizer

**Visualizer** is the read-only window onto the platform: who did what across
every app, the logs those apps expose, and the fleet drawn as a picture. It ships
inside the SLOP stack and is reached at `/visualizer/`.

It has its own manual — see the [Sysible Visualizer guide](/visualizer-manual.html).

## The gateway and routing

There is one origin and no DNS. SLOP answers on 443 for whatever address the host
has, and everything lives on that origin addressed by **path**:

```
https://<server-ip>/              the portal
https://<server-ip>/controller/   → SLOP_CONTROLLER_UPSTREAM (host port 8800)
https://<server-ip>/slep/         → SLOP_SLEP_UPSTREAM        (host port 8810)
https://<server-ip>/connect/      → SLOP_CONNECT_UPSTREAM     (host port 8700)
https://<server-ip>/flashback/    → the flashback service
https://<server-ip>/visualizer/   → the visualizer service
```

**Why paths and not subdomains.** One origin means one session cookie and zero
DNS: no apex record, no wildcard certificate, no `/etc/hosts` entries, and it
works on a raw IP from any machine on the network. Each app is built with its
prefix as its front-end base path, so the browser asks for
`/controller/assets/...`; the gateway strips the prefix and the app sees its own
root paths, cookies and websockets unchanged.

Port 80 exists only to redirect to 443.

## TLS

Caddy owns TLS for every site, and there are three ways to run it.

**Internal CA (the default).** Caddy mints one certificate under a fixed internal
name and serves it for every raw-IP request. This is why the first visit warns.
To make the warning go away properly, export the root and trust it on the
machines that will use SLOP:

```sh
sudo docker compose cp gateway:/data/caddy/pki/authorities/local/root.crt .
```

**Public certificates.** Point a real DNS name at the host, give the `:443` site
that name and set an ACME email in the global block. Caddy fetches and renews
Let's Encrypt certificates automatically.

**Your own certificate.** Mount a certificate and key and use
`tls /path/cert.pem /path/key.pem`.

The apps keep serving their own HTTPS internally; the gateway reaches them over
the loopback interface and does not verify those internal certificates, which are
self-signed by design.

## Single sign-on

In Community Edition **SLOP owns identity**. It ships a small identity provider
with the user store, the login page and the account screens, and the apps behind
it no longer show their own login.

On every proxied request the gateway asks the IdP whether the browser is signed
in. A yes lets the request through; a no redirects to `/login?next=…` so you land
back where you were going.

### The trust boundary

Before proxying, the gateway does three things, and the order matters:

1. **Strips** any client-supplied `X-Sysible-User`, `X-Sysible-Role` and
   `X-Sysible-Auth` headers. A browser must never be able to assert who it is.
2. **Injects** the real identity from the IdP.
3. **Stamps** a shared secret proving the request came through the gateway.

Each app honours an asserted identity **only** when its trust flag is on *and*
the shared secret matches. Someone reaching an app directly cannot know the
secret, so they cannot forge the headers — and if the secret is unset the apps
**fail closed** and ignore identity headers entirely rather than trusting them.

Reaching an app directly is also made harder, separately: the installer binds
each app's console to the Docker bridge rather than to every interface, so the
gateway can reach it and the network cannot. That is not what stops a forged
identity — the secret is — but it does mean the gateway's security headers and
the IdP's login throttle cannot be skipped by going straight to `:8800`. See
**Reference: ports and paths**.

:::warn
The shared secret is the boundary that matters. Treat it like a private key: it
lives in each app's `.env` at mode 0600, and it should never be passed on a
command line, where any local user can read it out of `/proc`.
:::

## The sysiblectl CLI

Everything on the host is managed with one command. SLOP is a product like the
others:

```sh
sysiblectl status                  # every product, at a glance
sysiblectl slop restart            # restart the gateway stack
sysiblectl controller update       # pull and rebuild one product
sysiblectl update all              # everything
sysiblectl slop logs               # follow a product's logs
```

The verbs are `start`, `stop`, `restart`, `status`, `logs`, `update`, `rebuild`,
`backup` and `destroy`. `rebuild` is the one that builds images from source;
`start` will build first if a product has never been built on this host.

## Backup and data

SLOP keeps its state in named Docker volumes:

| Volume | Holds |
|---|---|
| `slop-idp-data` | The user store — accounts, roles, password hashes |
| `slop-caddy-data` | TLS certificates and the internal CA |
| `flashback-data` | Every captured config version |

The app checkouts under `/opt/sysible-src` are ordinary git clones and can be
re-cloned. The volumes cannot — back them up. `sysiblectl slop backup` captures
the stack's volumes; losing `slop-idp-data` means recreating every account, and
losing `flashback-data` means losing the config history.

## Troubleshooting

**The portal shows grey dots.** The dot means "still checking". If it stays grey,
that app's health endpoint is not answering — check `sysiblectl status` and the
app's own logs. Grey is not the same as red: red means it answered and said it
was unhealthy.

**A browser warning on every visit.** Expected with the default internal CA.
Trust the root certificate (see **TLS**) rather than clicking through.

**An app shows its own login page.** Its SSO trust flag or shared secret is
missing, so it has failed closed and fallen back to local authentication. Check
that app's `.env` for `SYSIBLE_SSO_SHARED_SECRET` and its trust flag.

**Sign-in says too many attempts.** The throttle has tripped: 8 failures per
source in 5 minutes by default. Wait it out or raise
`SLOP_LOGIN_MAX_ATTEMPTS`.

**An update will not start.** See **When an update is refused** above.

## Security model

- **One origin, one cookie.** The session cookie is host-only with no `Domain=`,
  which is both the correct cookie for a raw IP and the thing that makes a single
  sign-in cover every app.
- **The gateway is the enforcement point**, and every app re-checks the identity
  it is handed. Defence does not depend on the gateway alone.
- **Fail closed everywhere.** No shared secret means identity headers are
  ignored, not trusted. No pinned fingerprint means a vendor key is refused, not
  installed.
- **The updater holds the Docker socket**, which is root-equivalent on the host.
  It therefore accepts exactly one thing from a caller: a key from a fixed
  allowlist. It never accepts a path, a repository, a branch or a command.
- **Security headers** are set at the gateway for every response, including HSTS,
  `nosniff`, a frame policy and a referrer policy.
- **Nothing is re-hosted.** Every app is built from its own official repository on
  your host, and vendor signing keys are pinned by fingerprint — an unrecognised
  key fails the build rather than being trusted.

## Reference: ports and paths

| Port | Who | Notes |
|---|---|---|
| 80 | Gateway | Redirects to 443 |
| 443 | Gateway | The only front door on the network |
| 8800 | Controller | Its own console. Bound to the Docker bridge — see below |
| 8810 | SLEP | Its own console. Bound to the Docker bridge |
| 8700 | Connect | Its own console. Bound to the Docker bridge |
| 9000 | Controller backend | The agent/CLI API. **On every interface, by design** |

The IdP, Flashback's console, the Visualizer and the updater are **not published**
on the host at all. They are reachable only through the gateway.

The three app consoles are published, but the installer binds them to the Docker
bridge gateway address rather than to every interface — reachable from this host
and the containers on it, which is how the gateway reaches them, and not from the
network. Without that, the gateway could simply be walked around: straight to
`:8800` and its HSTS, CSP and frame headers are gone, along with the IdP's
central login throttle. Override per app with `SYSIBLE_CONTROLLER_CONSOLE_BIND`,
`SYSIBLE_SLEP_BIND` and `SYSIBLE_CONNECT_BIND` in each app's own `.env`.

Port **9000 is deliberately left on every interface**. It is the Controller's
agent and CLI API, and managed hosts across the network dial it; restricting it
would cut off every agent on the fleet.

## Reference: environment variables

Set these in the compose `.env` next to `docker-compose.yml`.

| Variable | Default | Meaning |
|---|---|---|
| `SLOP_ADMIN_USER` | `admin` | First-run superuser name |
| `SLOP_ADMIN_PASSWORD` | generated | First-run password. If unset, one is generated into `/data/initial-password` (mode 0600) in the idp container, never the log |
| `SLOP_ADMIN_FORCE_CHANGE` | `1` | Require a password change at first sign-in |
| `SLOP_MIN_PASSWORD_LEN` | `10` | Minimum password length |
| `SLOP_SESSION_TTL` | `43200` | Sign-in lifetime, in seconds (12 hours) |
| `SLOP_LOGIN_MAX_ATTEMPTS` | `8` | Failed sign-ins per source before throttling |
| `SLOP_LOGIN_WINDOW_S` | `300` | The window those failures are counted over |
| `SYSIBLE_SSO_SHARED_SECRET` | generated | Proves a request came through the gateway |
| `SLOP_CONTROLLER_UPSTREAM` | `host.docker.internal:8800` | Where the Controller is |
| `SLOP_SLEP_UPSTREAM` | `host.docker.internal:8810` | Where SLEP is |
| `SLOP_CONNECT_UPSTREAM` | `host.docker.internal:8700` | Where Connect is |
| `SYSIBLE_SRC_DIR` | `/opt/sysible-src` | Where the app checkouts live |
| `SYSIBLE_FLASHBACK_KEEP` | `50` | Versions kept per file (see the Flashback guide) |
| `SLOP_MAX_REQUEST_BYTES` | `1048576` | Largest request body the IdP accepts |
| `SYSIBLE_UPDATER_MAX_REQUEST_BYTES` | `262144` | Largest request body the updater accepts |
| `SYSIBLE_CONTROLLER_CONSOLE_BIND` | the Docker bridge | Address the Controller's console binds to |
| `SYSIBLE_SLEP_BIND` | the Docker bridge | Address SLEP's console binds to |
| `SYSIBLE_CONNECT_BIND` | the Docker bridge | Address Connect's console binds to |
