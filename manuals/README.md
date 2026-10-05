# Product manuals

One Markdown file per product in this directory, rendered to `<product>-manual.html`
at the site root by `tools/generate_manuals.py`.

```sh
python3 tools/generate_manuals.py            # all of them
python3 tools/generate_manuals.py flashback  # just one
```

No dependencies — standard library only, so a fresh clone can regenerate the
manuals without installing anything.

## Backfilling screenshots

A manual marks a screenshot as a **slot**:

```
:::shot portal-signed-in
The portal: one card per app, each with a live health dot.
:::
```

Until the image exists, the page draws a dashed placeholder naming the exact file
to drop in. To fill it:

1. Save the image as `manuals/shots/<product>/<slot>.png`
   (`.jpg`, `.jpeg` and `.webp` also work) — for the example above that is
   `manuals/shots/slop/portal-signed-in.png`.
2. Re-run the generator.

The image is inlined as a data URI, so each manual stays a single self-contained
file that can be emailed or printed — the same shape as `controller-manual.html`.
The generator prints how many slots are still empty after each build.

## Writing

The Markdown subset is deliberately small: `##`/`###`/`####` headings, paragraphs,
bullet and numbered lists, tables, fenced code, links, `**bold**`, `_italic_` and
`` `code` ``. Plus three callouts:

```
:::note     a point worth making
:::warn     something that will bite
:::role     who can do this
```

Each one ends with a line containing only `:::`.

`##` headings become the numbered contents list automatically — do not number them
by hand, or the page will say "1. 1. Overview".

The first lines of the file are metadata (`title`, `subtitle`, `version`,
`description`), ending at the first blank line.
