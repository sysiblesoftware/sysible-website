title: Sysible Workstation
subtitle: Administrator & Installation Guide
version: 1.0.6
description: The engineering desktop — a Debian-stable GNOME workstation with the container, Kubernetes, IaC and cloud toolchain already installed, plus VSCodium and SysTerm.

## Overview

**Sysible Workstation** is a Debian-stable desktop for people who build and run
Linux infrastructure. It is a live image: boot it and you are in a working
GNOME session with the whole toolchain present, before installing anything.

It is the same base and the same toolchain as **Sysible Server**, with a desktop
on top. If you have read that guide, most of this one will be familiar — the
package set, `install-sysible`, `sysible-tools` and `sysible verify` behave
identically, because they are the same programs.

What the desktop adds:

| | |
|---|---|
| Session | GNOME, on Wayland where the hardware allows |
| Editor | VSCodium — Visual Studio Code without Microsoft's telemetry or branding |
| Terminal | **SysTerm**, the Sysible terminal |
| Virtualization | `virt-manager` and `virt-viewer` over libvirt/QEMU |
| Capture | Wireshark, with the capture group already set up |
| Office | LibreOffice Writer, Calc and Impress |
| Guest integration | open-vm-tools, spice-vdagent and qemu-guest-agent, so it behaves properly inside a hypervisor |

The image ships for **amd64** and **arm64** — Intel and AMD machines, and Apple
Silicon under a hypervisor.

:::note
The live session is fully functional. You can evaluate the entire toolchain,
including Docker and the Sysible apps, without writing anything to disk.
:::

## What is in the image

The package set is declared by the `sysible-workstation` metapackage:
`apt show sysible-workstation` prints it on a running machine.

**Hard dependencies — 67 packages**, the same engineering base as Sysible
Server plus `sysible-desktop-gnome`:

| Group | Packages |
|---|---|
| Containers | `docker-ce`, `docker-compose-plugin`, `containerd.io`, `podman`, `buildah`, `skopeo` |
| Automation | `ansible`, `ansible-lint`, `sshpass` |
| Networking | `nftables`, `iproute2`, `dnsutils`, `tcpdump`, `nmap`, `iperf3`, `mtr-tiny` |
| Diagnostics | `htop`, `iotop`, `sysstat`, `ncdu`, `smartmontools`, `lsof`, `strace` |
| Modern CLI | `jq`, `ripgrep`, `fd-find`, `bat`, `fzf` |
| Languages | `python3`, `python3-pip`, `python3-venv`, `pipx`, `build-essential` |
| Desktop | `sysible-desktop-gnome` |
| Platform | `openssl` — SLOP's installer mints its secrets with it |

**Recommends — 46 more**, installed by default:

| Group | Packages |
|---|---|
| Desktop | `gnome-core`, `calamares`, `systerm`, `codium`, `cherrytree` |
| IaC extras | `sops`, `age` |
| Cloud | `awscli`, `gh` |
| Virtualization | `virt-manager`, `virt-viewer` |
| Guest tools | `open-vm-tools`, `open-vm-tools-desktop`, `spice-vdagent`, `qemu-guest-agent` |
| Network analysis | `wireshark` |
| Office | `libreoffice-writer`, `libreoffice-calc`, `libreoffice-impress`, `libreoffice-gnome` |
| Security | `fail2ban`, `auditd`, `apparmor`, `lynis` |
| Languages | `golang`, `rustc`, `cargo`, `nodejs`, `npm`, `default-jdk`, `maven`, `gradle` |
| Clients | `postgresql-client`, `default-mysql-client`, `sqlite3`, `redis-tools` |

Remove any Recommends you do not want with `apt remove`; nothing in the image
depends on them.

**Guaranteed, but not apt packages.** `kubectl`, `helm`, `k9s` and `tofu`
(OpenTofu) come from the image's vendor hook rather than apt — Helm and OpenTofu
as their vendors' official binaries, k9s from a checksum-verified GitHub
release. They cannot be `Depends`, so the build asserts each is on `PATH` in the
finished image and fails if one is missing.

:::note
Terraform, Vault, Consul, Nomad, Packer and Boundary are **not** bundled — they
are BUSL-1.1 licensed and not open source. OpenTofu, the open Terraform
drop-in, is installed. See **Optional tools**.
:::

## Requirements

| | Minimum | Comfortable |
|---|---|---|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8 GB+ — GNOME plus containers |
| Disk | 25 GB | 60 GB+ |
| Firmware | UEFI or legacy BIOS | UEFI |
| Graphics | anything with a framebuffer | hardware acceleration for a smooth session |

In a hypervisor, give it **4 GB of RAM and 40 GB of disk** and enable
virtualization extensions if you intend to run containers or nested VMs.

## Getting the ISO

Each release publishes both architectures. The ISO exceeds GitHub's 2 GB
per-file limit, so it ships as numbered `.part` files with checksums for the
parts and for the reassembled image.

```sh
gpg --verify SHA256SUMS.<arch>.parts.gpg SHA256SUMS.<arch>.parts
sha256sum -c SHA256SUMS.<arch>.parts
cat sysible-workstation-<arch>.iso.*.part > sysible-workstation-<arch>.iso
gpg --verify SHA256SUMS.<arch>.gpg SHA256SUMS.<arch>
sha256sum -c SHA256SUMS.<arch>
```

There are two signatures because there are two things to verify: the parts you
downloaded, and the image you assembled.

:::warn
Confirm the Sysible release key's fingerprint **out of band** before trusting
either signature — it is published at [sysible.com/security](/security). A key
fetched from the same place as the file proves nothing.
:::

## Writing the installer medium

```sh
sudo dd if=sysible-workstation-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

:::warn
`of=` takes the **device** (`/dev/sdb`), not a partition (`/dev/sdb1`). Check
with `lsblk` first; writing to the wrong device destroys it.
:::

balenaEtcher and Rufus work too. The image is isohybrid, so one file boots on
UEFI and BIOS alike.

### In VMware Fusion, VirtualBox or UTM

Attach the ISO and choose **Debian 12.x (64-bit)** as the guest type — 64-bit
ARM on Apple Silicon. open-vm-tools and spice-vdagent are preinstalled, so
clipboard sharing and display auto-resize work without installing guest
additions.

## The live session

Pick **Sysible Workstation (Live)** from the boot menu. GNOME starts and signs
in automatically.

There is **no password**. The live account, `sysible`, ships with no password
hash and is then locked, so no credential is baked into the image and none can
leak from it. Sign-in happens through GDM's autologin, which needs no password
at all. `sudo` works without one in the live session.

:::warn
The live session writes to RAM. Anything you create is gone at shutdown unless
you save it elsewhere.
:::

Four Sysible launchers are in the app grid:

| Launcher | What it does |
|---|---|
| **Install Sysible Workstation** | Starts Calamares to install to disk |
| **Install Sysible Software** | The Sysible apps — Controller, SLEP, Connect, SLOP |
| **Sysible Tools — Optional Software** | The separately licensed tools |
| **Enroll with Sysible Controller** | Registers this machine with a Controller |

## Installing to disk

Launch **Install Sysible Workstation**. Calamares asks for location, keyboard,
partitioning, and your account.

Partitioning offers erase-disk, install alongside an existing system, or manual
partitioning. The bootloader is written for UEFI and BIOS.

### What happens to the live account

You create your own account during the install, and Calamares sets root's
password. Once your account exists, the live `sysible` account is **removed
from the installed system**, so an installed machine never carries a leftover
default login.

If you name your own account `sysible`, it is kept — that account is now yours,
with the password you chose.

:::note
Password quality is enforced by `libpam-pwquality`, a hard dependency, with the
policy in `/etc/security/pwquality.conf.d/`.
:::

## The desktop

GNOME, with Sysible's artwork and GRUB theme. `sysible-avatar.service` seeds the
Sysible avatar into AccountsService for human users, so the login screen looks
like part of the product rather than a stock Debian install.

VSCodium is the editor — Visual Studio Code's source without Microsoft's
telemetry or branding, so extensions come from Open VSX.

## SysTerm

**SysTerm** is the Sysible terminal, installed as a Recommends and available
from the app grid. It is a separate product with its own repository and its own
guide; see the SysTerm manual for its features in full.

## The Sysible apps

`install-sysible` installs the platform. It is byte-identical to the copy on
Sysible Server — the edition name is read from `/etc/os-release` at run time, so
the two cannot drift.

```sh
sudo install-sysible                    # a menu, everything ticked
sudo install-sysible slop               # all three apps behind the gateway
sudo install-sysible controller slep    # just those two
sudo install-sysible --uninstall
sudo install-sysible --reinstall slop
```

| Argument | Meaning |
|---|---|
| `controller` | Sysible Controller, on its own address |
| `slep` | Sysible Linux Engineering Platform |
| `connect` | Sysible Connect |
| `all` | All three, each on its own address, no gateway |
| `slop` | All three **behind** the SLOP gateway at `https://slop.lan/` |

On the desktop, **Install Sysible Software** runs the same thing with a
checklist. Each product is cloned to `/opt/sysible-src/<repo>` and brought up as
a container through `sysiblectl`.

:::note
**First sign-in is `admin` / `sysible`.** That is SLOP's shipped default and it
is public — change it at `/account` the first time you sign in. On a host
reachable from outside, set `SLOP_ADMIN_PASSWORD=random` before the first run
instead: a password is generated into a `0600` file and never written to the
log. See the Operations Platform manual.
:::

:::note
`slop` supersedes the rest: the gateway only makes sense in front of the apps,
so choosing it installs all three.
:::

`sysible-install` is an alias for `install-sysible` — both spellings work and
take the same arguments.

## Optional tools

```sh
sysible-tools                        # interactive menu
sysible-tools list                   # catalogue and install state
sudo sysible-tools install vault consul
```

The catalogue is `terraform`, `vault`, `consul`, `nomad`, `packer`, `boundary`
and `aws-cli`. **Sysible Tools — Optional Software** in the app grid is the same
thing with a GUI.

:::warn
The HashiCorp tools are BUSL-1.1 licensed and **not** open source. Installing
them means accepting that licence. OpenTofu is already in the image and needs no
acceptance.
:::

## Checking the machine

```sh
sysible verify                  # everything
sysible verify --containers     # one group
sysible verify --virtualization
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

Network, DNS, containers, Ansible and Controller reachability are critical; the
rest report without failing the run.

## Updates

```sh
sudo apt update && sudo apt upgrade
```

Security updates install automatically via `unattended-upgrades`. Sysible's own
packages come from the Sysible apt repository, configured by `sysible-release`
and pinned to `sysible-stable`. Each build publishes a uniquely versioned
package at a unique pool path, so a rebuild never rewrites a cached file.

`sysible-release-check.timer` records whether a newer release exists; it
installs nothing.

The Sysible apps are not apt packages — update them with `sysiblectl update all`.

## Containers

Docker Engine, the Compose plugin and containerd are installed and running. In
the **live session** the `sysible` account is already in the `docker` group. On
an installed system your own account is not:

```sh
sudo usermod -aG docker "$USER"   # then log out and back in
```

:::warn
The `docker` group is root-equivalent. On a shared machine prefer `sudo docker`,
or use `podman`, which runs rootless.
:::

## Virtualization

`virt-manager` and `virt-viewer` are installed over libvirt and QEMU. The live
account is already in the `libvirt` and `kvm` groups; add your own account after
installing:

```sh
sudo usermod -aG libvirt,kvm "$USER"
virsh list --all
```

`sysible verify --virtualization` reports whether KVM is actually usable. Inside
a VM, "not usable" normally means nested virtualization is off in the
hypervisor.

## Enrolling with Sysible Controller

**Enroll with Sysible Controller** in the app grid registers this machine with a
Controller so it appears in the fleet console and can be patched and managed
from there. You need the Controller's address and an enrolment token from its
**Host enrollment** page — see the Sysible Controller manual.

## Branding guard

What the boot menu calls this machine is one line in a drop-in that belongs to
the image, not to a package, so no upgrade ever restores it.
`sysible-branding-guard.service` corrects the GRUB distributor at boot and
regenerates the menu only if it had to change something. A distributor that is
not Sysible's is left alone.

## Troubleshooting

**The live session boots to a black screen or a text console.** A graphics
driver problem. Switch to a VT with `Ctrl+Alt+F3` and check `systemctl status
gdm3`. In a VM, enable 3D acceleration or raise the video memory.

**Clipboard or display resize does not work in a VM.** The guest tools are
installed but the matching host side may not be. On VMware install VMware Tools
on the host side; on QEMU/SPICE make sure the SPICE agent channel is attached.

**Docker says permission denied.** Your account is not in the `docker` group on
an installed system. Add it and log out and back in — a new group membership
does not apply to an existing session.

**`sysible verify` says no firewall configured.** `nftables` is installed but no
ruleset is loaded. The check is non-critical; load a policy if you want it to
pass.

**The installer will not let me use the whole disk.** The live medium cannot
repartition the device it booted from. Install from a USB stick to an internal
disk, or from an ISO to a virtual disk.

**I installed and the `sysible` account is gone.** That is deliberate — see
**Installing to disk**.

## Security model

- **No default password anywhere.** The live account ships with no password hash
  and locked; the live session signs in through GDM autologin, which needs none.
  root ships locked and is set by the installer.
- **No default login survives installation.** Calamares removes the live account
  once your own exists.
- **The image is signed.** Checksums for the parts and for the reassembled ISO
  are GPG-signed with the Sysible release key (ed25519). Verify both.
- **Host keys are per machine**, regenerated on first boot, so cloning an image
  does not clone an SSH identity.
- **Password quality is enforced** by PAM as a hard dependency.
- **Nothing listens until you ask it to.** The base image runs no Sysible
  services and opens no ports.
- **The apps are built from source on your host**, cloned from their official
  repositories — not pulled as opaque images from a Sysible registry.
- **Third-party repositories are pinned by key.** Docker's apt repository is
  configured at build time with a fingerprint-checked key.

:::warn
The live session has passwordless `sudo`. Anyone who can boot your USB stick has
root on that session — and on any disk attached to the machine. Treat the medium
as you would a root shell.
:::

## Reference: paths and files

| Path | What it is |
|---|---|
| `/opt/sysible-src/<repo>` | Checkouts of each Sysible product |
| `/etc/sysible/apps.wanted` | Apps chosen during an install, pending first boot |
| `/etc/sysible/tools.wanted` | Optional tools chosen during an install |
| `/var/log/sysible-apps-firstboot.log` | App setup log |
| `/usr/share/sysible/branding.manifest` | sha256 of every branded asset |
| `/etc/calamares/modules/` | Installer configuration |
| `/etc/security/pwquality.conf.d/` | Password policy |

## Reference: services

| Unit | When | What |
|---|---|---|
| `sysible-avatar.service` | boot | Seeds the Sysible avatar for human users |
| `sysible-branding-guard.service` | boot | Keeps the GRUB distributor correct |
| `sysible-regenerate-ssh-host-keys.service` | first boot | Per-machine SSH identity |
| `sysible-release-check.timer` | periodic | Records whether a newer release exists |

## Reference: commands

| Command | What it does |
|---|---|
| `sysible verify` | Check the machine is ready; `--network`, `--containers`, `--security`, `--virtualization` narrow it |
| `install-sysible` | Install, remove or reinstall the Sysible apps |
| `sysible-install` | The same program under the other spelling |
| `sysible-tools` | Install the separately licensed optional tools |
| `sysiblectl` | Manage installed apps — `update all`, `status`, `logs` |
