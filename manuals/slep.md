title: Sysible Linux Engineering Platform
subtitle: Administrator & User Guide
version: 1.0.0
description: Author, orchestrate and run Ansible and Terraform from one self-hosted console, with a real in-browser IDE — projects, inventories, credentials, runs and pipelines.

## Overview

**Sysible Linux Engineering Platform** (SLEP) is where automation is written and
run. If Sysible Controller is fleet *administration*, SLEP is infrastructure
*automation*: projects of playbooks and Terraform, the inventories they target,
the credentials they use, and a full history of every run.

It is deliberately the friendly shape of Ansible Automation Platform. The same
core objects — projects, inventories, credentials, job runs — without the
Kubernetes execution environments, automation mesh and operator sprawl that make
AAP a project in its own right.

| AAP | SLEP |
|---|---|
| Kubernetes + execution environments + operator | One container, SQLite by default |
| Automation mesh, receptors | Direct SSH, the way Ansible already works |
| Ansible only | Ansible **and** Terraform |
| Author elsewhere, sync via SCM | **In-browser IDE**; SCM optional |
| Heavy RBAC and licensing | Simple admin model, self-hosted |

:::note
Configuration *state* — holding hosts in a declared configuration over time — is
**Sysible Baseline**'s job, not SLEP's. Baseline drives Salt and reacts to its
event bus. SLEP builds and provisions.
:::

## The mental model

Five objects carry almost everything.

| Object | What it is |
|---|---|
| **Project** | A workspace of automation content — playbooks, Terraform configs — authored in the browser IDE or synced from Git |
| **Inventory** | The hosts and groups a run targets; entered by hand or imported from a Sysible Controller |
| **Credential** | An SSH key or password, cloud credential or vault token — stored server-side, injected into a run, never shown to the browser |
| **Run** | One execution of an engine against an inventory with a credential, streaming live output into a history |
| **Pipeline** | An ordered sequence of runs — Terraform apply, then Ansible, then enrol — visualised together |

Everything else — Infrastructure, Controllers, Jump Hosts, Variable Vault,
Schedules, Organizations — supports those five.

The golden path: **author** content in a project, point it at an **inventory**
with a **credential**, **run** it, watch the **visualizer**, then chain the steps
into a **pipeline**.

## Requirements

| | |
|---|---|
| Host | Any Linux machine with Docker and the Compose plugin |
| RAM | 2 GB for the console; more if runs are heavy |
| Disk | A few GB, plus whatever project workdirs and run logs need |
| Ports | `8810` web console, `9100` backend API |
| Browser | Anything current. The IDE needs a **secure context**, which is why the console is HTTPS by default |

On Sysible Server and Sysible Workstation, Docker and Compose are already
installed as hard dependencies.

:::note
Controller uses `9000`, `8800` and `8090`, so SLEP and a Controller coexist on
one host without colliding.
:::

## Installation

### On Sysible Server or Sysible Workstation

SLEP is one of the apps the image offers. It is installed from the unified
installer:

```sh
sudo install-sysible slep
```

On Workstation you can instead launch **Install Sysible Software** from the app
grid and tick **SLEP**. Either way the source is cloned to
`/opt/sysible-src/` and brought up as a container.

### Anywhere else

```sh
git clone https://github.com/sysiblesoftware/Sysible-Linux-Engineering-Platform slep
cd slep
docker compose -f deploy/docker-compose.yml up -d --build
```

One container runs everything — both services, with Ansible and Terraform baked
in. SQLite, project files and run logs persist in the `slep-data` volume.

Then open `https://<host>:8810`.

:::note
No Kubernetes, no mesh, no external database. One container and a volume.
:::

## First sign-in

Open the console and complete the **first-run screen** to create your
administrator account. You choose the password — nothing is pre-seeded, and no
credential ships in the image. That account becomes a superuser in the default
organization.

The console is HTTPS with a self-signed certificate out of the box, so the
browser warns once and then remembers. See **TLS** below for putting your own
hostname or a real certificate in front of it.

## A tour of the console

The left-hand navigation groups everything by job.

| Nav item | Use it to |
|---|---|
| **Projects** | Create and open a project and its IDE; launch runs and pipelines |
| **Inventories** | Define target hosts and groups; import a fleet from a Controller |
| **Infrastructure** | Provision VMs with Terraform and drive their lifecycle |
| **Controllers** | Connect a Sysible Controller to import inventory and enrol VMs |
| **Credentials** | Store the SSH, cloud and vault secrets runs use |
| **Jump Hosts** | Register bastions that runs and enrolment tunnel through |
| **Variable Vault** | Reusable extra-vars injected into runs |
| **Runs** | Full run history; open any run's log and visualizer; re-run |
| **Pipelines** | Author and launch multi-step sequences |
| **Schedules** | Run a job or pipeline on a recurring cadence |
| **Organizations** | Tenant boundaries — who can see and act on what |
| **Activity** | The audit trail |
| **Users** | Accounts and their roles |

## Projects and the IDE

A **project** is a folder of automation content plus its own run history.
Create one from *Projects → New project*; a slug and a per-project working
directory are created for you.

The **IDE** is Monaco — the editor from Visual Studio Code — with a file tree,
syntax highlighting for YAML, HCL and Jinja, an inline linter and a run panel.

- **+ File** adds `site.yml`, `main.tf` and so on. **Ctrl/⌘-S** saves.
- The linter flags common mistakes early, such as brittle apt version pins.
- **Sync from Git** instead, if your content already lives in source control.
- On an infrastructure project, the **infra bar** exposes the lifecycle actions —
  Plan, Apply, Destroy, Edit, Enroll — so a build can be driven without leaving
  the editor.

:::note
The IDE needs a secure context for clipboard and paste to work, which is one of
the reasons the console defaults to TLS.
:::

## Inventories

An **inventory** is the set of hosts a run targets. Create one from
*Inventories → New inventory*, then **+ Host** for each machine — name, address,
connection user and port, group. Groups let a playbook target a subset with
`hosts: web`.

**Import from a Controller** rather than typing: give a Controller URL and
backend API key and SLEP pulls the fleet you already manage, both
agent-enrolled and SSH-managed hosts, keeping each host's environment as an
Ansible group. Re-importing refreshes addresses and variables without
duplicating — it upserts by name.

Infrastructure projects also build an inventory automatically from the VMs they
apply, so machines you just created are immediately targetable.

## Credentials

A **credential** is how a run authenticates: an SSH private key, an SSH
password, a cloud credential or a vault token.

Secrets are encrypted at rest, injected into the run process server-side, and
**never surfaced to the browser or returned by the API**. A run takes exactly one
credential, chosen at launch. Password-based SSH uses `sshpass`, which is baked
into the image.

## Jump hosts

When targets are not directly reachable, register a **jump host** — a bastion
with an address, user and key. Runs and enrolment then tunnel through it:
Ansible and Terraform SSH through the bastion with a `ProxyCommand`, and agent
enrolment installs its bundle over the same hop.

Set a project's bastion once and every run and enrolment for that project
inherits it.

## Variable Vault

The **Variable Vault** stores reusable key/value sets — extra-vars such as
environment names, versions and feature flags — so they are not pasted into
every launch. Values are stored server-side and referenced when launching a run
or a pipeline step. Keys are restricted to a safe character set so they pass
cleanly to the engines.

## Running automation

Every engine has the same shape: pick a **target**, an **inventory** and a
**credential**, then **Launch**. Output streams live and the status badge settles
on `success`, `failed` or `canceled`.

| Engine | Target | Notes |
|---|---|---|
| **Ansible** | a playbook, e.g. `site.yml` | Live PLAY/TASK/RECAP parsing. **Re-run failed** retries only the hosts that broke, using `--limit` and `--start-at-task` |
| **Terraform / OpenTofu** | `plan`, `apply` or `destroy` | Self-heals stale provider locks and orphaned libvirt objects; reads applied VMs into the inventory |

**Stop** terminates the engine process and marks the run `canceled`.

**Re-run** repeats any past run from *Runs* with the same engine, target,
inventory, credential and variables.

:::warn
Cancelling a Terraform **apply** automatically launches a follow-up **Destroy**.
That removes everything in that project's Terraform state — it is
cleanup-after-abandon, not a surgical rollback of the partial apply.
:::

## The run visualizer

Every run opens with a **Visualize** pane beside the raw **Log**; drag the divider
to resize, or hide the log entirely. The visualisation is engine-aware.

- **Ansible** — a host × task grid showing which hosts the play reached and how
  each task fared: ok, changed, failed, unreachable, or didn't run.
- **Terraform** — what is being created, changed or destroyed, live, by real VM
  name rather than "Machine 1". Destroy mode says *destroyed*, not *created*.
- **Enroll** — one row per VM with its result and, on failure, the reason, plus
  an `X/Y enrolled → <controller>` tally.

A **pipeline** is shown as one window: the stages laid out side by side, each
with its live status, so the whole build is visible at a glance instead of
scrolled through. A stage flow strip along the top doubles as navigation.

## Infrastructure: provisioning VMs

The **Infrastructure** area provisions real machines with Terraform — libvirt and
KVM today — and drives their lifecycle, with no hand-written HCL.

The wizard collects provider, image, sizing and **VM groups**. A group is a named
set of identical VMs — image, count, disk and resources — so one project can
build more than one kind of machine in a single apply: two Ubuntu web nodes and
one Arch box, say. Disk size is free-form. Cloud-init (NoCloud) seeds users, keys
and passwords so the machines come up reachable.

| Action | What it does |
|---|---|
| **Plan / Apply / Destroy** | The standard Terraform actions, with confirmation on destroy |
| **Edit** | Reopen the wizard, change the spec and regenerate the Terraform. Existing wiring — bastion, controller — is preserved |
| **Apply auto-inventory** | After a successful apply, new VMs are read into the project's inventory, ready for Ansible |
| **Enroll** | Register the applied VMs into a Controller |

## Controllers and enrolment

SLEP connects to a **Sysible Controller** to import its inventory and to enrol the
VMs it builds, so new machines appear in the fleet.

**Connecting.** Authenticate one of two ways: a Controller superuser's console
username and password, which SLEP exchanges for the backend API key behind the
scenes; or the raw backend API key pasted directly.

**TLS trust on first use.** An on-premise Controller usually serves a self-signed
certificate. The first call that fails verification makes SLEP fetch the
presented certificate, pin it and retry, then reuse it for later calls — no PEM
to copy anywhere. This applies during enrolment too, so if the Controller's
certificate changes because it was rebuilt or moved, the next enrolment re-pins
and recovers by itself.

**Enrolling VMs.** The default is the agent, or pull, model: for each applied VM
SLEP downloads a one-time agent bundle from the Controller using the machine API
key, installs it over SSH — through the jump host if one is set — and the VM
enrols itself **outbound**. There is no inbound SSH as root and no human
superuser token involved.

:::note
A legacy SSH-host method also exists, registering hosts for the Controller to
reach directly. The agent path is the default because it needs only SLEP's
machine API key.
:::

## Pipelines

A **pipeline** runs an ordered list of steps as one launched sequence, sharing a
group so the visualizer can show the whole thing. Steps stop on the first
failure by default.

A common shape:

```
Terraform apply  →  Inventory (from VMs)  →  Ansible site.yml  →  Enroll → Controller
```

Two pseudo-steps make that end-to-end flow one click:

- **Inventory (from VMs)** reads the freshly applied VMs into the project's
  inventory and points the following Ansible steps at it.
- **Enroll → Controller** registers the applied VMs into the project's Controller.

The pipeline advances stage to stage on its own, all in the single-window
visualizer.

## Schedules

**Schedules** run a job or a pipeline on a recurring cadence. Give a target and a
time; SLEP fires it and records each firing in the run history exactly like a
manual run. Timezones are explicit — a schedule pins its zone, so a job set for
02:00 fires at 02:00 local.

## Organizations, users and roles

SLEP is multi-tenant. **Organizations** are the isolation boundary: projects,
inventories, credentials, runs, controllers and schedules all belong to one, and
users only see the organizations they are in. Cross-organization references are
refused — a pipeline in one cannot borrow another's credential or aim at its
inventory.

| Role | Can |
|---|---|
| **Superuser** | Full administration, including users and organizations |
| **Operator** | Author content and launch runs and pipelines in their organizations |
| **Viewer** | Read-only — see projects, runs and logs without launching anything |

Accounts, organization membership and roles are managed under **Users**.

## Activity

**Activity** is the audit trail: connections, runs launched, enrolments, schedule
changes and administrative actions, each attributed to the acting user and
scoped to what the viewer is allowed to see. It answers who ran that, who
enrolled those hosts, and when something changed.

## TLS

The console is HTTPS by default with a self-signed certificate generated at first
start and stored in the data volume under `data/tls/`. HTTPS is what makes the
browser treat the page as a secure context, which the IDE's clipboard and paste
require.

| Goal | How |
|---|---|
| Drop the name-mismatch warning | Set `SLEP_TLS_HOSTS` to your names and IPs, comma-separated, then delete `data/tls/` to regenerate |
| A real, warning-free certificate | Set `SLEP_TLS=0` to serve plain HTTP internally and front it with Caddy, nginx or Traefik terminating TLS |

The backend stays on loopback inside the container and is never exposed.
Firewall the console port as your network requires.

## Day-2 operations

All Sysible products share one management CLI. Put it on your PATH once from the
Controller checkout:

```sh
sudo ./deploy/sysible_ctl install
```

Then manage SLEP from anywhere:

```sh
sysible_ctl slep update     # pull, rebuild and restart in place
sysible_ctl slep status     # container state + console health probe
sysible_ctl slep logs
sysible_ctl slep restart
sysible_ctl slep backup     # timestamped tarball of the data volume
sysible_ctl update all      # every installed product at once
```

The `slep-data` volume is preserved across updates.

:::note
On Sysible Server and Workstation, `sysiblectl` is installed by
`install-sysible` and does the same job.
:::

## Troubleshooting

**Enrolment fails with "agent bundle download failed … no agent-bundle route
(HTTP 404)".** The Controller does not serve `/remote/agent-bundle`. Either it is
an older build without pull enrolment, or the connection URL points at the wrong
service — the console or portal port instead of the Controller **backend API**,
`:9000` by default. Reconnect the Controller at its API address. If it is
containerised, make sure the running image was built from current code; a stale
image serves stale routes.

**Enrolment fails with "certificate verify failed: self-signed certificate".**
Expected for a self-signed Controller — SLEP trusts it on first use and retries.
If it persists, the Controller is probably unreachable at that address, or two
services are answering the port.

**A 404 even though the route exists on disk.** The running process is serving old
code. Restart the Controller, and confirm nothing else owns its port — a leftover
container publishing `:9000` will intercept LAN traffic while `127.0.0.1` reaches
a different process. One Controller per port.

**Apply left orphaned libvirt objects** ("domain already exists"). The Terraform
runner self-heals stale domains and cloud-init ISOs from a partial apply and
retries. If it still fails it names exactly what to remove.

**A cancelled apply removed more than expected.** See the warning under **Running
automation** — cancelling an apply auto-runs Destroy across the whole project
state.

## Security model

- **No credential ships in the image.** The administrator account is created on
  the first-run screen with a password you choose.
- **Secrets never reach the browser.** Credentials are encrypted at rest,
  injected server-side into the run process, and are not returned by the API.
- **The console is HTTPS by default**, so the session is encrypted and the page is
  a secure context.
- **The backend is not exposed.** It stays on loopback inside the container; only
  the console port is published.
- **Enrolment is outbound.** The agent model means the VM enrols itself; there is
  no inbound SSH as root and no human superuser token in the flow.
- **Organizations are a hard boundary.** Cross-organization references are
  refused, not merely hidden.
- **Everything is attributed.** Activity records who did what.

:::warn
`SLEP_CONTROLLER_INSECURE=1` skips Controller TLS verification entirely. It is a
last resort for a LAN, not a setting to leave on. Prefer trust-on-first-use, or
`SLEP_CONTROLLER_CA` to trust a specific CA.
:::

## Reference: ports

| Port | Service |
|---|---|
| `8810` | Web console (BFF) — the only port you publish |
| `9100` | Backend API — loopback inside the container |

Sysible Controller uses `9000`, `8800` and `8090`, so the two coexist on one host.

## Reference: environment variables

| Variable | Meaning |
|---|---|
| `SLEP_DATA_DIR` | Database, project working directories and run logs |
| `SLEP_TLS_HOSTS` | Names and IPs to cover in the self-signed console certificate |
| `SLEP_TLS=0` | Serve plain HTTP internally; front it with a reverse proxy for real TLS |
| `SLEP_CONTROLLER_CA` | Trust a specific Controller CA or certificate instead of trust-on-first-use |
| `SLEP_CONTROLLER_INSECURE=1` | Skip Controller TLS verification — LAN last resort only |

## Reference: where things live

| Path | What it is |
|---|---|
| `backend/` | FastAPI API, the runners and `controller_import` |
| `webgui/` | The BFF and the React/Monaco console |
| `deploy/` | Dockerfile and compose file |
| `slep-data` volume | SQLite database, project workdirs, run logs, `data/tls/` |
