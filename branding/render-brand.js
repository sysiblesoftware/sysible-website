#!/usr/bin/env node
/**
 * Render the composed, text-bearing brand assets from sysible-brand.src.html.
 *
 * branding/README.md has told people to "re-render with Chromium" for a long
 * time without saying how, because no such script existed. That is not a
 * documentation gap, it is the reason the brand drifted: the SES avatar that
 * has been live on the GitHub org was composed by hand somewhere else and
 * never came back to the source file, and nothing could detect that because
 * there was nothing to re-render WITH. This is that script.
 *
 *   node branding/render-brand.js            write the assets
 *   node branding/render-brand.js --check    fail if any committed asset differs
 *
 * Text is rendered by a real browser with the vendored Sora webfont, which is
 * why these assets are composed here rather than in render-cards.py: Pillow and
 * cairosvg both reproduce Sora's tracking and variable weights only
 * approximately, and the lockup is mostly tracking.
 */
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html':'text/html', '.woff2':'font/woff2', '.ttf':'font/ttf',
                '.svg':'image/svg+xml', '.png':'image/png', '.css':'text/css' };

// id -> [[relative output path, width or null for natural size], ...]
const TARGETS = {
  'profile':      [['branding/sysible-profile-1024.png', null],
                   ['branding/sysible-profile-512.png', 512]],
  'lockup-dark':  [['branding/ses-lockup-dark.png', null],
                   ['.github/sysible-logo-dark.png', null]],
  'lockup-light': [['branding/ses-lockup-light.png', null],
                   ['.github/sysible-logo-light.png', null]],
};

const serve = () => new Promise(res => {
  const s = http.createServer((req, rep) => {
    const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
    if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory())
      return rep.writeHead(404).end();
    rep.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(rep);
  });
  s.listen(0, '127.0.0.1', () => res(s));
});

(async () => {
  const check = process.argv.includes('--check');
  const server = await serve();
  const port = server.address().port;
  const browser = await chromium.launch();
  // deviceScaleFactor 1: these are fixed-pixel assets, not a retina screenshot.
  const page = await (await browser.newContext({ deviceScaleFactor: 1 })).newPage();
  await page.goto(`http://127.0.0.1:${port}/branding/sysible-brand.src.html`,
                  { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);

  // The source file paints body #222 so the stages are visible while editing it
  // by hand. That grey would otherwise be baked into the transparent assets --
  // it was, on the first run: a solid slab behind every README banner. Clear it
  // before capturing, and omitBackground can then actually do its job.
  const clearPageBg = p => p.addStyleTag({
    content: 'html,body{background:transparent !important}' });

  const shoot = async (id, scale) => {
    const ctx = await browser.newContext({ deviceScaleFactor: scale });
    const pg = await ctx.newPage();
    await pg.goto(`http://127.0.0.1:${port}/branding/sysible-brand.src.html`,
                  { waitUntil: 'networkidle' });
    await pg.evaluate(() => document.fonts.ready);
    const transparent = id.startsWith('lockup');
    if (transparent) await clearPageBg(pg);
    await pg.waitForTimeout(200);
    const buf = await pg.locator(`#${id}`).screenshot({ omitBackground: transparent });
    await ctx.close();
    return buf;
  };

  let bad = 0, wrote = 0;
  for (const [id, outs] of Object.entries(TARGETS)) {
    if (!(await page.locator(`#${id}`).count())) {
      console.error(`missing stage #${id}`); bad++; continue;
    }
    for (const [rel, width] of outs) {
      // A width means "the same stage, rendered smaller" -- rendered, not
      // resampled, so the type stays crisp at avatar sizes.
      const buf = await shoot(id, width ? width / 1024 : 1);
      const abs = path.join(ROOT, rel);
      if (check) {
        const same = fs.existsSync(abs) && Buffer.compare(fs.readFileSync(abs), buf) === 0;
        if (!same) { console.error(`out of date: ${rel}`); bad++; }
      } else {
        fs.mkdirSync(path.dirname(abs), { recursive: true });
        fs.writeFileSync(abs, buf); console.log(`wrote ${rel}`); wrote++;
      }
    }
  }
  await browser.close(); server.close();
  if (check) { console.log(bad ? `${bad} asset(s) out of date` : 'brand assets up to date'); process.exit(bad ? 1 : 0); }
  console.log(`${wrote} asset(s) written from branding/sysible-brand.src.html`);
  process.exit(bad ? 1 : 0);
})();
