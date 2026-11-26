title: Sysible Server
subtitle: Administrator & Installation Guide
version: 1.0.6
description: The headless Debian-stable server base — what is in the image, how to install and verify it, and how to run the Sysible platform on it.

## Overview

**Sysible Server** is a Debian-stable server image with the toolchain for running
server software already installed. No desktop, no display manager, no GUI
applications: it boots to a console and is reached over SSH.

It is not a fork. The base is Debian stable, the package manager is apt, and
every Debian package you know is still there under its usual name. What the
image adds is the set of things a container and automation host needs before it
is useful — and a small number of Sysible programs that install and check the
rest.

Two things make it different from a Debian netinst you install yourself:

| | Debian netinst | Sysible Server |
|---|---|---|
| Container runtime | you add Docker's repository, key and packages | `docker-ce`, `docker-compose-plugin` and `containerd.io` are hard dependencies of the image |
| Automation | you install Ansible, OpenTofu, kubectl, Helm | installed, with the third-party repositories already trusted |
| Firewall | none configured | `nftables` installed, `fail2ban` and `auditd` running |
| Sysible apps | not available | asked for during the install, set up on first boot |

The image ships for **amd64** and **arm64**. Both are built from the same tree
in the same release, with the same package set.

:::note
Everything in this guide is in the image. Nothing here needs a subscription, a
licence server or an account. The release key that signs the downloads is
published at [sysible.com/security](/security).
:::

## What is in the image

The package set is declared by the `sysible-server` metapackage, so it is
readable rather than a matter of trust: `apt show sysible-server` on a running
machine prints the same list.

**Hard dependencies — 66 packages.** The image cannot be built without them.

| Group | Packages |
|---|---|
| Containers | `docker-ce`, `docker-compose-plugin`, `containerd.io`, `podman`, `buildah`, `skopeo` |
| Automation | `ansible`, `ansible-lint`, `sshpass` |
| Networking | `nftables`, `iproute2`, `net-tools`, `dnsutils`, `tcpdump`, `nmap`, `netcat-openbsd`, `iperf3`, `ethtool`, `mtr-tiny`, `traceroute` |
| Diagnostics | `htop`, `iotop`, `sysstat`, `ncdu`, `smartmontools`, `lm-sensors`, `lsof`, `strace` |
| Modern CLI | `jq`, `ripgrep`, `fd-find`, `bat`, `fzf` |
| Languages | `python3`, `python3-pip`, `python3-venv`, `pipx`, `build-essential` |
| System | `sudo`, `openssh-server`, `curl`, `wget`, `git`, `vim`, `tmux`, `rsync`, `libpam-pwquality`, `openssl` |
| Sysible | `sysible-release`, `sysible-cli`, `sysible-branding`, `sysible-artwork` |

**Recommends — 34 more.** Installed by default; remove them with
`apt install --no-install-recommends` or afterwards with `apt remove`.

| Group | Packages |
|---|---|
| IaC extras | `sops`, `age` |
| Cloud | `awscli`, `gh` |
| Virtualization | `libvirt-daemon-system`, `qemu-system`, `qemu-utils` |
| Security | `fail2ban`, `auditd`, `apparmor`, `lynis` |
| Languages | `golang`, `rustc`, `cargo`, `nodejs`, `npm`, `default-jdk`, `maven`, `gradle` |
| Clients | `postgresql-client`, `default-mysql-client`, `sqlite3`, `redis-tools` |

:::note
`podman` sits alongside Docker deliberately. It comes from Debian proper, so it
is the runtime that is present even when `download.docker.com` is unreachable,
and `install-sysible` falls back to it.
:::

**Guaranteed, but not apt packages.** `kubectl`, `helm`, `k9s` and `tofu`
(OpenTofu) are installed by the image's vendor hook — Helm and OpenTofu from
their vendors' official binaries, k9s from a verified GitHub release, because
their apt repositories misbehave in a fresh build chroot. They cannot be
expressed as `Depends`, so the build instead **asserts they are on `PATH` in the
finished image and fails if any is missing**. That is a stronger guarantee than
a dependency: it checks the program is actually there, rather than that a
package was marked installed.

Separately licensed tools — Terraform, Vault, Consul, Nomad, Packer, Boundary
and the AWS CLI's vendor build — are **not** bundled. They are offered during the
install and can be added later; see **Optional tools**.

## Requirements

| | Minimum | Comfortable |
|---|---|---|
| CPU | 2 cores | 4+ cores |
| RAM | 2 GB | 8 GB — the Sysible apps build containers |
| Disk | 20 GB | 60 GB+ |
| Firmware | UEFI or legacy BIOS | UEFI |
| Network | none to install | required to set up the Sysible apps |

The ISO is hybrid, so the same file boots from a USB stick on UEFI and BIOS
machines and from a virtual optical drive.

:::warn
Installing the Sysible apps needs working DNS and outbound HTTPS to GitHub and
Docker Hub. The base install does not — you can install offline and set the
apps up later.
:::

## Getting the ISO

Each release publishes both architectures. The ISO is larger than GitHub's
2 GB per-file limit, so it ships as numbered `.part` files with checksums for
the parts and for the reassembled image.

Download, for your architecture, every `sysible-server-<arch>.iso.*.part` plus
`SHA256SUMS.<arch>.parts`, `SHA256SUMS.<arch>.parts.gpg`, `SHA256SUMS.<arch>`
and `SHA256SUMS.<arch>.gpg`.

```sh
gpg --verify SHA256SUMS.<arch>.parts.gpg SHA256SUMS.<arch>.parts
sha256sum -c SHA256SUMS.<arch>.parts
cat sysible-server-<arch>.iso.*.part > sysible-server-<arch>.iso
gpg --verify SHA256SUMS.<arch>.gpg SHA256SUMS.<arch>
sha256sum -c SHA256SUMS.<arch>
```

There are two signatures because there are two things to check: the parts you
downloaded, and the image you assembled from them. Checking only one leaves the
other unverified.

:::warn
Import the Sysible release key and confirm its fingerprint **out of band** before
you trust either signature. A key fetched from the same place as the file proves
nothing. The fingerprint is published at [sysible.com/security](/security).
:::

## Writing the installer medium

Write the reassembled `.iso` to a USB stick with `dd`, balenaEtcher or Rufus.

```sh
sudo dd if=sysible-server-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

:::warn
`of=/dev/sdX` is the **device**, not a partition — `/dev/sdb`, not `/dev/sdb1`.
Writing to the wrong device destroys it. Confirm with `lsblk` first.
:::

In a hypervisor, attach the ISO and choose **Debian 12.x (64-bit)** as the guest
type — 64-bit ARM on Apple Silicon. Give it 4 GB of RAM and 40 GB of disk, and
enable nested virtualization if you intend to run containers or VMs inside it.

## Installing

Boot the medium. The Sysible boot menu appears; choose the install entry.

The installer is the Debian Installer, with Sysible's banner and palette. It
asks the usual questions — language, keyboard, hostname, domain, users and
passwords, clock, partitioning — and two of its own.

### Optional software to install

A checklist of separately licensed tools: `terraform`, `vault`, `consul`,
`nomad`, `packer`, `boundary`, `aws-cli`. The HashiCorp tools are BUSL-1.1
licensed and **not** open source; ticking them means you accept that licence.
Nothing is installed during the install itself — the selection is recorded and
acted on at first boot.

### Sysible software to set up on first boot

A checklist of the platform itself:

| Tick | What you get |
|---|---|
| `slop` | The Controller, SLEP and Connect behind one front door at `https://slop.lan/` with a single sign-in. Recommended; it already covers all three |
| `controller` | Sysible Controller — the fleet console |
| `slep` | Sysible Linux Engineering Platform — Terraform, Ansible and Salt |
| `connect` | Sysible Connect — a terminal in the browser |

Tick nothing to set nothing up. Anything chosen here can be changed afterwards
with `sudo install-sysible`.

:::note
Both answers are recorded into the installed system and acted on by a systemd
unit at first boot — not during the install. The installer has no guaranteed
network, and an offline install has none at all, so the work waits for a boot
that does.
:::

Partitioning, bootloader installation and reboot proceed as in any Debian
install. The image writes its bootloader for both UEFI and BIOS.

## First boot

The machine boots to a console and prints a login prompt. Two one-shot services
run in the background once the network is up.

| Unit | What it does |
|---|---|
| `sysible-tools-firstboot.service` | Installs the optional tools you ticked, then removes its request file |
| `sysible-apps-firstboot.service` | Installs the Sysible apps you ticked, through `install-sysible` |
| `sysible-regenerate-ssh-host-keys.service` | Generates this machine's own SSH host keys |

Both read their request from `/etc/sysible/`, wait for `network-online.target`,
and have no start timeout — cloning repositories and building containers takes
far longer than systemd's default.

They behave differently on failure, deliberately:

- **Tools.** The request is consumed whether or not the install worked, so a
  failed download does not retry on every boot. Re-run it yourself with
  `sudo sysible-tools install <tool>`.
- **Apps.** The request is **kept** and retried on the next boot, up to three
  attempts. After that it gives up and writes `/etc/sysible/apps-failed`, which
  the login hint reads out so the failure is visible rather than silent.

Watch either from the console:

```sh
journalctl -u sysible-apps-firstboot -f
tail -f /var/log/sysible-apps-firstboot.log
tail -f /var/log/sysible-tools-firstboot.log
```

:::note
Nothing listens on the network until the apps finish installing. A port that is
not open yet on a freshly installed machine is usually this, not a fault.
:::

## Accounts and SSH

The installer creates your account; no default login ships in the installed
system. `sudo` is installed and the account you create during the install is
given administrative rights.

Password quality is enforced by `libpam-pwquality`, with the policy in
`/etc/security/pwquality.conf.d/`. It is a hard dependency so it cannot be
silently dropped.

SSH is enabled and hardened. Host keys are regenerated on first boot, so two
machines installed from the same image do not share an identity.

```sh
ssh-copy-id you@server
ssh you@server
```

:::warn
Set up key authentication and then disable password authentication in
`/etc/ssh/sshd_config.d/`. `fail2ban` throttles brute force, but a key removes
the attack rather than slowing it.
:::

## The Sysible apps

`install-sysible` installs the platform. It is the same program on Sysible
Server and Sysible Workstation — byte-identical, with the edition read from
`/etc/os-release` at run time.

```sh
sudo install-sysible                    # a menu, everything ticked
sudo install-sysible slop               # all three apps behind the gateway
sudo install-sysible controller slep    # just those two
sudo install-sysible --uninstall        # remove them
sudo install-sysible --reinstall slop   # remove, then install cleanly
```

| Argument | Meaning |
|---|---|
| `controller` | Sysible Controller, on its own address |
| `slep` | Sysible Linux Engineering Platform |
| `connect` | Sysible Connect |
| `all` | All three, each on its own address, no gateway |
| `slop` | All three **behind** the SLOP gateway at `https://slop.lan/` |

Each product is cloned to `/opt/sysible-src/<repo>` and brought up as a
container through `sysiblectl`, which is installed too, so you manage everything
afterwards from one command.

:::note
`slop` supersedes the rest. The gateway only makes sense in front of the apps,
so selecting it installs all three regardless of what else was chosen.
:::

Point `slop.lan` and the `controller.`, `slep.` and `connect.` subdomains at the
host — in DNS, or in the client's `/etc/hosts` — to reach the gateway by name.

## Optional tools

`sysible-tools` installs the separately licensed tools on demand, after the
install.

```sh
sysible-tools                        # interactive menu
sysible-tools list                   # the catalogue and what is installed
sudo sysible-tools install vault consul
```

The catalogue is `terraform`, `vault`, `consul`, `nomad`, `packer`, `boundary`
and `aws-cli`.

:::warn
Terraform, Vault, Consul, Nomad, Packer and Boundary are licensed under the
BUSL-1.1 and are **not** open source. Installing them means accepting
HashiCorp's licence. OpenTofu — the open Terraform drop-in — is already in the
image and needs no acceptance.
:::

## Checking the machine

`sysible verify` reports whether the machine is actually ready, rather than
whether packages are present.

```sh
sysible verify                  # everything
sysible verify --network        # one group
sysible verify --security
```

| Group | Checks |
|---|---|
| `network` | Network configured, DNS resolving, SSH running |
| `containers` | Container runtime, Compose, Kubernetes tools |
| `automation` | Ansible, Terraform/OpenTofu |
| `cloud` | A cloud CLI present |
| `virtualization` | KVM usable |
| `security` | Firewall, AppArmor, fail2ban |
| `controller` | Sysible Controller reachable |
| `system` | Updates current |

Network, DNS, containers, Ansible and Controller reachability are **critical**;
the rest report without failing the run.

## Updates

The image is Debian stable, so `apt` works exactly as it does anywhere else.

```sh
sudo apt update && sudo apt upgrade
```

Security updates install automatically through `unattended-upgrades`. Sysible's
own packages come from the Sysible apt repository, configured by
`sysible-release` and pinned to the `sysible-stable` suite.

Each build publishes a uniquely versioned package at a unique pool path, so a
rebuild never rewrites a file a CDN has been told to cache — the cause of
`File has unexpected size` errors on repositories that reuse paths.

`sysible-release-check.timer` checks periodically whether a newer Sysible
release exists and records the answer; it does not install anything.

The Sysible apps are not apt packages. Update them with `sysiblectl update all`.

## Containers

Docker Engine, the Compose plugin and containerd are installed and running.
Your account is not in the `docker` group by default — being in it is
equivalent to root.

```sh
sudo usermod -aG docker "$USER"   # then log out and back in
```

:::warn
Adding a user to the `docker` group grants root-equivalent access to the host.
On a multi-user machine prefer `sudo docker`, or use `podman`, which runs
rootless.
:::

## Firewall and hardening

`nftables` is installed as a hard dependency and is what `sysible verify`
looks for. It ships without a restrictive policy — the image does not guess
which ports you need.

```sh
sudo nft list ruleset
```

Also present and running: `fail2ban` (SSH brute-force throttling), `auditd`
(audit log), `apparmor` (mandatory access control profiles) and `lynis` (an
on-demand audit tool, run with `sudo lynis audit system`).

## Virtualization

`libvirt-daemon-system`, `qemu-system` and `qemu-utils` are installed, headless.
`sysible verify --virtualization` reports whether KVM is actually usable — on a
VM that normally means nested virtualization is off in the hypervisor.

```sh
sudo usermod -aG libvirt "$USER"
virsh list --all
```

## Branding guard

What the boot menu calls this machine lives in one file that belongs to the
image rather than to a package, so no upgrade ever restores it. A machine
installed while that file was wrong would have kept booting a menu naming the
wrong product forever.

`sysible-branding-guard.service` corrects the GRUB distributor at boot and
regenerates the menu if it had to change anything. It leaves a distributor that
is not Sysible's alone.

## Troubleshooting

**The apps never came up.** Check the first-boot log. The usual cause is DNS or
no route to Docker Hub.

```sh
systemctl status sysible-apps-firstboot
cat /var/log/sysible-apps-firstboot.log
cat /etc/sysible/apps-failed      # exists only if it gave up
sudo install-sysible slop         # run it yourself
```

**A tool I ticked is missing.** The tools request is consumed on first boot even
if the download failed. Install it directly:

```sh
sudo sysible-tools install terraform
```

**`apt upgrade` reports `File has unexpected size`.** A stale cache. Clear it
and retry:

```sh
sudo rm -rf /var/lib/apt/lists/*
sudo apt update
```

**`sysible verify` says no firewall configured.** `nftables` is installed but
has no ruleset loaded. Load one, or ignore the check — it is non-critical.

**The console shows a pending-setup hint at every login.** The apps request is
still outstanding. Either let the next boot retry it, or run `install-sysible`
yourself and the hint clears.

## Security model

- **The image is signed.** Checksums for the parts and for the reassembled ISO
  are GPG-signed with the Sysible release key (ed25519). Verify both.
- **No default login survives the install.** The live session's credentials do
  not reach the installed system; the installer creates your account.
- **Host keys are per machine.** Regenerated on first boot, so cloning an image
  does not clone an SSH identity.
- **Password quality is enforced** by PAM, as a hard dependency.
- **Nothing listens until you ask it to.** The base image runs no Sysible
  services and opens no ports. The apps are installed only if you chose them.
- **The apps are built from source on your host** — cloned from their official
  repositories, not pulled as opaque images from a Sysible registry.
- **Third-party repositories are pinned by key.** Docker's apt repository is
  configured at build time with a fingerprint-checked key.

:::warn
`sysible verify` reports posture; it does not harden the machine for you. A
firewall policy, SSH key-only authentication and your own patch cadence are
still yours to set.
:::

## Reference: paths and files

| Path | What it is |
|---|---|
| `/etc/sysible/apps.wanted` | Apps chosen during the install, pending first boot |
| `/etc/sysible/apps-failed` | Written if the app setup gave up; read by the login hint |
| `/etc/sysible/tools.wanted` | Optional tools chosen during the install |
| `/opt/sysible-src/<repo>` | Checkouts of each Sysible product |
| `/var/log/sysible-apps-firstboot.log` | App setup log |
| `/var/log/sysible-tools-firstboot.log` | Tool install log |
| `/var/lib/sysible/apps-firstboot.tries` | Retry counter |
| `/usr/share/sysible/branding.manifest` | sha256 of every branded asset |
| `/etc/security/pwquality.conf.d/` | Password policy |

## Reference: services and timers

| Unit | Type | When |
|---|---|---|
| `sysible-apps-firstboot.service` | one-shot | First networked boot, if apps were chosen |
| `sysible-tools-firstboot.service` | one-shot | First networked boot, if tools were chosen |
| `sysible-regenerate-ssh-host-keys.service` | one-shot | First boot |
| `sysible-branding-guard.service` | one-shot | Every boot |
| `sysible-release-check.timer` | timer | Periodic release check |

## Reference: commands

| Command | What it does |
|---|---|
| `sysible verify` | Check the machine is ready; `--network`, `--containers`, `--security`, `--virtualization` narrow it |
| `install-sysible` | Install, remove or reinstall the Sysible apps |
| `sysible-tools` | Install the separately licensed optional tools |
| `sysiblectl` | Manage installed apps — `update all`, `status`, `logs` |
| `sysible-hint` | The login summary of pending or failed setup |
