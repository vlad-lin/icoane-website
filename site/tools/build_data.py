"""Builds site/data/lucrari.json from the Facebook export (site/tools/build_site.py
then turns it into the pages).

Run from anywhere:  python site/tools/build_data.py
Also writes site/tools/images.txt (source<TAB>target name<TAB>used) for the image scripts.
"""
import datetime
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
# The private Facebook export lives in ../facebook-export (never published).
EXPORT = os.path.join(os.path.dirname(SITE), 'facebook-export')
POSTS = os.path.join(EXPORT, "this_profile's_activity_across_facebook", "posts")
# Posts published after the export was made, added by hand (see site/README.md).
NEW_POSTS = os.path.join(SITE, 'new-posts')
# Icons from the 2019-2020 archive (old-works/works.json); their photos are prepared by
# prepare_old_photos.ps1 from the private folder "poze vechi" (never published).
OLD_WORKS = os.path.join(SITE, 'old-works', 'works.json')
OLD_PHOTOS = os.path.join(os.path.dirname(SITE), 'poze vechi', '_pentru-site')


def fix(o):
    """Facebook exports UTF-8 text as latin-1 escapes; undo that."""
    if isinstance(o, str):
        try:
            return o.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return o
    if isinstance(o, list):
        return [fix(x) for x in o]
    if isinstance(o, dict):
        return {k: fix(v) for k, v in o.items()}
    return o


def load(path):
    with open(path, encoding='utf-8') as f:
        return fix(json.load(f))


# --- Manual curation -------------------------------------------------------
# Posts (by index in profile_posts_1.json) presenting historical icons painted
# by others (museums, churches, collections). Left out of the site.
PATRIMONIU = {680, 683, 688, 696, 788, 741, 746, 781, 827, 833, 879, 917, 930,
              970, 976, 988, 993, 1026, 1087, 1095, 1099, 1101, 1131, 1141,
              1148, 1150, 1185, 1011,
              # Found by the painter in her review (5 Nov 2026):
              891, 901, 997, 1005, 1008, 1030, 1041, 1106, 1111}
# Posts that are not artwork, or are uncaptioned re-uploads of another post.
# 1136 announces a contest winner (a private person).
SKIP = {813, 684, 685, 690, 691, 692, 697, 698, 1011, 674, 1136}
# Icons shown without their caption: 932 is about parcels broken on the way to customers,
# 1012 and 1014 announce a contest (the icon was its prize).
HIDE_TEXT = {932, 1012, 1014}


def facebook_link(media):
    """Link to a post on Facebook. The export has no post links, but each photo file is
    named with its Facebook photo id, and the photo's page shows the post's caption
    (also to visitors who are not logged in)."""
    return 'https://www.facebook.com/photo/?fbid=' + media['uri'].rsplit('/', 1)[1].split('.')[0]
# Titles for posts whose caption does not name the icon (checked against the photo).
TITLES = {
    755: 'Masa Raiului',
    842: 'Sfântul Ierarh Nectarie',
    1017: 'Buna Vestire',
    1015: 'Sfinții Martiri Brâncoveni',
    1071: 'Sfinții Martiri Brâncoveni',
    1125: 'Intrarea Domnului în Ierusalim',
    1065: 'Intrarea Domnului în Ierusalim',
    1012: 'Maica Domnului cu Pruncul',
    1014: 'Maica Domnului cu Pruncul',
    1153: 'Sfântul Mare Mucenic Gheorghe',
    1130: 'Iisus Hristos Mântuitorul',
    1163: 'Maica Domnului Îndurerată',
    1164: 'Maica Domnului Îndurerată',
    1197: 'Maica Domnului Îndurerată',
    1047: 'Rugul Aprins al Maicii Domnului',
    989: 'Sfinții Mari Mucenici Gheorghe și Dimitrie',
    1090: 'Pogorârea Sfântului Duh',
    1088: 'Sfânta Treime și Încoronarea Maicii Domnului',
    1199: 'Sfântul Ierarh Nectarie',
    1080: 'Icoană în lucru',
    1058: 'Icoană în lucru',
    1102: 'Icoană în lucru, pentru o Sfântă Biserică',
    1142: 'Icoană în lucru – „urzeala”',
    1136: 'Icoane pictate în atelierul nostru',
    1079: 'Icoane pictate în atelierul nostru',
    1131: 'Biserica de lemn a Mănăstirii Nicula',
    1141: 'Muzeul de Icoane pe Sticlă „Pr. Zosim Oancea”, Sibiel',
    1148: 'Icoane pe sticlă, sec. XVIII–XIX (Sibiel)',
    1150: 'Icoană veche – Muzeul ASTRA, Sibiu',
}

# Black-and-white works that are finished pieces, not drawings for a later icon.
FINISHED_BW = {921}

# Icons painted for a church, or shown standing in one (from their captions). They get the
# "Pentru biserici" filter in the gallery and the church section on the home page.
# A merged icon can be named by any of its posts.
CHURCH = {'p744', 'p777', 'p779', 'p755', 'p883', 'p893', 'p937', 'p938', 'p870', 'p842', 'p1068',
          'p1031', 'p786', 'p1091', 'p1105', 'p1110', 'p1129', 'p1130', 'p1123', 'p1164', 'p1165',
          'p1179', 'p1199', 'p971',
          # added 4 Nov 2026, found when the church places were restored
          'p763', 'p764', 'p840', 'p852', 'p853', 'p857', 'p877', 'p948', 'p949', 'p953', 'p975',
          'p1035', 'p1135', 'p1161',
          # Radio Trinitas belongs to the Romanian Orthodox Church (user: include it)
          'p1094'}
# "Destinație" set by hand, for public places that are not churches (user, 4 Nov 2026).
DESTINATION = {'p1094': 'Radio Trinitas'}
# The place of a church in a caption: "Biserică (Ortodoxă) din Dobrogea / jud Brașov / vestul României".
CHURCH_PLACE = re.compile(r'(?:[Bb]iseric|[Mm]ănăstir)\w*(?:\s+[Oo]rtodox\w*)?\s+din\s+'
                          r'((?:jud\.?\s+)?(?!România\b)[A-ZĂÂÎȘȚ]\w+(?:-[A-ZĂÂÎȘȚ]\w+)*|vestul României)')

MONTHS = ('ianuarie februarie martie aprilie mai iunie iulie august septembrie '
          'octombrie noiembrie decembrie').split()

THEMES = [
    ('maica', 'Maica Domnului'),
    ('praznice', 'Iisus Hristos și praznice'),
    ('sfinti', 'Sfinți și arhangheli'),
    ('masa', 'Masa Raiului'),
    ('eroi', 'Martiri și eroi'),
    ('altele', 'Alte lucrări'),
    ('proiecte', 'Alte proiecte'),  # her side projects, not icons (Micul Prinț)
]

# Iconographic subjects: (pattern on diacritic-free lowercase text, title, theme).
# The earliest match in the caption wins; on ties, the earlier (more specific) entry.
SUBJECTS = [
    (r'masa raiului|mesei raiului|mesei de rai|ospatul ceresc', 'Masa Raiului', 'masa'),
    (r'treime si incoronarea', 'Sfânta Treime și Încoronarea Maicii Domnului', 'maica'),
    (r'incoronar(ea|ii) maicii', 'Încoronarea Maicii Domnului', 'maica'),
    (r'rugul aprins|rugului aprins', 'Rugul Aprins al Maicii Domnului', 'maica'),
    (r'buna vestire|bunei vestiri', 'Buna Vestire', 'maica'),
    (r'adormirea maicii|adormirii maicii', 'Adormirea Maicii Domnului', 'maica'),
    (r'nasterea maicii|nasterii maicii', 'Nașterea Maicii Domnului', 'maica'),
    (r'intrarea (maicii domnului )?in biserica|intrarea in biserica a maicii', 'Intrarea în Biserică a Maicii Domnului', 'maica'),
    (r'izvorul tamaduirii', 'Izvorul Tămăduirii', 'maica'),
    (r'care alapteaza|galaktotro', 'Maica Domnului „Cea care alăptează”', 'maica'),
    (r'indurerata', 'Maica Domnului Îndurerată', 'maica'),
    (r'floarea (neprihanita|nepieritoare|de crin)', 'Maica Domnului „Floarea neprihănită”', 'maica'),
    (r'(maica domnului|fecioara maria) cu pruncul', 'Maica Domnului cu Pruncul', 'maica'),
    (r'nasterea domnului|nasterii domnului|nasterea lui hristos|s a nascut hristos|craciun', 'Nașterea Domnului', 'praznice'),
    (r'botezul domnului|boboteaz', 'Botezul Domnului', 'praznice'),
    (r'intampinarea domnului', 'Întâmpinarea Domnului', 'praznice'),
    (r'intrarea (domnului )?(nostru iisus hristos )?in ierusalim|floriilor|stalparilor', 'Intrarea Domnului în Ierusalim', 'praznice'),
    (r'cina cea de taina', 'Cina cea de Taină', 'praznice'),
    (r'plangerea|vinerea mare|marea vineri', 'Plângerea lui Iisus Hristos', 'praznice'),
    (r'invierea', 'Învierea Domnului', 'praznice'),
    (r'inaltarea sfintei cruci|inaltarii sfintei cruci', 'Înălțarea Sfintei Cruci', 'praznice'),
    (r'inaltarea domnului|inaltarea lui hristos|inaltarii domnului', 'Înălțarea Domnului', 'praznice'),
    (r'pogorarea|pogorarii|cincizecimea|rusalii', 'Pogorârea Sfântului Duh', 'praznice'),
    (r'troita a treimii|trei fete', 'Sfânta Troiță a Treimii într-un singur trup', 'praznice'),
    (r'sfanta treime|sf troita', 'Sfânta Treime', 'praznice'),
    (r'schimbarea la fata', 'Schimbarea la Față', 'praznice'),
    (r'vita de vie', 'Iisus Hristos – Vița de vie', 'praznice'),
    (r'euharistic', 'Hristos Euharistic', 'praznice'),
    (r'imparat si mare arhiereu', 'Iisus Hristos Împărat și Mare Arhiereu', 'praznice'),
    (r'inconjurat de sfintii apostoli', 'Iisus Hristos înconjurat de Sfinții Apostoli', 'praznice'),
    (r'judecata de apoi|judecatii de apoi|infricosatoare[ai]? judecat|groaznica judecata', 'Judecata de Apoi', 'praznice'),
    (r'scara raiului', 'Scara Raiului', 'praznice'),
    (r'adam si eva|izgonirii lui adam', 'Adam și Eva în Rai', 'praznice'),
    (r'proroc(ului)? ilie|prooroc ilie|ilie tesviteanul', 'Sfântul Proroc Ilie', 'sfinti'),
    (r'gheorghe si dimitrie', 'Sfinții Mari Mucenici Gheorghe și Dimitrie', 'sfinti'),
    (r'gheorghe', 'Sfântul Mare Mucenic Gheorghe', 'sfinti'),
    (r'dimitrie|dumitru', 'Sfântul Mare Mucenic Dimitrie', 'sfinti'),
    (r'nicolae|nicoale', 'Sfântul Ierarh Nicolae', 'sfinti'),
    (r'haralambie', 'Sfântul Sfințit Mucenic Haralambie', 'sfinti'),
    (r'parascheva', 'Sfânta Cuvioasă Parascheva', 'sfinti'),
    (r'nectarie', 'Sfântul Ierarh Nectarie', 'sfinti'),
    (r'stelian', 'Sfântul Cuvios Stelian Paflagonul', 'sfinti'),
    (r'\bmina\b', 'Sfântul Mare Mucenic Mina', 'sfinti'),
    (r'\bandrei\b', 'Sfântul Apostol Andrei', 'sfinti'),
    (r'apostol(ul)? filip', 'Sfântul Apostol Filip', 'sfinti'),
    (r'petru si pavel', 'Sfinții Apostoli Petru și Pavel', 'sfinti'),
    (r'arhangheli(i)? mihail si gavriil|arhanghelii', 'Sfinții Arhangheli Mihail și Gavriil', 'sfinti'),
    (r'arhanghel(ul)? mihail', 'Sfântul Arhanghel Mihail', 'sfinti'),
    (r'constantin si elena', 'Sfinții Împărați Constantin și Elena', 'sfinti'),
    (r'paisie', 'Sfântul Cuvios Paisie Aghioritul', 'sfinti'),
    (r'efrem', 'Sfântul Efrem cel Nou', 'sfinti'),
    (r'\birina\b', 'Sfânta Mare Muceniță Irina', 'sfinti'),
    (r'eugenia', 'Sfânta Muceniță Eugenia', 'sfinti'),
    (r'\bzoe\b', 'Sfânta Muceniță Zoe', 'sfinti'),
    (r'martin de tours', 'Sfântul Martin de Tours', 'sfinti'),
    (r'taierea capului', 'Tăierea capului Sfântului Ioan Botezătorul', 'sfinti'),
    (r'nasterea sfantului ioan', 'Nașterea Sfântului Ioan Botezătorul', 'sfinti'),
    (r'ioan botezatorul', 'Sfântul Ioan Botezătorul', 'sfinti'),
    (r'nichifor', 'Sfântul Nichifor Leprosul', 'sfinti'),
    (r'sfantul (ierarh )?alexandru|patriarhul constantinopolului', 'Sfântul Ierarh Alexandru', 'sfinti'),
    (r'chiril si (sfantul )?nichita', 'Sfinții Chiril și Nichita', 'sfinti'),
    (r'chiril', 'Sfântul Ierarh Chiril', 'sfinti'),
    (r'simeon', 'Dreptul Simeon', 'sfinti'),
    (r'trei ierarhi', 'Sfinții Trei Ierarhi', 'sfinti'),
    (r'ioan scararul', 'Sfântul Ioan Scărarul', 'sfinti'),
    (r'marturisitori(i)? (ardeleni|transilvaneni|din ardeal)|sase sfinti', 'Sfinții Mărturisitori Ardeleni', 'eroi'),
    (r'brancoveni', 'Sfinții Martiri Brâncoveni', 'eroi'),
    (r'gafencu|sfantul inchisorilor', 'Valeriu Gafencu, „Sfântul Închisorilor”', 'eroi'),
    (r'temnitele comuniste|comunismul a umplut', 'Martirii din temnițele comuniste', 'eroi'),
    (r'avram iancu|horea|eroi ai (neamului|natiunii)|noi am facut din voi icoane', 'Martiri și eroi ai neamului românesc', 'eroi'),
    (r'micul print', 'Micul Prinț', 'proiecte'),
    (r'maica domnului|fecioara maria', 'Maica Domnului', 'maica'),
    (r'mantuitorul', 'Iisus Hristos Mântuitorul', 'praznice'),
]
SUBJECTS = [(re.compile(rx), title, theme) for rx, title, theme in SUBJECTS]

BULLETS = '•▪▫⊹✨❈✤❀✧◘⚜✠~·-–—*🌿🌻🌼🌟🌸❤♥︎️ \t'


def clean_line(s):
    s = s.strip()
    while s and (s[0] in BULLETS or unicodedata.category(s[0]) in ('So', 'Sk', 'Mn', 'Cf')):
        s = s[1:].strip()
    return s


def extract_title(text):
    lines = [clean_line(l) for l in text.split('\n')]
    lines = [l for l in lines if l]
    if not lines:
        return ''
    first = lines[0]
    m = re.search(r'«\s*([^«»]{3,90}?)\s*»', first) or re.search(r'„\s*([^„“”"]{3,90}?)\s*[“”"]', first)
    if m:
        t = m.group(1)
    else:
        t = first
        # Drop a leading feast date like "21 mai:" / "6 august -"
        t = re.sub(r'^\d{1,2}\s+(%s)(\s+\d{4})?\s*[:\-–]\s*' % '|'.join(MONTHS), '', t, flags=re.I)
        t = re.split(r'\s+[-–~]\s+|\s*\(|:\s', t)[0]
    t = t.strip(' .,:;-–~«»„“”"')
    if len(t) > 80:
        t = t[:77].rsplit(' ', 1)[0] + '…'
    return t


def simplify(s):
    s = s.lower().replace('ş', 'ș').replace('ţ', 'ț')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[-–_\s]+', ' ', s)


def subject_of(text):
    """Returns (title, theme) of the main subject, preferring the first line."""
    first = text.strip().split('\n', 1)[0]
    for source in (first, text):
        s = simplify(source)
        best = None
        for order, (rx, title, theme) in enumerate(SUBJECTS):
            m = rx.search(s)
            if m and (best is None or (m.start(), order) < best[0]):
                best = ((m.start(), order), title, theme)
        if best:
            return best[1], best[2]
    return None, 'altele'


# A phrase ends at a bracket, newline or sentence end (but not inside "sec. XIX").
END = r'(?=\)|\n|$|\.\s+(?!X|V|I)[A-ZĂÂÎȘȚŞŢ„«]|\s+[•▪▫⊹])'


def find(pattern, text):
    m = re.search(pattern + END, text)
    return m.group(1).strip(' ,.;:)(') if m else ''


def details(text):
    d = {}
    izvod = find(r'(?i:\bizvod)\b[\s:\-–]*(?:după\s+)?([^)\n•▪▫⊹]{4,110}?)', text)
    if not izvod:
        izvod = find(r'(?i:studiu|inspirat[ăa]?) după (?:o |un )?((?i:icoan|lucrare)[^\n•▪▫⊹]{4,140}?)', text)
    izvod = re.sub(r'\s+', ' ', izvod).strip(' -–,')
    if izvod.count('(') > izvod.count(')'):
        izvod += ')'
    # Skip fragments that are prose rather than a source ("..., iar icoana rezultată").
    if len(izvod) > 6 and not re.search(r'\b(am|iar|care|pe care)\b', izvod) and izvod.lower() not in ('original', 'tipar'):
        d['izvod'] = izvod[0].upper() + izvod[1:]
    dim = re.search(r'(?<!\d)(\d{1,3})\s*[x×]\s*(\d{1,3})\s*(cm|mm)', text, re.I)
    if dim:
        d['dimensiuni'] = f'{dim.group(1)} × {dim.group(2)} {dim.group(3).lower()}'
    feast = re.search(r'\b(\d{1,2})\s+(%s)\b' % '|'.join(MONTHS), text.split('\n')[0] if text else '', re.I)
    if feast:
        d['sarbatoare'] = f'{int(feast.group(1))} {feast.group(2).lower()}'
    low = text.lower()
    if re.search(r'nu (este|va fi|mai este) disponibil', low):
        d['disponibilitate'] = 'Nu este disponibilă — se poate picta din nou, la comandă'
    # "este disponibilă" = ready now; "disponibilă la comandă" = can be painted to order.
    elif re.search(r'(?<!nu )\b(este|e) disponibil\w*\b(?!\s+la comand)', low):
        d['disponibilitate'] = 'Disponibilă'
    elif re.search(r'comand', low):
        d['disponibilitate'] = 'Realizată la comandă'
    return d


def norm(s):
    return re.sub(r'\W+', ' ', s.lower()).strip()[:160]


# --- Customer references -----------------------------------------------------
# Rule (user, 6 Nov 2026): no customer names and no photos of customers. Anything else
# about a customer (a town, "a lovely family", "a special lady", a priest, a gift) may stay.
# Captions are cleaned sentence by sentence: CUT removes a name from a sentence, DROP
# removes a sentence that is about a named person. (Until 6 Nov 2026 towns, families
# and dedications were removed too: backups/2026-11-06-before-relaxing-customer-rules/.)
PLACE = 'place'
CHURCH_CLIENT = re.compile(r'[Bb]iseric|[Mm]ănăstir')
PRIVATE_CLIENT = re.compile(r'preot|famili|doamn|prieten|client|cuplu|\bsoț', re.I)
CUT = [
    (r'\s*pentru prietena noastră\s*@\w+', ''),   # Facebook tag of a person
    # a name stated outright ("numit Elias", "cu numele Martin", "soției sale, Irina")
    (r'(adorabil|om minunat|unei persoane),?\s*(?:numit|cu numele)\s+[A-ZĂÂÎȘȚ]\w+', r'\1'),
    (r'(soției sale),\s*[A-ZĂÂÎȘȚ]\w+', r'\1'),
    (r'(copil botezat),\s*[A-ZĂÂÎȘȚ]\w+', r'\1'),
    (r'prietenului nostru Andrei,', 'unui prieten al nostru,'),
    (r'lui Andrei, unul dintre', 'unuia dintre'),
    (r'lui Andrei, un deosebit', 'unui deosebit'),
    # a name given through the saint ("care poartă numele Sfântului Filip")
    (r'(doamne|din Cluj|copil),?\s*(?:care|ce)\s+poartă\s+numele\s+«?Sf\w+\s+«?\w+»?', r'\1'),
    (r',?\s*care au primit la botez numele celor doi sfinți', ''),
    (r'\s*care au fost botezați cu numele celor doi sfinți', ''),
    (r'de ziua numelui său «Zoe»,\s+care se tâlcuiește a fi «viață»', 'de ziua numelui său'),
]
CUT = [(re.compile(c[0]), c[1], len(c) > 2) for c in CUT]
DROP = re.compile(
    r'(?i:câștigător|concurs)|@\w|'                 # the contest (its winner) and Facebook tags
    r'[A-ZĂÂÎȘȚ][a-zăâîșț]+, unul dintre prietenii|'
    r'(?i:la mulți ani)\W*,\s*(?!tuturor|celor|prietenilor|sărbători)[A-ZĂÂÎȘȚ][a-zăâîșț]+\b[^!\n]{0,80}!')
# Sentences about historical places (the Antim Monastery icon, museums) are never customer references.
HISTORY = re.compile(r'Mănăstir|Antim|Muzeu|moaște')
# Sentence boundary: after . ! ? … (and any emoji), before a capital or bullet.
# Abbreviations such as "sec.", "Sf.", "Pr.", "jud." do not end a sentence.
SENTENCE = re.compile(r'(?<=[.!?…])(?<!\bsec\.)(?<!\bSf\.)(?<!\bPr\.)(?<!\bjud\.)(?<!\bMc\.)'
                      r'((?:[^\w\s.!?…]){0,3}\s+)(?=[A-ZĂÂÎȘȚ„«"(•◘▪▫⊹~-])')


def clean_customers(text):
    out = []
    for line in text.split('\n'):
        parts = SENTENCE.split(line)
        # parts = [sentence, separator, sentence, separator, ...]
        kept = []
        for k in range(0, len(parts), 2):
            sent = parts[k]
            sep = parts[k + 1] if k + 1 < len(parts) else ''
            new = sent
            church = bool(CHURCH_CLIENT.search(sent)) and not PRIVATE_CLIENT.search(sent)
            for rx, rep, place in CUT:
                if not (place and church):
                    new = rx.sub(rep, new)
            if new != sent:
                new = re.sub(r'\s+([,.!?…)])', r'\1', new)
                new = re.sub(r',\s*([.!?…])', r'\1', new)
                new = re.sub(r'\(\s*\)', '', new)
                new = re.sub(r'\(\s+', '(', new)
                new = re.sub(r'([^\s]) {2,}', r'\1 ', new).rstrip(' ,')
                body = clean_line(new)
                if body and body[0].islower():
                    new = new[:len(new) - len(body)] + body[0].upper() + body[1:]
                words = re.findall(r'\w+', new)
                if len(words) < 4 or (len(words) < 7 and re.match(r'\W*(?:Și\s+)?[Dd]e aceas?t[aă] dată\b', new)):
                    new = ''
            if new and DROP.search(new) and not HISTORY.search(new) and not church:
                new = ''
            if new:
                kept.append(new + sep)
        cleaned = ''.join(kept).rstrip()
        if cleaned != line.rstrip() and not clean_line(cleaned):
            continue  # line had only customer sentences: remove it entirely
        out.append(cleaned)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip()


# --- Old "in progress" wording (user, 5 Nov 2026) ----------------------------
# Posts written while an icon was still being painted ("icoană în lucru", "voi picta",
# "vă voi prezenta în curând") are long finished now. Each pair is an exact phrase of
# the cleaned caption and its replacement ('' removes it). Offers to paint an icon
# again ("va fi pictată din nou la comandă") are not in-progress notes and stay.
# A phrase that no longer matches anything is reported by the build.
REWORD = [
    # stages (drawings and half-painted icons shown under "Etapele lucrării")
    ('nostru, este din nou încă în lucru (297', 'nostru (297'),
    ('»  În lucru, încă o  iconiță', '» – încă o iconiță'),
    (' - Din nou, în lucru o iconiță pe sticlă', ' - Din nou, o iconiță pe sticlă'),
    (' - o nouă iconiță în lucru', ' - o nouă iconiță'),
    ('❈ Icoană în lucru: «Iisus Hristos – Vița de vie», izvod', '❈ «Iisus Hristos – Vița de vie», izvod'),
    ('Icoană  în lucru: «Iisus Hristos – Vița de vie»', '«Iisus Hristos – Vița de vie»'),
    ('icoană pe sticlă (în lucru)', 'icoană pe sticlă'),
    ('icoană pe sticlă, în lucru.', 'icoană pe sticlă.'),
    ('cu bucurie lucrăm o icoană', 'cu bucurie am pictat o icoană'),
    ('O nouă icoană în lucru, prima etapă în tuș cu penița.', 'Prima etapă: desenul în tuș cu penița.'),
    ('Gavriil» - icoană în lucru', 'Gavriil»'),
    ('este realizată la comandă, deci nu va fi disponibilă', 'a fost realizată la comandă, deci nu este disponibilă'),
    (' - icoană în lucru (izvod Șcheii', ' (izvod Șcheii'),
    ('[13x18 cm], deocamdată în lucru.', '[13x18 cm].'),
    ('Adam și Eva - icoană în lucru', 'Adam și Eva'),
    ('de asemenea, în continuare pe „dosul”  sticlei  voi picta icoana, în tempera  cu emulsie de ou.',
     'tot pe „dosul” sticlei am pictat apoi icoana, în tempera cu emulsie de ou.'),
    ('❈ Icoană în lucru: «Sfântul Mare Mucenic Gheorghe»', '❈ «Sfântul Mare Mucenic Gheorghe» – desenul icoanei'),
    ('Icoana pe sticlă al cărei desen vi-l prezint astăzi  urmează a fi pictată, în  tempera cu emulsie.\n'
     'Va fi prima icoană lucrată în atelierul nostru, comandată din  continentul american.',
     'Icoana a fost pictată apoi în tempera cu emulsie, la comandă, pentru continentul american.'),
    ('care va fi realizată în atelierul nostru.', 'realizată în atelierul nostru.'),
    ('împreună cu următoarele trei pe care vi le voi prezenta în aprilie-iunie, vor împodobi',
     'împreună cu alte trei, împodobește'),
    ('Trei dintre ele vor fi realizate de asemenea', 'Trei dintre ele au fost realizate de asemenea'),
    ('deocamdată diferențiate doar prin detalii grafice; peste câteva zile și prin detalii cromatice...',
     'diferențiate prin detalii grafice și, după pictare, prin detalii cromatice.'),
    (' - Icoană în lucru (57x62 cm)', ' (57x62 cm)'),
    ('într-o nouă icoană în curs de realizare în atelierul nostru, de această dată  lucrată pentru',
     'într-o nouă icoană pictată în atelierul nostru, de această dată pentru'),
    ('Sfântul Nectarie - din nou în lucru pentru o  sfântă Biserică', 'Sfântul Nectarie - din nou, pentru o sfântă Biserică'),
    ('»  - icoană în lucru (22x26 cm)', '» (22x26 cm)'),
    ('a  „ Rugului Aprins al Născătoarei de Dumnezeu ” se conturează...\n'
     '• Deocamdată am finalizat desenul în tuș cu penița  (pe sticlă : 30x42 cm)',
     'a „ Rugului Aprins al Născătoarei de Dumnezeu ”: desenul în tuș cu penița (pe sticlă: 30x42 cm)'),
    ('Gavriil - Icoană în lucru', 'Gavriil'),
    ('•  Icoană în lucru (15x21 cm)', '•  Icoană pe sticlă (15x21 cm)'),
    ('O nouă icoană în lucru...', 'O nouă icoană...'),
    ('\n• Icoană  în lucru ...', ''),
    ('• În lucru pentru o Sfântă Biserică', '• Pentru o Sfântă Biserică'),
    (')... Icoană în lucru...', ')...'),
    ('într-o icoană pe sticlă în lucru.', 'într-o icoană pe sticlă.'),
    ('În atelierul nostru va fi prima reprezentare', 'În atelierul nostru, este prima reprezentare'),
    ('Icoană pe sticlă , din nou în lucru.', 'Icoană pe sticlă, pictată din nou.'),
    ('Icoana se realizează după același izvod', 'Icoana a fost realizată după același izvod'),
    (' ( în lucru,din nou)', ''),
    (' În 2022 vor fi "Intrarea în Ierusalim" și "Rugul Aprins "...Deocamdată!', ''),
    ('\n✧ În curând vă voi prezenta-o și pictată', ''),
    (', etapă în care se află lucrarea   a cărei temă este inspirată', '. Tema lucrării este inspirată'),
    (' Vă voi prezenta personajele ( pe care le-ați recunoscut, cu siguranță ) la finalizarea lucrării .', ''),
    ('( pe spatele sticlei ), etapă aproape finalizată. Va urma apoi pictura',
     '( pe spatele sticlei ); urmează pictura'),
    ('Va fi o icoană mare ( 37 x 49 cm )', 'Este o icoană mare (37 x 49 cm)'),
    (', probabil va fi prima icoană pe sticlă', ', probabil prima icoană pe sticlă'),
    ('pe care am pictat-o pe sticlă în atelierul nostru o voi prezenta în zilele următoare fiindcă cinstirea',
     'a fost pictată pe sticlă în atelierul nostru; cinstirea'),
    # captions of finished icons that announce work still to come
    (', foarte ușor accidentată, în curs de reparație.', '.'),
    (' În perioada următoare vă voi prezenta o nouă icoană a sfântului.', ''),
    ('Urmează încă o comandă pentru această temă, vă voi prezenta-o în martie, cu aproximație.', ''),
    ('Tot ceea ce voi lucra în anul viitor vă voi prezenta aici (icoana în lucru și finalizată) cum am procedat '
     'și în anul care va fi curând „anul trecut”.', ''),
    ('! Tot ceea ce voi lucra în anul viitor vă voi prezenta aici, cum am procedat și în anul care va fi  curând '
     '„anul trecut”', '!'),
    ('◘ Două  lucrări cu  această temă iconografică (comandate cu ceva timp în urmă) urmează a fi realizate '
     'curând, una dintre ele va fi realizată în varianta clasică, cealaltă va fi personalizată  (cu sfântul '
     'Ioan Botezatorul în rombul Sfântului Nicolae, rombul sfintei Parascheva rămânând neschimbat)', ''),
    ('• În curând (octombrie - noiembrie) încă o  frumoasă icoană  cu această temă, mult mai complexă, va fi '
     'realizată în atelierul nostru, de asemenea pentru o  Sfântă Biserică.', ''),
    (' În perioada următoare voi picta două icoane asemănătoare acesteia, una dintre ele în luna aprilie, '
     'cealaltă în iulie-august ( conform programărilor ) . Mă-ntreb cum vă voi prezenta ( vouă, prietenilor '
     'acestei pagini ) fiecare dintre aceste icoane... Pictată " după " ... sau " în timp de " ...război ?', ''),
    ('• În curând vă voi prezenta și cea mai recentă variantă a acestei teme', ''),
    ('♦ Încă nu am realizat în atelierul nostru icoana Sfântului Apostol Andrei , avem însă o comandă pe care '
     'o vom onora în curând', ''),
    ('✤ În perioada următoare vă voi prezenta această deosebită lucrare într-o ramă care va fi sculptată '
     'special pentru ea', ''),
    ('va pleca in curând spre o Sfânta Biserică.', 'a plecat spre o Sfântă Biserică.'),
    (' Foarte  curând vom realiza din nou această temă, comandată în București, de această dată.', ''),
    ('V-aș mulțumi foarte mult dacă ați aprecia printr-un „like” varianta care vă place. Opinia dumneavoastră  va  '
     'fi importantă pentru îmbunătățirea aspectului următoarei icoane cu această temă, pe care o vom realiza curând.', ''),
    ('• Următoarea icoană cu această temă va avea ca model doar una dintre cele patru, adică icoana  care în '
     'această postare va primi cele mai multe inimioare de la dumneavoastră. Mulțumim!', ''),
    ('voi realiza această icoană în stilul meu, dacă sfântul îmi va permite. Dacă nu-mi va permite, voi ști și  '
     '(desigur) nu voi continua', 'am realizat această icoană în stilul meu.'),
    ('• Credeți că hotărârea de-a picta această icoană catolică în stilul meu este corectă?  Toate aceste emoții '
     'și întrebări vin din provocarea', '• Au fost multe emoții și întrebări, venite din provocarea'),
    # Facebook-only references (comments, likes), meaningless on the site (user, 6 Nov 2026)
    (', iar  în comentarii vă voi prezenta primele două icoane, împodobite cu flori într-o sfântă Biserică', '.'),
    (' ( în comentarii :  icoana cu rama pictată)', ''),
    ('Dacă veți aprecia , vom considera că vă place și o ramă pictată...', ''),
    ('va fi  trimisă  la Paris, cu mare bucurie.', 'a fost trimisă la Paris, cu mare bucurie.'),
    ('• Va fi a doua icoană a «Sfântului Efrem»', '• Este a doua icoană a «Sfântului Efrem»'),
    ('• Va fi prima icoană a «Sfântului Efrem»', '• Este prima icoană a «Sfântului Efrem»'),
    ('◘ Va fi prima icoană  a «Sfântului Apostol Andrei»', '◘ Este prima icoană a «Sfântului Apostol Andrei»'),
    ('• A doua este așteptată într-o sfântă Biserică; va fi alături de alte câteva icoane pictate în atelierul nostru',
     '• A doua a fost pictată pentru o sfântă Biserică, alături de alte câteva icoane pictate în atelierul nostru'),
    ('O icoană cu această temă a fost comandată din nou, este programată în vară pentru a fi realizată după un alt '
     'izvod țărănesc, probabil Savu Moga.', ''),
    ('Icoană în "lucru"... Desenul', 'Cum se lucrează o icoană pe sticlă... Desenul'),
    # restored with the relaxed customer rule (6 Nov 2026)
    ('de această dată va ajunge curând la Brașov.', 'de această dată a ajuns la Brașov.'),
    ('Urmează acum, identică, o a doua icoană cu această temă, care va merge la Oradea.',
     'A urmat, identică, o a doua icoană cu această temă, care a mers la Oradea.'),
    ('Icoana va pleca cu bucurie la Brăila, unde este așteptată.', 'Icoana a plecat cu bucurie la Brăila.'),
    ('Peste câteva zile, iconița va fi dăruită  unui om minunat', 'Iconița a fost dăruită unui om minunat'),
    (' pe care vi-l voi prezenta în zilele următoare', ''),
    (' (foto în comentarii)', ''),
    ('este al noii icoane care va ajunge întreagă la Arad.', 'este al noii icoane, care a ajuns întreagă la Arad.'),
    ('pentru a fi cadoul perfect care va fi dăruit în 18 Decembrie la Râmnicu Vâlcea',
     'pentru a fi cadoul perfect, dăruit pe 18 decembrie la Râmnicu Vâlcea'),
    ('căreia i se va oferi această icoană', 'căreia i s-a oferit această icoană'),
    ('• Prima dintre ele este așteptată la Arad; va fi un cadou deosebit pentru o doamnă specială',
     '• Prima dintre ele a plecat la Arad, un cadou deosebit pentru o doamnă specială'),
    ('pentru a fi dăruită  peste câteva zile unui om minunat', 'pentru a fi dăruită unui om minunat'),
    ('va pleca în curând la Sibiu', 'a plecat la Sibiu'),
    ('va pleca mâine dimineață spre Oradea unde va reprezenta', 'a plecat spre Oradea, unde a fost'),
]
REWORD_USED = set()


def reword(text):
    for k, (old, new) in enumerate(REWORD):
        if old in text:
            text = text.replace(old, new)
            REWORD_USED.add(k)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


# --- Reposts of the same icon -------------------------------------------------
# The same icon was often re-posted in later years, on its feast day. Entries whose
# main photos are near-identical (hash_images.ps1) become one entry; the other
# captions are kept as its history. Up to 17 of 256 bits differ for re-edited or
# re-cropped photos of one icon; two paintings of the same izvod differ more.
SAME_ICON = 17
GENERIC_TITLES = {'Maica Domnului', 'Iisus Hristos Mântuitorul', 'Icoană pe sticlă'}


# Page addresses already published (tools/page_ids.txt): a merged page keeps the one listed.
with open(os.path.join(HERE, 'page_ids.txt'), encoding='utf-8') as _f:
    PAGE_IDS = {line.strip() for line in _f if line.strip() and not line.startswith('#')}


def merge_reposts(entries):
    hash_file = os.path.join(HERE, 'hashes.txt')
    if not os.path.exists(hash_file):
        return entries
    hashes = {}
    with open(hash_file, encoding='utf-8-sig') as f:
        for line in f:
            name, value = line.strip().split('\t')
            hashes[name] = int(value, 16)

    def dist(a, b):
        return bin(hashes[a] ^ hashes[b]).count('1') if a in hashes and b in hashes else 999

    # Compilation posts show several different icons, each matching another post: never merged.
    def compilation(e):
        matched = [img for img in e['images']
                   if any(o is not e and dist(img, o['images'][0]) <= SAME_ICON for o in entries)]
        return len(matched) > 1
    single = [e for e in entries if not compilation(e)]
    parent = {e['id']: e['id'] for e in single}

    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for k, a in enumerate(single):
        for b in single[k + 1:]:
            if dist(a['images'][0], b['images'][0]) <= SAME_ICON:
                parent[root(a['id'])] = root(b['id'])
    groups = {}
    for e in single:
        groups.setdefault(root(e['id']), []).append(e)

    merged = {}
    for members in groups.values():
        if len(members) == 1:
            continue
        members.sort(key=lambda e: e['date'])
        # The page address and main photo stay with the post chosen when the site went live
        # (longest original caption): the addresses are indexed. What the page shows (caption
        # and facts such as availability) comes from the most recent post (user, 6 Nov 2026).
        published = [m for m in members if m['id'] in PAGE_IDS]
        home = published[0] if published else max(members, key=lambda e: len(e['text']))
        main = ([m for m in members if m['text']] or [home])[-1]
        named = [m for m in members if int(m['id'][1:]) in TITLES and m['id'][0] == 'p']
        specific = [m for m in members if m['title'] not in GENERIC_TITLES]
        if named:
            best = named[0]
        elif specific:
            best = max(specific, key=lambda m: [s['title'] for s in specific].count(m['title']))
        else:
            best = main
        e = dict(main, id=home['id'], title=best['title'], theme=best['theme'], date=members[0]['date'])
        if e['date'] != main['date']:
            e['text_date'] = main['date']
        # The date line shows the first post's date, so it links to the first post.
        if members[0].get('facebook'):
            e['facebook'] = members[0]['facebook']
        else:
            e.pop('facebook', None)
        if any(m.get('portfolio') for m in members) and members[0].get('portfolio'):
            e['portfolio'] = True
        else:
            e.pop('portfolio', None)
        images = list(home['images'])
        for m in members:
            for img in m['images']:
                if all(dist(img, x) > SAME_ICON for x in images):
                    images.append(img)
        e['images'] = images
        for m in reversed(members):
            for key in ('izvod', 'dimensiuni', 'sarbatoare', 'disponibilitate'):
                if key in m and key not in e:
                    e[key] = m[key]
        stages = [s for m in members for s in m.get('stages', [])]
        if stages:
            e['stages'] = sorted(stages, key=lambda s: s['date'])
        history = [{'date': m['date'], 'text': m['text']} for m in reversed(members)
                   if m is not main and m['text'] and norm(m['text']) != norm(main['text'])]
        if history:
            e['history'] = history
        e['aliases'] = [m['id'] for m in members if m is not home]
        for m in members:
            merged[m['id']] = e
    out, done = [], set()
    for e in entries:
        target = merged.get(e['id'], e)
        if id(target) not in done:
            done.add(id(target))
            out.append(target)
    out.sort(key=lambda e: (e['date'], e['id']), reverse=True)
    return out


def main():
    posts = load(os.path.join(POSTS, 'profile_posts_1.json'))
    # Colour saturation per image (from measure_colour.ps1); ink drawings measure ~0.
    saturation = {}
    colour_file = os.path.join(HERE, 'colour.txt')
    if os.path.exists(colour_file):
        with open(colour_file, encoding='utf-8-sig') as f:
            for line in f:
                name, value = line.strip().split('\t')
                saturation[name] = float(value.replace(',', '.'))
    portfolio = load(os.path.join(POSTS, 'album', '3.json'))
    entries, images = [], []

    def add_images(media_list, eid):
        out = []
        for n, m in enumerate(media_list):
            src = m['uri'].split('posts/media/', 1)[1]
            name = f'{eid}-{n + 1}.jpg'
            images.append((os.path.join(POSTS, 'media', *src.split('/')), name))
            out.append(name)
        return out

    seen = {}
    for i, p in enumerate(posts):
        media = [d['media'] for a in p.get('attachments', []) for d in a.get('data', []) if 'media' in d]
        if not media or i in SKIP or i in PATRIMONIU or i == len(posts) - 1 and len(media) > 10:
            continue
        if not any(s in media[0]['uri'] for s in ('Photos_', 'your_posts', 'Mobileuploads')):
            continue
        text = '\n'.join(d['post'] for d in p['data'] if 'post' in d) or (media[0].get('description') or '')
        text = text.strip()
        key = norm(text)
        # Same caption re-posted within a few weeks: keep the most recent one.
        if key and key in seen and abs(seen[key] - p['timestamp']) < 30 * 86400:
            continue
        if key:
            seen[key] = p['timestamp']
        subject, theme = subject_of(TITLES.get(i) or text)
        title = TITLES.get(i) or subject or extract_title(text) or 'Icoană pe sticlă'
        head = text[:400].lower()
        if re.search(r'în lucru|in lucru|desen(ul)? (în|cu) tu|desen cu peni|desen pe sticl|urzeal|„lucru"|"lucru"|prima etap|prima faz', head):
            kind = 'lucru'
        else:
            kind = 'icoana'
        eid = f'p{i}'
        e = {
            'id': eid,
            'date': datetime.datetime.fromtimestamp(p['timestamp']).strftime('%Y-%m-%d'),
            'title': title,
            'kind': kind,
            'theme': theme,
            'text': '' if i in HIDE_TEXT else reword(clean_customers(text)),
            'images': add_images(media, eid),
        }
        # Posts whose caption is hidden here are not linked either.
        if i not in HIDE_TEXT:
            e['facebook'] = facebook_link(media[0])
        e.update(details(text))
        if (kind == 'icoana' and i not in FINISHED_BW and e['images']
                and all(saturation.get(n, 1) < 0.1 for n in e['images'])):
            e['kind'] = 'lucru'
        entries.append(e)

    # The original portfolio (30 Dec 2021): one photo per icon, each with its own title.
    for n, ph in enumerate(portfolio['photos']):
        caption = (ph.get('description') or '').strip()
        subject, theme = subject_of(caption)
        eid = f'a{n}'
        entries.append({
            'id': eid,
            'date': datetime.datetime.fromtimestamp(ph['creation_timestamp']).strftime('%Y-%m-%d'),
            'title': subject or caption.strip('„“"') or 'Icoană pe sticlă',
            'kind': 'icoana',
            'theme': theme,
            'text': '',
            'portfolio': True,
            'facebook': facebook_link(ph),
            'images': add_images([ph], eid),
        })

    # Posts newer than the Facebook export, added by hand to site/new-posts/posts.json
    # (photos in the same folder). Each has its own id: n1, n2, ...
    new_file = os.path.join(NEW_POSTS, 'posts.json')
    if os.path.exists(new_file):
        with open(new_file, encoding='utf-8') as f:
            new_posts = json.load(f)
        for p in new_posts:
            eid, text = p['id'], p['text'].strip()
            subject, theme = subject_of(p.get('title') or text)
            e = {
                'id': eid,
                'date': p['date'],
                'title': p.get('title') or subject or extract_title(text) or 'Icoană pe sticlă',
                'kind': 'icoana',
                'theme': theme,
                'text': reword(clean_customers(text)),
                'images': [],
            }
            for n, photo in enumerate(p['photos']):
                name = f'{eid}-{n + 1}.jpg'
                images.append((os.path.join(NEW_POSTS, photo), name))
                e['images'].append(name)
            if p.get('facebook'):
                e['facebook'] = p['facebook']
            e.update(details(text))
            # Facts set by hand win over the ones read from the caption.
            for key in ('izvod', 'dimensiuni', 'sarbatoare', 'disponibilitate'):
                if p.get(key):
                    e[key] = p[key]
            entries.append(e)

    entries.sort(key=lambda e: (e['date'], e['id']), reverse=True)

    # Work-in-progress posts are not shown on their own: each ink drawing is attached
    # to the finished icon with the same subject posted soonest after it (within ~5 months).
    def day(e):
        return datetime.date.fromisoformat(e['date'])
    finished = [e for e in entries if e['kind'] == 'icoana']
    for draft in sorted((e for e in entries if e['kind'] == 'lucru'), key=day):
        later = [f for f in finished if f['title'] == draft['title'] and 0 <= (day(f) - day(draft)).days <= 150]
        if later:
            target = min(later, key=day)
            target.setdefault('stages', []).append(
                {'date': draft['date'], 'text': draft['text'], 'images': draft['images']})
    entries = [e for e in entries if e['kind'] != 'lucru']
    entries = merge_reposts(entries)
    for e in entries:
        del e['kind']

    # The 2019-2020 archive: icons not on Facebook become entries v1, v2, ...; icons that
    # are (photographed earlier) get one more photo. Matched by eye, not by photo hash.
    church_photos = []
    if os.path.exists(OLD_WORKS):
        with open(OLD_WORKS, encoding='utf-8') as f:
            old = json.load(f)
        by_post = {}
        for e in entries:
            for pid in [e['id']] + e.get('aliases', []):
                by_post[pid] = e
        for w in old['works']:
            e = {'id': w['id'], 'date': w['date'], 'title': w['title'], 'theme': w['theme'],
                 'text': w['text'], 'images': [w['id'] + '-1.jpg'], 'archive': True}
            if w.get('date_approx'):
                e['date_approx'] = True
            for key in ('izvod', 'dimensiuni', 'sarbatoare', 'disponibilitate'):
                if w.get(key):
                    e[key] = w[key]
            images.append((os.path.join(OLD_PHOTOS, w['id'] + '.jpg'), e['images'][0]))
            entries.append(e)
        for a in old['add_photos']:
            e = by_post[a['to']]
            name = f"{a['to']}-arhiva.jpg"
            images.append((os.path.join(OLD_PHOTOS, f"add-{a['to']}.jpg"), name))
            e['images'] = [name] + e['images'] if a.get('first') else e['images'] + [name]
        for c in old['church_photos']:
            images.append((os.path.join(OLD_PHOTOS, c['name']), c['name']))
            church_photos.append(c['name'])
        entries.sort(key=lambda e: (e['date'], e['id']), reverse=True)
    for e in entries:
        for pid in [e['id']] + e.get('aliases', []):
            if pid in DESTINATION:
                e['destinatie'] = DESTINATION[pid]
        if CHURCH & set([e['id']] + e.get('aliases', [])):
            e['biserica'] = True
            # Where the church is, when a caption says ("... Biserică din Dobrogea").
            # Merged posts naming different places (p842: Măcin, Arad...) show no place.
            texts = [e['text']] + [h['text'] for h in e.get('history', [])]
            places = {re.sub(r'^jud\.?\s+', 'jud. ', m.group(1)) for t in texts for m in CHURCH_PLACE.finditer(t)}
            if len(places) == 1:
                e['biserica_loc'] = places.pop()

    profile = load(os.path.join(EXPORT, 'profile_information', 'profile_information', 'profile_information.json'))['profile_v2']
    site = {
        'name': 'Atelierul Bizantin de Icoane pe Sticlă',
        # The Facebook bio says "(cu peste 300 lucrari în portofoliu)"; the real count is ~250.
        'tagline': 'Pictor iconar inspirat de icoanele celebrilor pictori ardeleni',
        # Her Facebook "about" text, with the figures brought up to date (approved by the user):
        # it was written ~2022 ("acum aproape 3 ani", "aproape 80 icoane"). With the 2019-2020
        # archive the site shows ~290 different icons; her bio says "peste 300 lucrari".
        'about': profile['about_me'].replace(' \nBunei', ' Bunei')
                 .replace('acum aproape 3 ani, în ziua', 'în 2019, în ziua')
                 .replace('aproape 80 icoane', 'aproximativ 300 de icoane'),
        'facebook': profile['profile_uri'],
        'since': datetime.datetime.fromtimestamp(profile['registration_timestamp']).strftime('%Y-%m-%d'),
        'themes': [{'key': k, 'label': l} for k, l in THEMES],
        'church_photos': church_photos,
    }
    # Photos still used on the site (unmatched drawings and merged duplicates are not).
    used = {n for e in entries for n in e['images'] + [m for s in e.get('stages', []) for m in s['images']]}
    used.update(church_photos)

    os.makedirs(os.path.join(SITE, 'data'), exist_ok=True)
    with open(os.path.join(SITE, 'data', 'lucrari.json'), 'w', encoding='utf-8') as f:
        json.dump({'site': site, 'lucrari': entries}, f, ensure_ascii=False, indent=1)
    # All candidate photos are listed, so measure_colour.ps1 and hash_images.ps1 see them
    # all; the third column marks the ones make_images.ps1 puts on the site.
    with open(os.path.join(HERE, 'images.txt'), 'w', encoding='utf-8-sig') as f:
        for src, name in images:
            f.write(src + '\t' + name + '\t' + str(int(name in used)) + '\n')

    print(len(entries), 'entries,', len(used), 'of', len(images), 'photos used')
    for k, (old, _) in enumerate(REWORD):
        if k not in REWORD_USED:
            print('REWORD phrase not found:', old[:70])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
