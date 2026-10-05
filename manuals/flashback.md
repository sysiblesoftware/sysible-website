title: Sysible Flashback
subtitle: Administrator & User Guide
version: 1.0.0
description: The config time machine — every version of every tracked config file on every host, with diffs, downloads and one-click restore.

## Overview

**Sysible Flashback** is the config time machine. Every host running a Sysible
agent sends its tracked configuration files in, and Flashback keeps every version
of every one of them — so the question "what did this file look like before the
change, and who changed it" has an answer that does not depend on anyone having
remembered to take a backup.

From the console you can, for any host and any file:

- read every stored version, newest first
- **view** a version in the browser
- **download** it
- **diff** any two versions of it
- **restore** a version back to the host
- **compare** the same path across the whole fleet, to find the box that drifted

Flashback ships inside the SLOP stack and is reached at
`https://<server-ip>/flashback/`. It needs no separate install.

:::shot console
The console: hosts on the left, that host's files in the middle, that file's versions beside them.
:::

For the platform it runs in — installation, accounts, TLS and single sign-on — see the [Sysible Linux Operations Platform guide](/slop-manual.html).

### What it is not

It is not a general backup system. It stores configuration files, not data
volumes, databases or whole filesystems — and it stores *changes*, not a copy per
day. For machine-level backup and restore, use the Controller's backup tooling.

## How a version gets here

Nothing is pulled. The host's agent pushes a snapshot of its tracked files, and
Flashback records a new version of a file **only when its content differs** from
that file's most recent stored version. A fleet that is not changing produces
almost no new rows, which is what makes keeping every version affordable.

The capture is driven by the Controller: it is the Controller's Flashback wiring
that tells agents what to capture and where to send it. If that wiring is
missing, no host can capture anything, and the console says so once at the top of
the hosts column rather than letting every row read as a stale agent.

:::note
If the hosts column is empty, the usual cause is that the Controller is not
pointed at Flashback — not that the agents are broken. The console distinguishes
"not wired up" from "nothing captured yet", and the wording tells you which.
:::

### Capturing on demand

You do not have to wait for the next poll. The hosts column offers:

- **Back up now** on a single host's row
- **Back up all** for the whole fleet
- **Back up selected** for the hosts you tick — the unit an operator usually
  actually wants, since environments are how fleets are run

A capture is a request, not an instruction executed inline: the host's agent
performs it on its next check-in, so rows stop saying "no backup captured yet" on
their own shortly afterwards.

## Finding things

### Hosts

Hosts are grouped by **environment**, the same grouping the rest of the suite
uses, because a flat list of opaque host identifiers tells an operator nothing
about which box they are looking at. Groups fold, and on a large fleet they start
folded.

Above the list is a filter. It matches the host name, its identifier, its address
**and its environment**, so typing `prod` finds the production group and `web`
finds the web boxes wherever they live. A match inside a folded group opens that
group rather than hiding the result.

### Files

A host here typically has several hundred to a thousand captured files, so the
files column has its own filter. Terms are space-separated and **all** must match,
in any order — `x11 session` finds `/etc/X11/Xsession` without you having to
remember how the path is spelled. The count beside the box says how many of the
total are showing.

Both filters stay pinned to the top of their column while the list scrolls, and
Escape clears either one.

:::shot file-search
Filtering a host's files: four of nine hundred, found by typing.
:::

## Reading a version

Pick a host, then a file, then a version. The versions column shows each stored
version with its timestamp, size and content hash, newest first and marked
`current`.

With a version selected you get four actions:

**View this version** renders the file in the browser. A binary file says so
rather than showing you replacement characters, and anything over 512 KB shows
its first 512 KB with a note to download the rest — a browser asked to lay out
megabytes of text stops responding.

**Download this version** gives you the exact bytes, named with the version's
short hash so two downloads of the same path do not collide.

**Restore this version** queues a restore (see below).

**Pick a second version** to diff the two. Selecting another version in the same
file turns the pane into a unified diff with additions and removals marked.

:::shot view-version
Viewing a stored version in the browser, beside the versions that came before it.
:::

:::note
A stored config is an arbitrary file off a managed host, so the viewer renders it
as **text**, never as markup. A config containing HTML or a script tag is shown as
the characters it contains and nothing is executed. That is also why the download
is served as an attachment rather than as a document the browser would render.
:::

## Restoring

**Restore this version** queues the restore and asks you to confirm first. What
happens next:

1. The restore is queued against that host, for that exact path and version.
   A version that is not a real stored version of that host and path is refused
   outright.
2. The host's agent picks it up on its next check-in.
3. The agent **backs up the file as it currently is** before overwriting it — so
   the restore is itself undoable — then writes the stored version back.
4. The agent acknowledges, and the restore shows as complete.

:::warn
A restore changes a file on a live host. It does not restart the service that
reads it: nginx will not reload because its config was restored. Plan the restart
alongside the restore.
:::

Restores are recorded. Each host's row carries its recent restores, and the audit
log records who asked for what.

## Comparing across hosts

**Compare files across hosts** answers the question an operator usually arrives
with after an incident: *this box behaves differently — is its config different?*

Pick a path that several hosts have, and Flashback shows you which hosts hold
which content for it, grouped so that identical boxes collapse together and the
odd one out is obvious. From there you can diff any two of them.

Hosts that have no stored copy of that path are listed separately rather than
silently omitted — "this host does not have this file" and "this host has it and
it matches" are different answers.

:::shot compare
Comparing one path across the fleet: the hosts that agree, and the one that does not.
:::

## Roles

Flashback uses the platform's three roles, asserted by SLOP:

| Role | Can |
|---|---|
| `superuser` | Everything, including restores |
| `operator` | Browse, view, download, diff, request captures, restore |
| `auditor` | Browse, view, download, diff — and nothing that changes a host |

An auditor sees the whole history. What an auditor does not get is the Restore
button or the capture buttons, and the API refuses those calls as well as hiding
them — the console not showing a control is a convenience, not the enforcement.

## Retention

Flashback keeps the **50 most recent versions per file** by default, set with
`SYSIBLE_FLASHBACK_KEEP`. When a file exceeds that, its oldest versions are
pruned and the content they referenced is garbage-collected if no other version
still points at it.

Because a version is only written when the content actually changed, 50 versions
of a file is 50 real changes to it, not 50 days of an unchanged file. On most
configuration this is years of history.

## Where the data lives

Everything is in the `flashback-data` Docker volume: the SQLite index and the
stored content, de-duplicated by hash so that a file identical across two hundred
hosts is stored once.

That volume is the whole product. Back it up — the app can be rebuilt from source
in minutes, and the history cannot be rebuilt at all.

## Security model

- **The console is only reachable through the gateway.** Flashback's web
  interface is not published on a host port; SLOP is the sole front door, and the
  identity it asserts is checked against the shared secret on every request.
- **The agent endpoint is separate and deliberately narrow.** Agents post
  snapshots to their own port, which is bound to the Docker bridge address rather
  than to every interface: reachable from this host and from containers on it,
  not from the network. It is authenticated with its own token
  (`SYSIBLE_FLASHBACK_AGENT_TOKEN`), distinct from any operator's session.
- **A restore cannot be used to write arbitrary content.** It names a host, a path
  and a version that Flashback already stores; anything else is refused. You
  cannot restore a file to a host that never had it, or restore content that was
  never captured.
- **Stored config is treated as hostile input** everywhere it is displayed — see
  the note under **Reading a version**.
- **Everything that changes a host is audited**, with the account that asked.

:::warn
Captured configuration frequently contains secrets: keys in `/etc/ssh`,
credentials in service configs, tokens in environment files. Flashback is
therefore as sensitive as the hosts it protects. Give `auditor` to people who
should read config history, and treat the `flashback-data` volume with the same
care as a password store.
:::

## Troubleshooting

**No hosts at all.** The Controller is not pointed at Flashback, or no agent has
checked in yet. The banner at the top of the hosts column says which.

**A host is listed but has no files.** It has been seen but has not captured yet.
Use **Back up now** on its row and give it one check-in interval.

**A file I expect is not there.** Flashback stores what the agent was told to
capture. The capture set is configured in the Controller, not here.

**"No backup captured yet" after pressing Back up now.** The request is queued for
the agent's next check-in; the console re-reads shortly afterwards. If it persists
past a couple of intervals, check that host's agent in the Controller.

**A restore was queued but nothing changed.** The agent has not checked in, or it
has and the service using the file has not been restarted. Check the host's
restore activity for the acknowledgement.

## Reference: environment variables

| Variable | Default | Meaning |
|---|---|---|
| `SYSIBLE_FLASHBACK_KEEP` | `50` | Versions kept per file before pruning |
| `SYSIBLE_FLASHBACK_DATA` | `/data` | Where the index and content live |
| `SYSIBLE_FLASHBACK_AGENT_TOKEN` | — | Token agents present when posting snapshots |
| `SYSIBLE_FLASHBACK_AGENT_BIND` | `172.17.0.1` | Address the agent endpoint binds to |
| `SYSIBLE_FLASHBACK_AGENT_PORT` | `8770` | Port the agent endpoint binds to |
| `SYSIBLE_FLASHBACK_TRUST_GATEWAY_AUTH` | `1` in SLOP | Honour the identity SLOP asserts |
| `SYSIBLE_FLASHBACK_MAX_REQUEST_BYTES` | — | Largest snapshot accepted |
