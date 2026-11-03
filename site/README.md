# Atelierul Bizantin de Icoane pe Sticlă — website

Open `public/index.html` in any browser (double-click). No server, internet connection or installation is needed. It opens the Romanian, English or French version depending on the browser's language.

## Folders

- `public/`: **the website itself**, and the only folder to publish. Everything in it is generated, so don't edit it by hand.
  - `ro/`, `en/`, `fr/`: one folder per language, each with home, gallery, about, technique, orders and one page per icon (`ro/icoane/masa-raiului-p922.html`).
  - `img/full` (photos up to 1600 px) and `img/thumb` (560 px), shared by all languages.
- `assets/`: `style.css` and `site.js`, copied into `public/assets/` by the build.
- `content/ui.json`: all interface and page text (menus, technique, orders…) in ro/en/fr, side by side.
- `translations/en/`, `translations/fr/`: machine translations.
  - `terms.json` holds titles and izvod.
  - The other files hold captions, keyed by a code computed from the Romanian text.
  - `todo-en.json` / `todo-fr.json` list what is still untranslated. Romanian is shown meanwhile.
- `data/lucrari.json`: the works, generated from the Facebook export.
- `tools/`: the scripts below.

## Rebuilding

After changing text in `content/` or `translations/`, or the showcase choices at the top of `tools/build_site.py`, only the pages need rebuilding:

```
python site\tools\build_site.py
```

After a new Facebook export (put it in `..\facebook-export\`), run everything:

```
python site\tools\build_data.py
powershell -ExecutionPolicy Bypass -File site\tools\measure_colour.ps1
powershell -ExecutionPolicy Bypass -File site\tools\hash_images.ps1
python site\tools\build_data.py
powershell -ExecutionPolicy Bypass -File site\tools\make_images.ps1
python site\tools\build_site.py
```

- `measure_colour.ps1` recognises ink drawings (nearly colourless photos). Each drawing is attached to its finished icon under "Etapele lucrării".
- `hash_images.ps1` fingerprints each photo. Reposts of the same icon (same photo) become one page, and the other captions are kept under "Alte prezentări ale acestei icoane".
- `make_images.ps1` resizes the photos and deletes the ones no longer used.

## Adding a new Facebook post (without a new export)

Posts published after the export go in `new-posts/`:

1. Save the photo(s) in `new-posts/`, named e.g. `2026-09-22-intrarea-domnului-in-ierusalim.jpg`.
2. Add an entry to `new-posts/posts.json` with:
   - a new `id` (`n2`, `n3`, …; never reuse or renumber, because it is part of the page address)
   - the `date` (YYYY-MM-DD), the `photos` and the caption `text`, exactly as on Facebook
   - optionally `title`, `izvod`, `dimensiuni`, `sarbatoare` or `disponibilitate`, when the automatic reading of the caption gets them wrong
3. Run the full chain above. Only the new photos are created; the existing ones stay as they are.
4. A new `izvod` also needs a line in `translations/en/terms.json` and `translations/fr/terms.json`.

**Available icons.** An icon whose caption says it is available ("această icoană este disponibilă") gets the status "Disponibilă". It appears on the "Available" page (`ro/disponibile.html`, `en/available.html`, `fr/disponibles.html`) and gets a badge in the gallery. **When it is sold,** add this to its entry in `posts.json` and rebuild:

```
"disponibilitate": "Nu este disponibilă — se poate picta din nou, la comandă"
```

It then leaves the Available page. Its caption still says "disponibilă", because the caption is kept as she wrote it.

The caption is cleaned of customer references and its facts are read the same way as for exported posts. If a later Facebook export includes these posts, remove them from `posts.json`, or they will be merged with their exported copy (same photo) and their page address will change from `…-n1` to `…-p<number>`.

## Curation (lists at the top of `tools/build_data.py`)

- `PATRIMONIU`: old icons by other painters (museums, churches). Left out of the site.
- `SKIP`: posts left out entirely (non-artwork, re-uploads, the contest posts).
- `HIDE_TEXT`: icons shown without their caption (the broken-parcel post, the contest announcement).
- `TITLES`: titles for posts whose caption doesn't name the icon.
- `FINISHED_BW`: black-and-white pieces that are finished works, not drawings.
- `SUBJECTS`: the vocabulary that turns captions into consistent titles and themes.
- **Customer clean-up** (`CUT`, `DROP`, `TOWNS`): captions are cleaned automatically, so the site names no customers (names, towns, families, dedications). A church is kept ("pentru o Sfântă Biserică") but not its town.

Keys are the post's position in `profile_posts_1.json`, the number after `p` in page names.

## Domain and contact

- The site's address is `SITE_URL = 'https://icoane.biz'` at the top of `tools/build_site.py`.
  - It produces canonical links, language alternates, social previews, `public/sitemap.xml` and `public/robots.txt`.
  - If the site ends up at `www.icoane.biz` instead, change it and rebuild.
- There is no e-mail address yet. When there is one, add it where the comment in the orders page says so (`orders_page` in `tools/build_site.py`), with its text in `content/ui.json` in all three languages.

## Publishing

- Only `public/` is served: static HTML with no build step.
- The plan is the same as evochain: GitHub Pages hosts the site, and the `icoane.biz` DNS records are added in Railway, where the domain was bought. See "Next steps" in `../CLAUDE.md` for the options and the exact DNS records.
- Rebuild with the commands above before each commit, so `public/` is up to date.
