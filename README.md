# Sysible website

The public download & marketing site for **Sysible Linux** and **Sysible
Controller CE**. One self-contained static page — inline CSS, JS and SVG, no
external assets, no build step, no backend, no tracking.

Live at **https://sysible.pages.dev** (Cloudflare Pages).

## Layout

| Path | Purpose |
|------|---------|
| `index.html` | The entire site — inline styles, script and SVG. |
| `_headers` | Cloudflare Pages cache/security headers. |
| `.assetsignore` | Keeps `README.md` / `.github` out of the deployed assets. |
| `.github/workflows/deploy.yml` | Auto-deploy to Cloudflare Pages on push to `main`. |

## Editing the downloads

- **Sysible Linux ISOs are self-hosted.** Edit the `LINUX_DL` config block near
  the top of the `<script>` in `index.html`:
  ```js
  var LINUX_DL = {
    BASE_URL: "https://downloads.sysible.io",   // where the ISOs live
    version:  "0.1.0",
    codename: "Ignition",
    sha:      "SHA256SUMS",
    iso: { amd64: "sysible-linux-0.1-amd64.iso",
           arm64: "sysible-linux-0.1-arm64.iso" }
  };
  ```
  Point `BASE_URL` at your real host and drop a `SHA256SUMS` manifest next to
  the ISOs. Bump `version` / filenames on each release.
- **Controller CE** downloads are progressively enhanced: the page renders
  static first, then fetches the latest `sysiblesoftware/sysible-controller`
  release from the GitHub API and fills in the assets. It still works if that
  API is blocked (falls back to the Releases page).

## Deploy — Cloudflare Pages

`.github/workflows/deploy.yml` deploys to the Cloudflare Pages project
**`sysible`** on every push to `main` (and via *Actions → Deploy → Run
workflow*). Served at **https://sysible.pages.dev**.

**One-time setup:**

1. **Create a Cloudflare API token** — dashboard → *My Profile → API Tokens →
   Create Token*. Use the *Edit Cloudflare Workers* template, or a custom token
   with **Account → Cloudflare Pages → Edit**. Copy the token.
2. **Find your Account ID** — Cloudflare dashboard → *Workers & Pages* →
   *Account ID* in the right sidebar.
3. **Add two GitHub repo secrets** — *Settings → Secrets and variables →
   Actions → New repository secret*:
   - `CLOUDFLARE_API_TOKEN` = the token from step 1
   - `CLOUDFLARE_ACCOUNT_ID` = the Account ID from step 2
4. **Deploy** — push to `main`, or run the **Deploy** workflow manually. It
   creates the `sysible` Pages project on first run.

Until the secrets exist, the workflow runs green but **skips** the deploy with a
warning, so it never blocks.

**Custom domain** — Cloudflare dashboard → *Workers & Pages → sysible → Custom
domains → Set up a domain* (e.g. `www.sysible.io`). Requires the domain's DNS on
Cloudflare; the certificate is provisioned automatically.

## Local preview

It's a static file — open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000   # then visit http://localhost:8000
```
