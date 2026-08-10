#!/usr/bin/env python3
"""Turn a GitHub "release" API object into the compact release-linux.json the
download page reads.

Reads the raw release JSON (the payload of
`/repos/<owner>/<repo>/releases/latest`) on stdin and writes the derived,
deterministically-serialized document on stdout. Run the same way in CI and
locally so the committed seed and the workflow output stay byte-identical:

    curl -sSL -H 'Accept: application/vnd.github+json' \
      https://api.github.com/repos/sysiblesoftware/sysible-linux/releases/latest \
      | python3 tools/build_release_json.py > release-linux.json
"""
import json
import re
import sys

PART_RE = re.compile(r"^(?P<iso>.+\.iso)\.(?P<idx>\d+)\.part$")
SUMS_RE = re.compile(r"^SHA256SUMS\.(?P<arch>amd64|arm64)$")
PARTSUMS_RE = re.compile(r"^SHA256SUMS\.(?P<arch>amd64|arm64)\.parts$")
REASSEMBLE_RE = re.compile(r"^REASSEMBLE\.(?P<arch>amd64|arm64)\.md$")
CODENAME_RE = re.compile(r"[“”\"']([A-Za-z][A-Za-z0-9 ]+)[“”\"']")


def arch_of(name):
    if "arm64" in name or "aarch64" in name:
        return "arm64"
    if "amd64" in name or "x86_64" in name or "x86-64" in name:
        return "amd64"
    return None


def main():
    rel = json.load(sys.stdin)
    tag = rel.get("tag_name") or ""
    version = tag[1:] if tag.startswith("v") else tag

    codename = ""
    m = CODENAME_RE.search(rel.get("body") or "")
    if m:
        codename = m.group(1).strip()

    arches = {}

    def arch_entry(arch):
        return arches.setdefault(
            arch,
            {"iso": "", "parts": [], "sums": None, "partsSums": None, "reassemble": None},
        )

    for a in rel.get("assets", []):
        name = a.get("name") or ""
        url = a.get("browser_download_url") or ""
        arch = arch_of(name)
        if arch is None:
            continue
        entry = arch_entry(arch)
        pm = PART_RE.match(name)
        if pm:
            entry["iso"] = pm.group("iso")
            entry["parts"].append({"name": name, "url": url, "size": a.get("size")})
        elif PARTSUMS_RE.match(name):
            entry["partsSums"] = {"name": name, "url": url}
        elif SUMS_RE.match(name):
            entry["sums"] = {"name": name, "url": url}
        elif REASSEMBLE_RE.match(name):
            entry["reassemble"] = {"name": name, "url": url}

    for entry in arches.values():
        entry["parts"].sort(key=lambda p: p["name"])

    doc = {
        "version": version,
        "tag": tag,
        "codename": codename,
        "name": rel.get("name") or "",
        "published_at": rel.get("published_at") or "",
        "html_url": rel.get("html_url") or "",
        "arches": arches,
    }
    json.dump(doc, sys.stdout, indent=2, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
