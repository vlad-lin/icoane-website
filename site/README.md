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
