title: Sysible Visualizer
subtitle: Administrator & User Guide
version: 1.0.0
description: The read-only window onto the platform — who did what across every app, the logs those apps expose, and the fleet drawn as a picture.

## Overview

**Sysible Visualizer** is the read-only window onto everything else. It answers
three questions that no single app can answer on its own, because each app only
knows about itself:

- **Activity** — who did what, across every app on this platform
- **Logs** — the run and service logs those apps expose, read in place
- **Fleet Topology** — the fleet drawn as a picture

It ships inside the SLOP stack and is reached at
`https://<server-ip>/visualizer/`.

:::shot home
The Visualizer home: three views, chosen rather than hunted for.
:::

For the platform it runs in — installation, accounts, TLS and single sign-on — see the [Sysible Linux Operations Platform guide](/slop-manual.html).

### It stores nothing

This is the most important thing to know about it. Visualizer has no database and
no volume. Every record it shows is fetched live from the app that owns it, at the
moment you ask, **using your own identity** — so each app applies its own role
rules to you rather than to the Visualizer.

Two consequences follow, and both are deliberate:

- There is no second copy of your audit trail to secure, to back up, or to drift
  out of agreement with the original.
- An auditor and a superuser looking at the same screen may see different rows,
  because the upstream apps answered each of them differently. That is correct.

:::note
Visualizer changes nothing. There is no button in it that alters a host, a job or
an account. If you need to act on what you find, the row tells you which app owns
it and the topology links hosts straight into the Controller.
:::

## Activity

Activity is one tab per app — Controller, SLEP, Connect and Flashback — showing a
normalised feed: when, who, what source, what action, against what, with detail.

### Sources

Every event carries a source, and the chips above the table filter by it:

| Chip | Means |
|---|---|
| **People** | A named human did this |
| **API** | A key-authenticated caller did this, with no person behind it |
| **Automation** | An app's own scheduled or background work |

The counts on the chips are of what the table can actually show, so they always
add up to what is in front of you — a chip reading zero means "nothing of that
kind here", never "your search hid it".

### Routine fleet sweeps

The Controller runs a posture sweep and a package-update check against **every
host on a timer**. On a fleet of any size those are not the majority of the
activity feed — they are effectively all of it, one row per host per cycle, each
carrying its full shell command.

So they are folded away by default, and a **Routine** toggle beside the chips
says how many are hidden. One press brings them back.

Nothing is discarded: the count is always visible, and a feed that happens to be
entirely routine says so rather than looking empty. The same action performed by a
*person* is never treated as routine — that is the most interesting row on the
page, not the least.

:::shot activity
Activity with the routine sweeps folded away: three real actions instead of ninety-six.
:::

### Searching and limits

The search box filters the rows the current app returned, across actor, action,
target and detail. The row limit (100, 250 or 500) is how many rows are fetched
from the app; raising it asks the app for more history.

## Logs

Where an app exposes a log — SLEP's run logs, the Controller's own service log —
Visualizer reads it in place rather than making you go and find it. Open a row's
log from Activity and it appears alongside the feed, so you keep the context of
what you were reading.

Logs are fetched live and never stored here.

## Fleet Topology

Fleet Topology draws the fleet as a graph. It is the Controller's network topology
view, rebuilt here so it sits beside the activity that explains it.

:::shot topology
Fleet Topology: hosts grouped by environment, with posture overlaid.
:::

### The two lenses

**Environment** groups hosts the way your fleet is actually organised — production,
staging, lab. This is the default, and it is the one that matches how work is
assigned.

**Network** groups by what the hosts are attached to: subnets, gateways and the
paths between them. This is the lens for "why can this box not reach that one".

### Posture

Posture is an overlay, not a third lens. The map paints immediately without it and
the posture sweep is layered on once it returns — a whole-fleet posture query is
expensive, and a map that waits for it is a map that looks broken for several
seconds.

With posture on, hosts carrying critical findings are ringed and gateways are
labelled, so "which of these needs attention" is answered without reading a list.

### Working with the map

- **Collapse all / Expand all** fold the groups, which is what makes a
  several-hundred-host fleet legible.
- **Zoom in / out**, and **fit**, which also resets any node you have dragged.
- Nodes can be dragged; the layout remembers where you put them.
- **Auto** refreshes the map every ten seconds. It only polls while you are
  looking at the topology — leaving the view stops it.
- **Clicking a host opens it in the Controller**, which is where you can actually
  do something about it.

## Roles

Visualizer uses the platform's three roles, and every one of them may view it —
including `auditor`, because read-only oversight is exactly what this is for.

What differs is not the Visualizer's permissions but the upstream apps'. The
Visualizer forwards your identity on every fetch, so what you can see here is
precisely what you could see in each app directly. It cannot show you more, and
it does not try.

## When an app cannot be read

One app being unreachable does not break the console. The affected tab says what
failed and why, and the other tabs carry on working — a dashboard that goes blank
because one of four upstreams timed out is worse than no dashboard.

An app that reports nothing and an app that could not be reached are shown
differently, on purpose: the first is a quiet, healthy fleet and the second is a
problem.

## Security model

- **Read-only by construction.** There is no write path. The service exposes
  nothing that changes any other app's state.
- **Stateless.** No database, no volume, no cached copy of anybody's audit trail.
- **Your identity, not its own.** Every upstream fetch carries the caller's
  forwarded identity, so each app enforces its own rules. The Visualizer holds no
  privileged credential that could be used to read more than the caller may.
- **Reachable only through the gateway.** It is not published on a host port, and
  it honours an asserted identity only when the gateway's shared secret matches.
  Without that secret it fails closed.
- **Limits are enforced**, on the row count and the request size, so a caller
  cannot turn the console into a way to pull an app's entire history in one go.

## Troubleshooting

**A tab says it could not read an app.** That app is down, or its upstream address
is wrong. Check the portal's health dot for it and `sysiblectl status`.

**An app's tab is empty but healthy.** It has recorded nothing. The empty state
distinguishes this from a failed read — read the wording.

**Everything is "Automation" and nothing else.** That is the routine sweeps. They
are folded by default; if you are seeing them, the Routine toggle is on.

**The topology is empty.** It comes from the Controller. If the Controller cannot
be read, neither can the map.

**The map is slow to show posture.** By design — the graph paints first and the
posture sweep overlays when it returns.

## Reference: environment variables

| Variable | Default | Meaning |
|---|---|---|
| `SYSIBLE_VISUALIZER_TRUST_GATEWAY_AUTH` | `1` in SLOP | Honour the identity SLOP asserts |
| `SYSIBLE_SSO_SHARED_SECRET` | from install | Proves a request came through the gateway |
| `SLOP_CONTROLLER_UPSTREAM` | `host.docker.internal:8800` | Where to read the Controller's activity |
| `SLOP_SLEP_UPSTREAM` | `host.docker.internal:8810` | Where to read SLEP's activity |
| `SLOP_CONNECT_UPSTREAM` | `host.docker.internal:8700` | Where to read Connect's activity |
| `SLOP_FLASHBACK_UPSTREAM` | `flashback:8080` | Where to read Flashback's audit |
| `SYSIBLE_VISUALIZER_MAX_LIMIT` | — | Largest row count a caller may request |
| `SYSIBLE_VISUALIZER_TIMEOUT_S` | — | How long to wait on an upstream app |
| `SYSIBLE_VISUALIZER_LOCAL_USER` | `local` | Identity used in standalone mode only |
