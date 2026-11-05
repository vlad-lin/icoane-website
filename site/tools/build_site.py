"""Builds the website in site/public/ from:
  - site/data/lucrari.json   the works (made by build_data.py)
  - site/content/ui.json     interface and page text in ro/en/fr
  - site/translations/<lang>/ machine translations of titles, izvod and captions

Run:  python site/tools/build_site.py
Untranslated items fall back to Romanian and are listed in site/translations/todo-<lang>.json.
The pages use relative links, so public/index.html opens straight from disk.
"""
import datetime
import glob
import hashlib
import html
import json
import os
import posixpath
import re
import shutil
import sys
import unicodedata
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PUBLIC = os.path.join(SITE, 'public')
LANGS = ['ro', 'en', 'fr']

# The public address (no trailing slash). It turns on canonical links, language
# alternates, social previews, sitemap.xml and robots.txt. Must match the domain
# set up on Railway (with or without "www.").
SITE_URL = 'https://icoane.biz'

# Contact address shown on the site (forwards to the painter's own inbox).
EMAIL = 'contact@icoane.biz'
# Her WhatsApp number, international form without "+" (public on her Facebook page: 0756 390 461).
WHATSAPP = '40756390461'
# Google Analytics 4 measurement ID. site.js loads it only after the visitor accepts
# the cookie banner, and never when the site is opened from disk (file://).
# Set to '' to switch statistics off (the banner then disappears too).
GA_ID = 'G-1WBC279E6L'
# TEMPORARY (user, 4 Nov 2026): False = Analytics loads on every visit, with no cookie
# banner, so the user can see which pages the painter opens while she reviews the site.
# The privacy page then shows a "temporary note" saying so. Set back to True (and update
# PRIVACY_UPDATED) right after her review: see CLAUDE.md, "Next steps".
GA_ASK_CONSENT = False
# Date shown on the privacy page; change it whenever that text changes.
PRIVACY_UPDATED = '2026-11-04'

# Showcase choices (post ids; a merged icon can be named by any of its posts).
HERO = ['p705', 'p808', 'p906']
ABOUT = 'p700'
BEFORE_AFTER = 'p922'  # finished icon whose ink drawing is attached as a stage
ORDERS_ART = 'p755'
# Icons shown in the home page's church section (the church photos come from old-works/works.json).
CHURCH_ART = ['p1199', 'p1123', 'p1091', 'p786']
RECENT = 8
# The availability value (set by build_data.py) of icons that are for sale now;
# they are listed on the "available" page.
AVAILABLE = 'Disponibilă'


def esc(s):
    return html.escape(str(s), quote=True)


def fold(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def slugify(s):
    s = fold(s.replace('œ', 'oe').replace('Œ', 'oe').replace('æ', 'ae'))
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60].rstrip('-')


def messenger_btn(L, cls):
    """Messenger: on computers the chat inside facebook.com (where people are already logged
    in; m.me would send them to messenger.com, which asks for a separate login). site.js
    switches phones to m.me, which opens the Messenger app."""
    user = SITE_DATA['facebook'].rstrip('/').rsplit('/', 1)[-1]
    return (f'<a class="btn {cls} js-messenger" href="https://www.facebook.com/messages/t/{esc(user)}" '
            f'data-mobile="https://m.me/{esc(user)}" target="_blank" rel="noopener">{esc(L.t("send_message"))}</a>')


def whatsapp_btn(L, cls, text):
    """WhatsApp chat with her number, with a first message already written (the visitor can edit it)."""
    url = f'https://wa.me/{WHATSAPP}?text=' + urllib.parse.quote(text)
    return f'<a class="btn {cls}" href="{esc(url)}" target="_blank" rel="noopener">{esc(L.t("whatsapp_btn"))}</a>'


def text_key(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:12]


def text_html(s):
    out = []
    for para in re.split(r'\n\s*\n', s.strip()):
        h = esc(para.strip())
        h = re.sub(r'(https?://[^\s<]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', h)
        out.append('<p>' + h.replace('\n', '<br>') + '</p>')
    return ''.join(out)


class Translator:
    """Looks up machine translations; remembers what is missing."""

    def __init__(self, lang):
        self.lang = lang
        self.terms, self.texts = {}, {}
        self.missing_terms, self.missing_texts = {}, {}
        for path in sorted(glob.glob(os.path.join(SITE, 'translations', lang, '*.json'))):
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            (self.terms if os.path.basename(path) == 'terms.json' else self.texts).update(data)

    def term(self, s):
        if self.lang == 'ro' or not s:
            return s
        if s not in self.terms:
            self.missing_terms[s] = ''
        return self.terms.get(s) or s

    def text(self, s):
        """Returns (text, translated?)."""
        if self.lang == 'ro' or not s:
            return s, False
        k = text_key(s)
        if self.texts.get(k):
            return self.texts[k], True
        self.missing_texts[k] = s
        return s, False


class Lang:
    def __init__(self, code, ui):
        self.code = code
        self.ui = ui[code]
        self.tr = Translator(code)
        self.p = self.ui['pages']

    def t(self, key, **kw):
        s = self.ui[key]
        for k, v in kw.items():
            s = s.replace('{' + k + '}', str(v))
        return s

    def date(self, iso):
        y, m, d = (int(x) for x in iso.split('-'))
        return f'{d} {self.ui["months"][m - 1]} {y}'

    def work_date(self, e):
        """The date shown for a work: archive icons without a known date show "before 2020"."""
        return self.ui['before_2020'] if e.get('date_approx') else self.date(e['date'])

    def feast(self, s):
        d, month = s.split(' ', 1)
        ro = UI['ro']['months']
        return f'{d} {self.ui["months"][ro.index(month)]}' if month in ro else s

    def title(self, e):
        if e['title'] == UI['ro']['default_title']:
            return self.ui['default_title']
        return self.tr.term(e['title'])

    def page(self, key):
        return f'{self.code}/{self.p[key]}'

    def work(self, e):
        return f'{self.code}/{self.p["icons"]}/{slugify(self.title(e))}-{e["id"]}.html'


def rel(target, current):
    """Relative link from one public path to another."""
    return posixpath.relpath(target, posixpath.dirname(current) or '.')


# --- Layout ------------------------------------------------------------------------
BRAND_MARK = '<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true"><path d="M15 3h2v6h6v2h-6v4h4v2h-4v12h-2V17h-4v-2h4v-4H9V9h6z"/></svg>'
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23b8391f'/%3E"
           "%3Cpath d='M15 4h2v6h6v2h-6v4h4v2h-4v10h-2V18h-4v-2h4v-4H9v-2h6z' fill='%23f0cf7a'/%3E%3C/svg%3E")


def layout(L, path, alternates, title, description, body, active='', image=''):
    """path: this page's path under public/; alternates: {lang: path} for the same page."""
    def link(p):
        return esc(rel(p, path))
    nav = ''
    for key in ('gallery', 'available', 'about', 'technique', 'orders'):
        cls = ' class="nav-cta"' if key == 'orders' else ''
        cur = ' aria-current="page"' if key == active else ''
        nav += f'<a href="{link(L.page(key))}"{cls}{cur}>{esc(L.t("nav_" + key))}</a>'
    langs = ''.join(
        f'<a href="{link(alternates[c])}" hreflang="{c}" lang="{c}" title="{esc(UI[c]["lang_name"])}"'
        + (' aria-current="true"' if c == L.code else '') + f'>{c.upper()}</a>'
        for c in LANGS)
    head_extra = ''
    if SITE_URL:
        head_extra += f'<link rel="canonical" href="{SITE_URL}/{esc(path)}">\n'
        for c in LANGS:
            head_extra += f'<link rel="alternate" hreflang="{c}" href="{SITE_URL}/{esc(alternates[c])}">\n'
        head_extra += f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/{esc(alternates["ro"])}">\n'
        head_extra += (f'<meta property="og:type" content="website">\n<meta property="og:title" content="{esc(title)}">\n'
                       f'<meta property="og:description" content="{esc(description)}">\n')
        if image:
            head_extra += f'<meta property="og:image" content="{SITE_URL}/{esc(image)}">\n'
    # Cookie banner for the statistics; hidden until site.js decides to show it.
    cookie_link, banner = '', ''
    if GA_ID and GA_ASK_CONSENT:
        cookie_link = f' · <button type="button" class="linklike" id="cookie-settings">{esc(L.t("footer_cookies"))}</button>'
        banner = (f'<div class="consent" id="consent" role="region" aria-label="{esc(L.t("consent_label"))}" hidden>'
                  f'<p>{esc(L.t("consent_text"))} <a href="{link(L.page("privacy"))}">{esc(L.t("consent_more"))}</a></p>'
                  f'<div class="consent-actions">'
                  f'<button type="button" class="btn btn-ghost" data-consent="denied">{esc(L.t("consent_decline"))}</button>'
                  f'<button type="button" class="btn btn-ghost" data-consent="granted">{esc(L.t("consent_accept"))}</button>'
                  f'</div></div>\n')
    return f'''<!doctype html>
<html lang="{L.code}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{head_extra}<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="{link('assets/style.css')}">
<script>document.documentElement.classList.add('js')</script>
</head>
<body{f' data-ga="{esc(GA_ID)}"' if GA_ID else ''}{'' if GA_ASK_CONSENT or not GA_ID else ' data-ga-always="1"'}>

<header class="topbar">
  <div class="wrap topbar-inner">
    <a class="brand" href="{link(L.page('home'))}">
      {BRAND_MARK}
      <span>{esc(L.t('brand_1'))}<small>{esc(L.t('brand_2'))}</small></span>
    </a>
    <button class="nav-toggle" aria-label="{esc(L.t('menu'))}" aria-expanded="false" aria-controls="nav">☰</button>
    <nav id="nav" class="nav">{nav}<span class="langs" aria-label="{esc(L.t('language'))}">{langs}</span></nav>
  </div>
</header>

<main>
{body}
</main>

<footer class="footer">
  <div class="wrap">
    <p>© {datetime.date.today().year} {esc(L.t('site_name'))} · {esc(L.t('footer'))}</p>
    <p class="footer-links"><a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{link(L.page('privacy'))}">{esc(L.t('footer_privacy'))}</a>{cookie_link}</p>
  </div>
</footer>
{banner}<script src="{link('assets/site.js')}"></script>
</body>
</html>
'''


# --- Pages ---------------------------------------------------------------------------
def thumb(e, path, i=0):
    return esc(rel('img/thumb/' + e['images'][i], path))


def card(L, e, path):
    title = L.title(e)
    multi = f'<span class="badge multi">{esc(L.t("photos", n=len(e["images"])))}</span>' if len(e['images']) > 1 else ''
    if e.get('disponibilitate') == AVAILABLE:
        multi += f'<span class="badge available">{esc(L.t("badge_available"))}</span>'
    meta = L.work_date(e) + (' · ' + e['dimensiuni'] if e.get('dimensiuni') else '')
    izvod = f'<p class="card-izvod">{esc(L.t("izvod_prefix") + L.tr.term(e["izvod"]))}</p>' if e.get('izvod') else ''
    church = ' data-church="1"' if e.get('biserica') else ''
    return (f'<a class="card" href="{esc(rel(L.work(e), path))}" data-id="{e["id"]}" data-theme="{e["theme"]}"{church} '
            f'data-date="{e["date"]}" data-title="{esc(title)}">'
            f'<div class="card-img">{multi}<img loading="lazy" src="{thumb(e, path)}" alt="{esc(title)}"></div>'
            f'<div class="card-body"><h3>{esc(title)}</h3><p class="card-meta">{esc(meta)}</p>{izvod}</div></a>')


def home_page(L, works, by_id, path):
    hero = ''.join(
        f'<a href="{esc(rel(L.work(e), path))}" title="{esc(L.title(e))}"><img src="{thumb(e, path)}" alt="{esc(L.title(e))}"></a>'
        for e in (by_id.get(i) for i in HERO) if e)
    facts = ''.join(f'<li><strong>{esc(a)}</strong><span>{esc(b)}</span></li>' for a, b in L.ui['facts'])
    recent = ''.join(card(L, e, path) for e in works[:RECENT])
    teaser_art = {'about': by_id.get(ABOUT), 'technique': by_id.get(BEFORE_AFTER), 'orders': by_id.get(ORDERS_ART)}
    teasers = ''
    for key in ('about', 'technique', 'orders'):
        head, text = L.ui['teasers'][key]
        e = teaser_art[key]
        img = ''
        if e:
            src = ('img/thumb/' + e['stages'][0]['images'][0]) if key == 'technique' and e.get('stages') else 'img/thumb/' + e['images'][0]
            img = f'<div class="teaser-img"><img loading="lazy" src="{esc(rel(src, path))}" alt=""></div>'
        teasers += (f'<a class="teaser teaser-{key}" href="{esc(rel(L.page(key), path))}">{img}<div class="teaser-body">'
                    f'<p class="eyebrow">{esc(L.t("nav_" + key))}</p><h3>{esc(head)}</h3><p>{esc(text)}</p>'
                    f'<span class="teaser-more">{esc(L.t("read_more"))} →</span></div></a>')
    return f'''<section class="hero starry">
  <div class="wrap hero-inner">
    <div class="hero-text">
      <p class="eyebrow">{esc(L.t('hero_eyebrow'))}</p>
      <h1>{L.t('hero_h1')}</h1>
      <p class="lead">{esc(L.t('tagline'))}</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="{esc(rel(L.page('gallery'), path))}">{esc(L.t('cta_gallery'))}</a>
        <a class="btn btn-ghost" href="{esc(rel(L.page('orders'), path))}">{esc(L.t('cta_order'))}</a>
      </div>
      <ul class="facts">{facts}</ul>
    </div>
    <div class="hero-art">{hero}</div>
  </div>
</section>
<div class="band" aria-hidden="true"></div>
<section class="section gallery">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">{esc(L.t('recent_eyebrow'))}</p>
      <h2>{esc(L.t('recent_title'))}</h2>
    </div>
    <div class="grid">{recent}</div>
    <div class="more"><a class="btn btn-ghost" href="{esc(rel(L.page('gallery'), path))}">{esc(L.t('all_works', n=len(works)))}</a></div>
  </div>
</section>
{church_section(L, works, by_id, path)}
<div class="band" aria-hidden="true"></div>
<section class="section teasers-section starry">
  <div class="wrap teasers">{teasers}</div>
</section>'''


def church_section(L, works, by_id, path):
    """Home page: her icons in churches (a church photo, a few icons, a link to all of them)."""
    photos = SITE_DATA.get('church_photos', [])
    icons = [e for e in (by_id.get(i) for i in CHURCH_ART) if e]
    count = sum(1 for e in works if e.get('biserica'))
    if not photos or not count:
        return ''
    title = L.t('church_title')
    thumbs = ''.join(f'<a href="{esc(rel(L.work(e), path))}" title="{esc(L.title(e))}">'
                     f'<img loading="lazy" src="{thumb(e, path)}" alt="{esc(L.title(e))}"></a>' for e in icons)
    return f'''<div class="band" aria-hidden="true"></div>
<section class="section church">
  <div class="wrap church-inner">
    <figure class="church-photo">
      <img loading="lazy" src="{esc(rel('img/full/' + photos[0], path))}" alt="{esc(L.t('church_photo_alt'))}">
      {f'<img class="church-inset" loading="lazy" src="{esc(rel("img/full/" + photos[1], path))}" alt="">' if len(photos) > 1 else ''}
      <figcaption>{esc(L.t('church_photo_caption'))}</figcaption>
    </figure>
    <div class="church-text">
      <p class="eyebrow">{esc(L.t('church_eyebrow'))}</p>
      <h2>{esc(title)}</h2>
      {''.join(f'<p>{esc(p)}</p>' for p in L.ui['church_text'])}
      <div class="church-icons">{thumbs}</div>
      <div class="hero-actions">
        <a class="btn btn-primary" href="{esc(rel(L.page('gallery'), path))}#theme=biserici">{esc(L.t('church_all', n=count))}</a>
        <a class="btn btn-ghost" href="{esc(rel(L.page('orders'), path))}">{esc(L.t('cta_order'))}</a>
      </div>
    </div>
  </div>
</section>'''


def gallery_page(L, works, path):
    counts = {}
    for e in works:
        counts[e['theme']] = counts.get(e['theme'], 0) + 1
    chips = f'<button data-theme="all" aria-pressed="true">{esc(L.t("all_themes"))}<span class="count">{len(works)}</span></button>'
    church = sum(1 for e in works if e.get('biserica'))
    if church:
        chips += (f'<button data-theme="biserici" aria-pressed="false">{esc(L.t("church_chip"))}'
                  f'<span class="count">{church}</span></button>')
    for key, label in L.ui['themes'].items():
        if counts.get(key):
            chips += f'<button data-theme="{key}" aria-pressed="false">{esc(label)}<span class="count">{counts[key]}</span></button>'
    strings = {k: L.ui[k] for k in ('count_one', 'count_many', 'count_shown')}
    cards = ''.join(card(L, e, path) for e in works)
    return f'''<section class="section gallery gallery-page">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">{esc(L.t('gallery_eyebrow'))}</p>
      <h1 class="h2">{esc(L.t('gallery_title'))}</h1>
      <p>{esc(L.t('gallery_intro'))}</p>
    </div>
    <div class="controls">
      <div class="search-row">
        <label class="search">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 4a6 6 0 1 0 3.7 10.7l4.8 4.8 1.4-1.4-4.8-4.8A6 6 0 0 0 10 4zm0 2a4 4 0 1 1 0 8 4 4 0 0 1 0-8z"/></svg>
          <input id="search" type="search" placeholder="{esc(L.t('search_placeholder'))}" autocomplete="off">
        </label>
        <select id="sort" aria-label="{esc(L.t('sort_label'))}">
          <option value="new">{esc(L.t('sort_new'))}</option>
          <option value="old">{esc(L.t('sort_old'))}</option>
          <option value="az">{esc(L.t('sort_az'))}</option>
        </select>
      </div>
      <div class="chips" id="theme-filter" aria-label="{esc(L.t('theme_label'))}">{chips}</div>
    </div>
    <p class="result-count" id="result-count" aria-live="polite"></p>
    <div class="grid" id="grid" data-lang="{L.code}" data-strings="{esc(json.dumps(strings, ensure_ascii=False))}">{cards}</div>
    <p class="empty" id="empty" hidden>{esc(L.t('no_results'))}</p>
    <div class="more"><button class="btn btn-ghost" id="more" hidden>{esc(L.t('show_more'))}</button></div>
  </div>
</section>
<script src="{esc(rel(f'assets/search-{L.code}.js', path))}"></script>'''


def available_page(L, works, path):
    """The icons for sale now, with a message box; a friendly note when there are none."""
    available = [e for e in works if e.get('disponibilitate') == AVAILABLE]
    if available:
        count = L.t('count_one') if len(available) == 1 else L.t('count_many', n=len(available))
        content = (f'<p class="result-count">{esc(count)}</p>'
                   f'<div class="grid">{"".join(card(L, e, path) for e in available)}</div>'
                   f'<div class="v-cta available-cta"><p>{esc(L.t("available_cta"))}</p>'
                   f'<div class="cta-buttons">{messenger_btn(L, "btn-primary")}'
                   f'{whatsapp_btn(L, "btn-ghost", L.t("whatsapp_text"))}'
                   f'<a class="btn btn-ghost" href="mailto:{EMAIL}">{esc(L.t("email_btn"))}</a></div></div>')
    else:
        content = (f'<div class="v-cta available-cta"><p>{esc(L.t("available_empty"))}</p>'
                   f'<a class="btn btn-primary" href="{esc(rel(L.page("orders"), path))}">{esc(L.t("cta_order"))}</a></div>')
    return f'''<section class="section gallery available-page">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">{esc(L.t('available_eyebrow'))}</p>
      <h1 class="h2">{esc(L.t('available_title'))}</h1>
      <p>{esc(L.t('available_intro'))}</p>
    </div>
    {content}
  </div>
</section>'''


def work_page(L, e, works, by_title, path, prev, nxt):
    title = L.title(e)
    full = lambda name: esc(rel('img/full/' + name, path))
    small = lambda name: esc(rel('img/thumb/' + name, path))
    media = [(n, '') for n in e['images']]
    for s in e.get('stages', []):
        media += [(n, L.t('stage_caption', d=L.date(s['date']))) for n in s['images']]
    thumbs = ''
    if len(media) > 1:
        thumbs = '<div class="v-thumbs">' + ''.join(
            f'<a href="{full(n)}" data-index="{i}" data-caption="{esc(c)}" aria-label="{esc(c or L.t("photo_n", n=i + 1))}"'
            + (' aria-current="true"' if i == 0 else '') + f'><img loading="lazy" src="{small(n)}" alt=""></a>'
            for i, (n, c) in enumerate(media)) + '</div>'

    rows = [(L.t('fact_theme'), esc(L.ui['themes'].get(e['theme'], '')))]
    if e.get('izvod'):
        rows.append((L.t('fact_izvod'), esc(L.tr.term(e['izvod']))))
    if e.get('dimensiuni'):
        rows.append((L.t('fact_size'), esc(e['dimensiuni'])))
    if e.get('sarbatoare'):
        rows.append((L.t('fact_feast'), esc(L.feast(e['sarbatoare']))))
    if e.get('disponibilitate'):
        value = esc(L.ui['availability'].get(e['disponibilitate'], e['disponibilitate']))
        if e['disponibilitate'] == AVAILABLE:
            value = f'<a href="{esc(rel(L.page("available"), path))}">{value}</a>'
        rows.append((L.t('fact_availability'), value))
    if e.get('destinatie'):
        rows.append((L.t('fact_church'), esc(e['destinatie'])))
    elif e.get('biserica'):
        where =(L.t('church_value_at', loc=L.tr.term(e['biserica_loc'])) if e.get('biserica_loc')
                 else L.t('church_value'))
        rows.append((L.t('fact_church'), f'<a href="{esc(rel(L.page("gallery"), path))}#theme=biserici">{esc(where)}</a>'))
    facts = ''.join(f'<tr><th scope="row">{esc(a)}</th><td>{b}</td></tr>' for a, b in rows)

    if e.get('archive'):
        when = L.t('from_archive_undated') if e.get('date_approx') else L.t('from_archive', d=L.date(e['date']))
    else:
        # Icons from Facebook: the date line links to the (first) post there.
        key = ('from_portfolio' if e.get('portfolio') else
               'first_shown' if e.get('history') or e.get('text_date') else 'published_on')
        if e.get('facebook'):
            key += '_fb'
        when = L.t(key, d=L.date(e['date']))
    when = esc(when)
    if e.get('facebook') and not e.get('archive'):
        when = (f'<a href="{esc(e["facebook"])}" target="_blank" rel="noopener nofollow" '
                f'title="{esc(L.t("facebook_post_title"))}">{when} →</a>')

    def caption(text):
        s, translated = L.tr.text(text)
        note = f'<p class="mt-note">{esc(L.t("machine_note"))}</p>' if translated and L.ui['machine_note'] else ''
        lang = '' if translated or L.code == 'ro' else ' lang="ro"'
        return f'<div class="post-text"{lang}>{text_html(s)}</div>{note}'

    info = ''
    if e['text']:
        label = L.t('caption_label')
        if e.get('history'):
            label += ' · ' + L.date(e.get('text_date') or e['date'])
        info += f'<p class="post-label">{esc(label)}</p>{caption(e["text"])}'

    if e.get('stages'):
        info += f'<p class="post-label">{esc(L.t("stages_label"))}</p>'
        offset = len(e['images'])
        for s in e['stages']:
            info += (f'<div class="stage"><a href="{full(s["images"][0])}" data-index="{offset}" aria-label="{esc(L.t("see_drawing"))}">'
                     f'<img loading="lazy" src="{small(s["images"][0])}" alt=""></a>'
                     f'<div><p class="stage-date">{esc(L.t("stage_date", d=L.date(s["date"])))}</p>'
                     + (caption(s['text']) if s['text'] else '') + '</div></div>')
            offset += len(s['images'])

    if e.get('history'):
        info += f'<p class="post-label">{esc(L.t("history_label"))}</p>'
        for h in e['history']:
            info += f'<details class="history"><summary>{esc(L.date(h["date"]))}</summary>{caption(h["text"])}</details>'

    related = [o for o in by_title.get(e['title'], []) if o is not e]
    if related:
        info += (f'<p class="post-label">{esc(L.t("related_label", n=len(related)))}</p><div class="related">'
                 + ''.join(f'<a href="{esc(rel(L.work(o), path))}" title="{esc(L.title(o) + " · " + L.work_date(o))}">'
                           f'<img loading="lazy" src="{thumb(o, path)}" alt=""></a>' for o in related[:12])
                 + '</div>')

    page_url = f'{SITE_URL}/{L.work(e)}' if SITE_URL else ''
    info += (f'<div class="v-cta"><p>{esc(L.t("cta_text_work" if e["theme"] == "proiecte" else "cta_text"))}</p><div class="cta-buttons">'
             f'{messenger_btn(L, "btn-primary")}'
             f'{whatsapp_btn(L, "btn-ghost", L.t("whatsapp_text_work" if e["theme"] == "proiecte" else "whatsapp_text_icon", t=title, url=page_url).strip(" :"))}</div></div>')

    pager = '<nav class="pager">'
    pager += (f'<a class="pager-prev" rel="prev" href="{esc(rel(L.work(prev), path))}"><span>‹ {esc(L.t("prev"))}</span>{esc(L.title(prev))}</a>'
              if prev else '<span></span>')
    pager += (f'<a class="pager-next" rel="next" href="{esc(rel(L.work(nxt), path))}"><span>{esc(L.t("next"))} ›</span>{esc(L.title(nxt))}</a>'
              if nxt else '<span></span>')
    pager += '</nav>'

    first = e['images'][0]
    return f'''<section class="work-page starry">
  <div class="wrap">
    <nav class="crumbs"><a href="{esc(rel(L.page('gallery'), path))}">← {esc(L.t('back_gallery'))}</a></nav>
    <article class="work">
      <div class="work-media">
        <a class="v-main" id="v-main" href="{full(first)}" target="_blank" rel="noopener" title="{esc(L.t('open_full'))}"><img id="v-img" src="{full(first)}" alt="{esc(title)}"></a>
        <p class="v-caption" id="v-caption"></p>
        {thumbs}
      </div>
      <div class="work-info">
        <h1>{esc(title)}</h1>
        <p class="v-date">{when}</p>
        <table class="facts-table"><tbody>{facts}</tbody></table>
        {info}
        {pager}
      </div>
    </article>
  </div>
</section>'''


def about_page(L, by_id, path):
    a = by_id.get(ABOUT)
    art = ''
    if a:
        art = (f'<figure class="about-art"><a href="{esc(rel(L.work(a), path))}"><img src="{esc(rel("img/full/" + a["images"][0], path))}" alt="{esc(L.title(a))}"></a>'
               f'<figcaption>{esc(L.t("about_caption", t=L.title(a)))}</figcaption></figure>')
    text, translated = L.tr.text(SITE_DATA['about'])
    note = f'<p class="mt-note">{esc(L.t("machine_note"))}</p>' if translated and L.ui['machine_note'] else ''
    return f'''<section class="section about">
  <div class="wrap about-inner">
    {art}
    <div>
      <p class="eyebrow">{esc(L.t('about_eyebrow'))}</p>
      <h1 class="h2">{esc(L.t('about_title'))}</h1>
      <div class="prose"{'' if translated or L.code == 'ro' else ' lang="ro"'}>{text_html(text)}</div>
      {note}
    </div>
  </div>
</section>'''


def technique_page(L, by_id, path):
    steps = ''.join(
        f'<li><span class="step-n">{esc(n)}</span><h2 class="h3">{esc(h)}</h2><p>{esc(p)}</p>'
        + (f'<p class="aside">{esc(aside)}</p>' if aside else '') + '</li>'
        for n, h, p, aside in L.ui['steps'])
    c = by_id.get(BEFORE_AFTER)
    ba = ''
    if c and c.get('stages'):
        link = esc(rel(L.work(c), path))
        ba = (f'<div class="before-after"><a href="{link}"><img src="{esc(rel("img/thumb/" + c["stages"][0]["images"][0], path))}" alt="">'
              f'<span>{esc(L.t("before_label"))}</span></a><div class="arrow" aria-hidden="true">→</div>'
              f'<a href="{link}"><img src="{thumb(c, path)}" alt="{esc(L.title(c))}"><span>{esc(L.t("after_label", t=L.title(c)))}</span></a></div>')
    return f'''<section class="section technique starry">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">{esc(L.t('technique_eyebrow'))}</p>
      <h1 class="h2">{esc(L.t('technique_title'))}</h1>
      <p>{esc(L.t('technique_intro'))}</p>
    </div>
    <ol class="steps">{steps}</ol>
    {ba}
  </div>
</section>'''


def orders_page(L, path):
    ticks = ''.join(f'<li>{t}</li>' for t in L.ui['orders_ticks'])
    return f'''<section class="section orders">
  <div class="wrap orders-inner">
    <div>
      <p class="eyebrow">{esc(L.t('orders_eyebrow'))}</p>
      <h1 class="h2">{esc(L.t('orders_title'))}</h1>
      <div class="prose">
        <p class="quote">{esc(L.t('orders_quote'))}</p>
        <ul class="ticks">{ticks}</ul>
        <p class="note">{esc(L.t('orders_note'))}</p>
      </div>
    </div>
    <aside class="contact-card">
      <h2 class="h3">{esc(L.t('contact_title'))}</h2>
      <p>{esc(L.t('contact_text'))}</p>
      <a class="btn btn-primary btn-block" href="{esc(SITE_DATA['facebook'])}" target="_blank" rel="noopener">{esc(L.t('facebook_btn'))}</a>
      {messenger_btn(L, 'btn-ghost btn-block')}
      {whatsapp_btn(L, 'btn-ghost btn-block', L.t('whatsapp_text'))}
      <a class="btn btn-ghost btn-block" href="mailto:{EMAIL}">{esc(L.t('email_btn'))}</a>
      <p class="contact-email"><a href="mailto:{EMAIL}">{EMAIL}</a></p>
    </aside>
  </div>
</section>'''


def privacy_page(L, path):
    def para(s):
        h = text_html(s)
        return h.replace('{email}', f'<a href="mailto:{EMAIL}">{EMAIL}</a>')
    sections = ''.join(f'<h2 class="h3">{esc(head)}</h2>' + para('\n\n'.join(paras))
                       for head, paras in L.ui['privacy_sections'])
    temp_note = '' if GA_ASK_CONSENT else f'<p class="temp-note">{esc(L.t("privacy_temp_note"))}</p>'
    return f'''<section class="section privacy">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">{esc(L.t('privacy_eyebrow'))}</p>
      <h1 class="h2">{esc(L.t('privacy_title'))}</h1>
      <p>{esc(L.t('privacy_updated', d=L.date(PRIVACY_UPDATED)))}</p>
    </div>
    <div class="prose privacy-text">{temp_note}{sections}</div>
  </div>
</section>'''


def root_page():
    links = ''.join(f'<li><a href="{c}/index.html" hreflang="{c}" lang="{c}">{esc(UI[c]["lang_name"])}</a></li>' for c in LANGS)
    return f'''<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(UI['ro']['site_name'])}</title>
<meta name="description" content="{esc(UI['ro']['meta_description'])}">
<link rel="icon" href="{FAVICON}">
<script>
  // Open the visitor's language (English or French), otherwise Romanian.
  (function () {{
    var langs = navigator.languages || [navigator.language || ''], pick = 'ro';
    for (var i = 0; i < langs.length; i++) {{
      var l = String(langs[i]).slice(0, 2).toLowerCase();
      if (l === 'ro' || l === 'en' || l === 'fr') {{ pick = l; break; }}
    }}
    location.replace(pick + '/index.html');
  }})();
</script>
<noscript><meta http-equiv="refresh" content="0; url=ro/index.html"></noscript>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="lang-choice">
<main class="wrap"><h1>{esc(UI['ro']['site_name'])}</h1><ul>{links}</ul></main>
</body>
</html>
'''


def main():
    global UI, SITE_DATA
    with open(os.path.join(SITE, 'content', 'ui.json'), encoding='utf-8') as f:
        UI = json.load(f)
    with open(os.path.join(SITE, 'data', 'lucrari.json'), encoding='utf-8') as f:
        data = json.load(f)
    SITE_DATA = data['site']
    works = data['lucrari']
    by_id = {}
    for e in works:
        by_id[e['id']] = e
        for alias in e.get('aliases', []):
            by_id[alias] = e
    by_title = {}
    for e in works:
        by_title.setdefault(e['title'], []).append(e)

    # Start clean, but keep the photos (make_images.ps1 maintains them).
    # Folders are only emptied: Windows refuses to delete one that is open somewhere.
    for name in os.listdir(PUBLIC) if os.path.isdir(PUBLIC) else []:
        p = os.path.join(PUBLIC, name)
        if name == 'img':
            continue
        if not os.path.isdir(p):
            os.remove(p)
            continue
        for folder, dirs, files in os.walk(p, topdown=False):
            for f in files:
                os.remove(os.path.join(folder, f))
            for d in dirs:
                try:
                    os.rmdir(os.path.join(folder, d))
                except OSError:
                    pass
    os.makedirs(os.path.join(PUBLIC, 'assets'), exist_ok=True)
    for name in ('style.css', 'site.js'):
        shutil.copy(os.path.join(SITE, 'assets', name), os.path.join(PUBLIC, 'assets', name))

    def write(path, content):
        full = os.path.join(PUBLIC, *path.split('/'))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

    langs = {c: Lang(c, UI) for c in LANGS}
    sitemap = []
    for c, L in langs.items():
        def alts(fn):
            return {o: fn(langs[o]) for o in LANGS}
        site_name = L.t('site_name')
        pages = [
            ('home', site_name, home_page(L, works, by_id, L.page('home'))),
            ('gallery', f'{L.t("gallery_title")} · {site_name}', gallery_page(L, works, L.page('gallery'))),
            ('available', f'{L.t("available_title")} · {site_name}', available_page(L, works, L.page('available'))),
            ('about', f'{L.t("about_title")} · {site_name}', about_page(L, by_id, L.page('about'))),
            ('technique', f'{L.t("technique_title")} · {site_name}', technique_page(L, by_id, L.page('technique'))),
            ('orders', f'{L.t("orders_title")} · {site_name}', orders_page(L, L.page('orders'))),
            ('privacy', f'{L.t("privacy_title")} · {site_name}', privacy_page(L, L.page('privacy'))),
        ]
        for key, title, body in pages:
            path = L.page(key)
            hero = by_id.get(HERO[0])
            write(path, layout(L, path, alts(lambda o, k=key: o.page(k)), title, L.t('meta_description'), body,
                               active=key if key != 'home' else '', image='img/full/' + hero['images'][0] if hero else ''))
            sitemap.append(path)
        for i, e in enumerate(works):
            path = L.work(e)
            text = L.tr.text(e['text'])[0] if e['text'] else ''
            desc = re.sub(r'\s+', ' ', text).strip()
            desc = (desc[:152].rsplit(' ', 1)[0] + '…') if len(desc) > 155 else desc
            body = work_page(L, e, works, by_title, path, works[i - 1] if i else None,
                             works[i + 1] if i + 1 < len(works) else None)
            write(path, layout(L, path, alts(lambda o, e=e: o.work(e)), f'{L.title(e)} · {site_name}',
                               desc or L.t('meta_description'), body, active='gallery', image='img/full/' + e['images'][0]))
            sitemap.append(path)
        # Search index for the gallery: folded text per work (title, theme, izvod, feast, caption).
        index = {}
        for e in works:
            parts = [L.title(e), e['title'], L.ui['themes'].get(e['theme'], ''), L.tr.term(e.get('izvod', '')),
                     L.feast(e['sarbatoare']) if e.get('sarbatoare') else '', L.tr.text(e['text'])[0]]
            index[e['id']] = re.sub(r'\s+', ' ', fold(' '.join(p for p in parts if p)))
        write(f'assets/search-{c}.js', 'window.SEARCH = ' + json.dumps(index, ensure_ascii=False) + ';\n')

    write('index.html', root_page())
    if SITE_URL:
        urls = ''.join(f'<url><loc>{SITE_URL}/{esc(p)}</loc></url>\n' for p in sitemap)
        write('sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
        write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n')

    # What still needs translating (Romanian is shown meanwhile).
    for c, L in langs.items():
        if c == 'ro':
            continue
        todo = os.path.join(SITE, 'translations', f'todo-{c}.json')
        missing = {'terms': L.tr.missing_terms, 'texts': L.tr.missing_texts}
        if missing['terms'] or missing['texts']:
            with open(todo, 'w', encoding='utf-8') as f:
                json.dump(missing, f, ensure_ascii=False, indent=1)
        elif os.path.exists(todo):
            os.remove(todo)
        print(f'{c}: {len(L.tr.missing_terms)} terms and {len(L.tr.missing_texts)} texts not yet translated')
    print(len(sitemap), 'pages written to', PUBLIC)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
