title: Sysible Baseline
subtitle: Administrator & User Guide
version: 1.0.0
description: Desired-state configuration for the fleet — declare what each host must look like, apply it with Salt, and choose what happens when something changes.

## Overview

**Sysible Baseline** is where you declare what a host's configuration must be.
You write the declaration as a Salt state, assign it to hosts or to a whole
environment, and Baseline keeps those hosts matching it — reporting what it had
to change, and running whatever you asked to happen afterwards.

Baseline ships inside the SLOP stack and is reached at
`https://<server-ip>/baseline/`. It needs no separate install.

:::note
**Baseline and Flashback are two different products, and the difference is the
point.** Baseline declares what a host *must be*; [Sysible
Flashback](/flashback-manual.html) records what it *actually is*. They have
separate consoles, separate stores and separate credentials, deliberately — the
declaration and the observation have to be able to disagree, or neither is worth
reading. When they do disagree, that is drift, and it is the thing you want to
see.
:::

### What it is not

It is not a general automation runner. One-off jobs, provisioning and anything
that happens *once* belong in the [Sysible Linux Engineering
Platform](/slep) — SLEP builds and provisions, Baseline keeps.
Configuration state was removed from SLEP for exactly this reason: two products
both claiming a host's configuration is a disagreement waiting to happen.

## How a state reaches a host

Baseline is **masterless**. There is no Salt master, your hosts run no minion
daemon, and nothing new listens on the network.

When a host is due, the Controller asks Baseline what that host must look like.
Baseline returns the state and a `salt-call --local` command. The Controller
runs it over the channel it already has to that host's agent, and posts the
output back. Baseline reads the result and decides what follows.

:::note
This matters for what you have to operate. No second daemon per host, no second
port, no second set of keys to accept and rotate, and nothing that can be
offline while this console still calls a host "managed". The Controller remains
the only thing that talks to your fleet.
:::

The trade, stated plainly: `--local` means a host can only reason about itself.
There is no Salt mine, no peer publishing and no master-side pillar. Baseline's
question is "must this host look like this", which `--local` answers completely.

:::shot console
The console: declared states, what drifted, and what fires when it does.
:::

## Declaring a state

A state is a **list of things that must be true** about a host. You pick what to
add, fill in a few fields, and Baseline writes the Salt state for you — you do
not have to know that the key is `pkg.installed` rather than `pkg.install`, or
which arguments take a list.

| Add | What it makes true |
| --- | --- |
| Packages installed / removed | The named packages are present, or are not |
| Service running / stopped | Started now and on at boot, or stopped and off |
| File with this content | The file is created or rewritten to match exactly |
| Directory exists | With an owner, group and mode if you give them |
| Line present in a file | That line is there; the rest of the file is untouched |
| User account, Group | The account exists, with its groups, shell and home |
| Kernel parameter (sysctl) | The parameter has that value |
| Scheduled command (cron) | The job is in that user's crontab |
| Run a command | With a guard, so it does not run on every apply |

The order of the list is the order the host is changed in, so "install it, then
start it" means putting the package above the service. Items can be moved and
removed.

### Writing your own Salt state

The builder is not the only way in. **New state → YAML** gives you an empty
editor: write or paste any Salt SLS and save it. Nothing is generated and
nothing is converted — it is stored exactly as typed, and reopening it gives
you the same editor back.

Use it for anything the builder does not cover, including states that depend on
a Salt file server, Jinja templating, requisites, or modules this console does
not list.

### The YAML view of a built state

A state built from a list also has a **YAML** view, showing the Salt SLS that
list produces. It is read-only there, because the list is what gets saved — and
what you read is the exact string the fleet runs, fetched from the same place
the save uses.

If you want to take such a state over, **Edit this YAML by hand** does it: from
the next version on it is whatever you type. That switch is one-way for the
state going forward, because reading SLS back into a list of items would be a
guess, and what a guess silently drops is the part you cannot see. The versions
written before the switch keep their list and are still readable as one.

A state typed as YAML always opens as YAML:

```
nginx_installed:
  pkg.installed:
    - name: nginx

nginx_config:
  file.managed:
    - name: /etc/nginx/nginx.conf
    - source: salt://nginx.conf
    - mode: 644
```

:::note
`source: salt://…` is an example of what the builder does not do: it has no file
server behind it. **File with this content** carries the content itself, which
is what Baseline's masterless design can guarantee. For anything that needs a
Salt file server, write the state as YAML and point it at one you run.
:::

Every save is a **new version**. Nothing is overwritten, because "what did this
say yesterday" is the first question asked when a fleet drifts, and the answer
has to exist. The 50 most recent versions of each state are kept.

### Deleting a state

**Delete** removes a state and every version of it. Any assignments to it go
too, and the confirmation names them first: those hosts stop being configured
by that state, and finding that out later is the kind of thing nobody traces
back.

Past **runs are kept**. They record what actually happened on hosts rather than
what was declared, so they outlive the declaration — a run list that empties
itself when a state is tidied up is not an audit trail.

## The Hosts view

The console opens on the **fleet**, as the Controller knows it, grouped by
environment. Each host shows:

- **what it must satisfy** — the states assigned to it, plus the ones it
  inherits from its environment, marked as inherited;
- **what the last run made of it** — *As declared*, *Drifted*, *Failing*,
  *Never applied*, or **Not managed** when nothing is assigned to it at all;
- and the actions: **Assign…**, **Preview**, **Apply now**.

:::note
**Not managed is not compliance.** A host with no state assigned to it, and
none inherited from its environment, is simply not looked at by Baseline. It is
the state most of a fleet is in on day one, and reporting it as "as declared"
would show an entirely unconfigured fleet as green.
:::

If the Controller cannot be reached the host panel says so and the rest of the
console carries on: states, assignments, rules and runs all come from
Baseline's own store.

## Assigning a state to hosts

Declaring a state does not apply it. **Assign** picks what it applies to:

Start from the host: **Assign…** on its row opens the dialog with that host
already chosen. **Assign to all of &lt;environment&gt;** does the same for a
whole environment — what used to require knowing the `env:<name>` syntax.

The dialog itself offers:

- a **host**, from the fleet the Controller knows — grouped by environment,
  with each host's address beside it, and SSH-only hosts marked;
- an **environment**, which applies to every host in it in addition to anything
  assigned to the host itself;
- or a target you **type**, which is always offered — a host the Controller has
  not enrolled yet is a legitimate thing to assign to.

If the Controller cannot be reached the list is empty and the dialog says why,
falling back to typing. Losing the ability to assign because the host *picker*
is down would be worse than typing a name.

## Preview before you apply

A **preview** is Salt's dry run (`test=True`): the host reports what *would*
change and changes nothing.

:::warn
A preview fires **no** event rules, by design. A dry run makes no changes, so
restarting a service for a change that never happened would be worse than having
no preview at all.
:::

Use it on any state you have not applied to a host before. A declaration that is
correct on one host and wrong on another is normal, and the preview is where you
find that out.

## What happens after a state is applied

This is the half that usually gets forgotten: the service that must be restarted
because its config file changed, the snapshot worth taking now the host is in a
known state, the alert for the one state in forty that failed.

Baseline does that with **rules**, evaluated against the outcome of each state:

| | |
|---|---|
| **When** | a state matching a pattern `changes`, `fails`, `is already correct`, or on any run |
| **Then** | `record it`, `run a command`, `capture the host's config in Flashback`, or `apply the state again` |

:::warn
**Rules fire on CHANGE, not on state.** "Restart nginx when its config changes"
fires only in a run where Salt actually changed that file. A rule that fired on
every scheduled run would restart the service forever on a timer — which is an
outage with a schedule attached, and the most likely way this feature could do
harm.
:::

A rule fires at most **once per run**, however many states it matched.

### Why rules live here and not in the state

Salt has its own `watch` and `onchanges` requisites, and for things Salt owns
they are the right tool. They cannot reach anything else — so "tell the
Controller", "capture this in Flashback" and "page someone" end up as shell-outs
buried inside configuration, invisible to review and running with whatever
privileges the state had. Rules are separate so you can read them, change them,
and see what fired without reading the state.

### The hand-off to Flashback

The `capture` action is the seam between the two products: Baseline has just put
the host into a declared state, so this is the moment to record what the host
actually looks like. Flashback stores that, and from then on you can diff it
against any earlier version.

## Reading drift

The top of the console answers one question: how many hosts are as declared?

- **as declared** — the last run changed nothing. The host already matched.
- **drifted** — the last run had to change something to bring it back.
- **failing** — the last run could not finish, or a state failed.

:::warn
A host that could not be evaluated is **never** reported as "as declared". If
`salt-call` is missing, the state fails to render, or the output is unreadable,
that host is *failing*, with the reason recorded. A configuration tool that
reports a fleet it never looked at as compliant is worse than one that reports
nothing.
:::

A host with **no state assigned** does not appear in these counts at all. It is
not compliant — it is unmanaged, which is a different thing and has a different
fix.

## Roles

Baseline uses the platform's three roles, asserted by SLOP:

| Role | Can |
|---|---|
| **Viewer** | read states, rules and run history |
| **Operator** | everything above, plus declare states, assign them and edit rules |
| **Superuser** | everything above, plus the platform's own settings |

## Security model

- **The console is only reachable through the gateway.** Baseline has no login
  of its own; it trusts the identity SLOP asserts, proven with a shared secret.
  A browser reaching it directly cannot spoof that.
- **The Controller authenticates with its own bearer token**
  (`SYSIBLE_BASELINE_AGENT_TOKEN`), separate from Flashback's. The two services
  have different powers — Flashback's token reads and writes a host's stored
  configuration, Baseline's declares what a host must become — and one token for
  both would make a compromise of either a compromise of both.
- **A `command` rule runs as root on your hosts.** It is a shell string you
  typed, dispatched through the same attributed, logged path as any other
  operator-initiated command. Treat the rule list with the same care as sudo
  access, and prefer `capture` and `notify` where they will do.

:::warn
A state can do anything Salt can do, which is anything. Review a declaration the
way you would review a playbook that runs as root on every host it is assigned
to — because that is what it is.
:::

## Where the data lives

Everything is in the `baseline-data` Docker volume: declared states, their
version history, assignments, rules and run history.

This is **not** the same volume as Flashback's, and must not be made so. One
holds what you declared, the other holds what the fleet actually looks like.
Merging them would mean losing the ability to tell those apart, which is the
only reason either is useful.

## Troubleshooting

**No hosts at all.** Nothing has been assigned a state yet, or the Controller
has no Baseline wiring (`SYSIBLE_BASELINE_URL` / `SYSIBLE_BASELINE_AGENT_TOKEN`
unset on the Controller). Those are different problems: the first is "nobody
declared anything", the second is "the Controller cannot ask".

**Every host is failing with "salt-call: command not found".** Baseline is
masterless, so Salt runs *on the host*. Install the `salt-minion` package (the
`salt-call` binary is what is needed; the daemon is not used).

**A rule never fires.** Check the trigger. `changed` fires only in a run that
actually changed something, so a rule on a fleet that is already correct is
silent — which is right. Use `any` if you genuinely want it every run.

**A state applies but the service does not restart.** The restart is a rule, not
part of the state. Check that the rule's match pattern matches the state's id,
not the file name.

## Reference: environment variables

| Variable | Default | Meaning |
|---|---|---|
| `SYSIBLE_BASELINE_AGENT_TOKEN` | — | Token the Controller presents. Empty = Baseline refuses everything |
| `SYSIBLE_BASELINE_AGENT_BIND` | `172.17.0.1` | Address the Controller-facing port binds to |
| `SYSIBLE_BASELINE_AGENT_PORT` | `8771` | Port the Controller-facing API binds to |
| `SYSIBLE_BASELINE_KEEP` | `50` | Versions kept per state before pruning |
| `SYSIBLE_BASELINE_DATA` | `/data` | Where states and run history live |
| `SYSIBLE_BASELINE_TRUST_GATEWAY_AUTH` | `1` in SLOP | Honour the identity SLOP asserts |

:::warn
`SYSIBLE_BASELINE_*` belongs to Baseline alone. Sysible Flashback briefly
carried that prefix during a rename and deliberately no longer reads it — both
products want several of the same setting names, and the backup tool quietly
using the config manager's token would not show up until the day you needed a
restore.
:::
