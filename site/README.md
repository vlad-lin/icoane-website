# Atelierul Bizantin de Icoane pe Sticlă — website

Open `public/index.html` in any browser (double-click). No server, internet connection or installation is needed. It opens the Romanian, English or French version depending on the browser's language.

## Folders

- `public/`: **the website itself**, and the only folder to publish. Everything in it is generated, so don't edit it by hand.
  - `ro/`, `en/`, `fr/`: one folder per language, each with home, gallery, available, about, technique, orders, privacy and one page per icon (`ro/icoane/masa-raiului-p922.html`).
  - `img/full` (photos up to 1600 px) and `img/thumb` (560 px), shared by all languages.
- `assets/`: `style.css` and `site.js`, copied into `public/assets/` by the build.
- `content/ui.json`: all interface and page text (menus, technique, orders…) in ro/en/fr, side by side.
- `translations/en/`, `translations/fr/`: machine translations.
  - `terms.json` holds titles and izvod.
  - The other files hold captions, keyed by a code computed from the Romanian text.
  - `todo-en.json` / `todo-fr.json` list what is still untranslated. Romanian is shown meanwhile.
- `new-posts/`: posts published after the Facebook export (`posts.json` plus the original photos). See "Adding a new Facebook post" below.
- `old-works/`: what the site takes from the private 2019–2020 archive (see below).
- `data/lucrari.json`: the works, generated from the Facebook export (a one-time import), `new-posts/` and `old-works/`.
- `tools/`: the scripts below.

## Rebuilding

After changing text in `content/` or `translations/`, or the showcase choices at the top of `tools/build_site.py`, only the pages need rebuilding:

```
python site\tools\build_site.py
```

After adding a post to `new-posts/` (or changing the curation lists in `tools/build_data.py`), run everything. The Facebook export in `..\facebook-export\` and the archive in `..\poze vechi\` stay on this PC only and are still read as sources:

```
powershell -ExecutionPolicy Bypass -File site\tools\prepare_old_photos.ps1
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
- `prepare_old_photos.ps1` (first line) is only needed when `old-works/` changes; see below.

## The 2019–2020 archive (`old-works/`)

Icons from before the Facebook page, taken from the folder `..\poze vechi\` (photos and Word documents from 2019–2020). That folder is **private and never published** (it is in `.gitignore`); only the resized photos end up in `public/img`.

- `old-works/make_works.py` lists what the site takes from it, and writes `old-works/works.json`. Edit the script, then run `python site\old-works\make_works.py` and the full chain above.
  - `WORKS`: icons not on Facebook, with ids `v1`, `v2`… (never renumber: the id is part of the page address). Each has its photo, an optional crop (`[left, top, width, height]` as fractions), the facts, and the description she wrote in 2019 (prices and weights left out).
  - The date is the day the photo was taken. `date_approx` marks the three icons found only in `Portofoliu icoane.docx`; they show "înainte de 2020".
  - `ADD_PHOTOS`: icons already on the site that were photographed earlier get one more photo (`first` makes it the main one).
  - `CHURCH_PHOTOS`: the church photos for the home page.
- `tools/prepare_old_photos.ps1` turns these photos upright, crops them and saves them in `..\poze vechi\_pentru-site\`.
- The icons are matched to Facebook posts by eye, not by photo fingerprint (the 2019 studio photos are framed and lit differently).

## Icons for churches

`CHURCH` in `tools/build_data.py` lists the icons whose captions say they were painted for a church or stand in one (Radio Trinitas, which belongs to the Church, is included). They get a "Pentru biserici" filter in the gallery, a "Destinație" line on their page, and the church section on the home page (its four icons: `CHURCH_ART` in `tools/build_site.py`).

- The "Destinație" line shows the church's place when a caption gives one ("O sfântă biserică din Dobrogea"). Her captions name regions or towns, never the church itself. The places are translated in `translations/<lang>/terms.json`.
- `DESTINATION` in `tools/build_data.py` sets a destination by hand (`p1094`: "Radio Trinitas").

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
- **Customer clean-up** (`CUT`, `DROP`, `TOWNS`): captions are cleaned automatically, so the site names no private customers (names, towns, families, dedications, priests ordering for themselves). Churches and monasteries are public clients: where they are is kept ("pentru o Sfântă Biserică din Dobrogea"), and shown on the icon page's "Destinație" line (`CHURCH_PLACE`; no place when merged posts disagree).

Keys are the post's position in `profile_posts_1.json`, the number after `p` in page names.

## Domain and contact

- The site's address is `SITE_URL = 'https://icoane.biz'` at the top of `tools/build_site.py`.
  - It produces canonical links, language alternates, social previews, `public/sitemap.xml` and `public/robots.txt`.
  - If the site ends up at `www.icoane.biz` instead, change it and rebuild.
- **E-mail:** `EMAIL = 'contact@icoane.biz'` at the top of `tools/build_site.py`. Railway's Email Forwarding sends it on (to the user's Gmail for now). It is shown in the footer, on the orders and Available pages, and in the privacy page.
- **Messenger:** the buttons ("Trimite un mesaj pe Messenger") open the page's chat inside facebook.com on computers, and the Messenger app (`m.me`) on phones (`messenger_btn()` in `build_site.py`, plus the switch in `site.js`).
- **WhatsApp:** `WHATSAPP` at the top of `tools/build_site.py` (her public number). Its button sits next to Messenger on the icon pages, the Available page and the orders card. On an icon page it opens WhatsApp with a first message naming the icon and its link.

## Statistics and privacy

- **Google Analytics 4:** `GA_ID` at the top of `tools/build_site.py`. Set it to `''` to switch statistics off; the cookie banner then disappears too.
- **TEMPORARY (since 4 Nov 2026):** `GA_ASK_CONSENT = False` in `tools/build_site.py` loads Analytics on every visit, with no banner, while the painter reviews the site. The privacy page says so in a note. **Set it back to `True` (and update `PRIVACY_UPDATED`) right after her review**, then rebuild and publish.
- **When Analytics loads (normally):** `assets/site.js` adds it only after a visitor presses "Accept" on the cookie banner. It never loads when the site is opened from disk. "Setări cookie" in the footer reopens the banner.
- **Privacy page:** its texts are `privacy_sections` in `content/ui.json` (ro/en/fr). When you change them, also update `PRIVACY_UPDATED` in `build_site.py`.
- The page promises 2 months of data retention and no advertising features. Keep the Google Analytics settings matching.

## Publishing

- The site is live at https://icoane.biz, hosted on GitHub Pages.
- Every push to `main` runs `.github/workflows/pages.yml`, which publishes only `public/`. It takes about 3–5 minutes; most of that is downloading the repository with its photos.
- Rebuild with the commands above before each commit, so `public/` is up to date.
- **DNS** is managed in Railway, where the domain was bought (it uses Name.com's servers). Keep all its records:
  - four A records and the `www` CNAME (GitHub Pages)
  - the `_github-pages-challenge` TXT (GitHub)
  - the `google-site-verification` TXT (Search Console)
  - the e-mail forwarding records that Railway manages itself (MX and SPF)
- **Google Search Console** (domain property `icoane.biz`) has the sitemap `https://icoane.biz/sitemap.xml`. Google Analytics and Search Console are under the site owner's Google account.
