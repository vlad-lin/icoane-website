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
              1148, 1150, 1185, 1011}
# Posts that are not artwork, or are uncaptioned re-uploads of another post.
# 1136 announces a contest winner (a private person).
SKIP = {813, 684, 685, 690, 691, 692, 697, 698, 1011, 674, 1136}
# Icons shown without their caption: 932 is about parcels broken on the way to customers,
# 1012 and 1014 announce a contest (the icon was its prize).
HIDE_TEXT = {932, 1012, 1014}
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

MONTHS = ('ianuarie februarie martie aprilie mai iunie iulie august septembrie '
          'octombrie noiembrie decembrie').split()

THEMES = [
    ('maica', 'Maica Domnului'),
    ('praznice', 'Iisus Hristos și praznice'),
    ('sfinti', 'Sfinți și arhangheli'),
    ('masa', 'Masa Raiului'),
    ('eroi', 'Martiri și eroi'),
    ('altele', 'Alte lucrări'),
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
    (r'micul print', 'Micul Prinț', 'altele'),
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
    elif re.search(r'comand', low):
        d['disponibilitate'] = 'Realizată la comandă'
    return d


def norm(s):
    return re.sub(r'\W+', ' ', s.lower()).strip()[:160]


# --- Customer references -----------------------------------------------------
# The site names no customers: no first names, towns, families or dedications.
# Captions are cleaned sentence by sentence: CUT removes the customer part of a
# sentence, DROP removes sentences that are only about a customer.
TOWNS = (r'(?:Brăila|Bacău|Constanța|Mangalia|Bra[sșş]ov|Bucure[sșş]ti|Timi[sșş]oara|Oradea|Arad|Sibiu|'
         r'Cluj|Râmnicu Vâlcea|Alba Iulia|Maramure[sșş]|Dobrogea|Măcin|continentul american)')
PERSON = (r'(?:famili\w*|cuplu|tată|soț|preot|băiețel|copil|om|frățiori|doamn\w*|prieten\w*)')
CUT = [
    (r'\s*\(\s*la cererea clientului\s*\)', ''),
    (r'\(\s*La cererea clientului\s+', '('),
    (r'^La cererea clientului\s*,\s*', ''),
    (r',?\s*la cererea clientului(?: care a dorit o icoană personalizată)?', ''),
    (r'clientul\s+dorește icoana', 'icoana este'),
    (r'Dorin[țţ]a clientului a fost ca în această icoană să-l reprezentăm', 'În această icoană l-am reprezentat'),
    (r'\s*\(\s*prin bunăvoința[^)]*\)', ''),
    (r'\s*pentru prietena noastră\s*@\w+', ''),
    (r',\s*un prieten al atelierului[^.!?\n]*', ''),
    (r'\s*datorită unei[^.!?\n]*famili[^.!?\n]*', ''),
    # "se află în colecția unei familii..., deci nu este disponibilă"
    (r'se află în colecția unei[^,.!?\n]*,\s*deci nu este disponibilă', 'nu este disponibilă'),
    (r'\s*(?:aflat[ăa]\s+)?în colecția unei[^.!?\n]*', ''),
    # "nu este disponibilă, a plecat spre Constanța..."
    (r'(disponibil[ăa])\s*,\s*(?:a plecat|va pleca)[^.!?\n]*', r'\1'),
    # "pentru o Sfântă Biserică din Dobrogea" -> keep the church, drop the town
    (r'((?:pentru|unei|o)\s+(?:\w+\s+){0,3}(?:[Bb]iseric|[Mm]ănăstir)\w*(?:\s+[Oo]rtodox\w*)?(?:\s+\([^)]*\))?)'
     r'\s*,?\s*din\s+(?:jud\.?\s+|vestul\s+)?[A-ZĂÂÎȘȚ]\w+', r'\1'),
    # "comandată la Brăila", "comandată în Bacău" -> "comandată"
    (r'(comandat[ăa]|pictat[ăa]|lucrat[ăa])\s+(?:în|la|din)\s+' + TOWNS, r'\1'),
    # "...pentru a fi dăruită (cu bucurie) unui om minunat, ..." -> "..."
    (r',?\s*pentru a fi (?:dăruit|oferit)\w*\s+(?:[^.!?\n)]{0,25}?\s)?(?:lui|unui|unei|prietenului|tinerei)\b[^.!?\n)]*', ''),
    # "(a fost comandată/pictată) pentru o frumoasă familie din Arad" -> "(...)"
    (r',?\s*(?:pentru|de)\s+(?:o|un|doi)\s+(?:[\w-]+\s+){0,3}?' + PERSON +
     r'(?:\s+(?:de\s+(?:tineri\s+)?români|(?!din\b|care\b|ce\b)[a-zăâîșț]+))?(?:\s*,?\s*numit\s+\w+)?'
     r'(?:\s*,?\s*din\s+(?:[A-ZĂÂÎȘȚ]\w+(?:-\w+)*\s*)+)?(?:\s*,?\s+(?:care|ce)\b[^.!?\n)]*)?', ''),
]
CUT = [(re.compile(rx), rep) for rx, rep in CUT]
DROP = re.compile(
    r'(?i:client|câștigător|concurs)|@\w|casa unei|^\W*(?:Și\s+)?[Dd]e aceas?t[aă] dată,?\s+(?:din|la|în|pentru)\b|[Ff]amili(?:a|ei|i)\s+(?:a hotărât|din)|minunatei famili|'
    r'[Aa]semenea a procedat|soți(?:a|ei)|\bsoț\b|frățiori|om (?:minunat|deosebit)|'
    r'doamn\w*\s+(?:deosebit|special|căreia|\(religie)|religie (?:ortodox|catolic)|[Pp]oșt\w* român|'
    r'[A-ZĂÂÎȘȚ][a-zăâîșț]+, unul dintre prietenii|'
    r'(?i:la mulți ani)\W*,\s*(?!tuturor|celor|prietenilor|sărbători)[A-ZĂÂÎȘȚ][a-zăâîșț]+\b[^!\n]{0,80}!|'
    r'(?:plecat|pleca|merge|ajuns|ajunge|așteptat|comandat|dăruit|casa|căsuț|cadou)[^.!?\n]*\b(?:la|în|din|spre|de)\s+' + TOWNS)
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
            for rx, rep in CUT:
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
            if new and DROP.search(new) and not HISTORY.search(new):
                new = ''
            if new:
                kept.append(new + sep)
        cleaned = ''.join(kept).rstrip()
        if cleaned != line.rstrip() and not clean_line(cleaned):
            continue  # line had only customer sentences: remove it entirely
        out.append(cleaned)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip()


# --- Reposts of the same icon -------------------------------------------------
# The same icon was often re-posted in later years, on its feast day. Entries whose
# main photos are near-identical (hash_images.ps1) become one entry; the other
# captions are kept as its history. Up to 17 of 256 bits differ for re-edited or
# re-cropped photos of one icon; two paintings of the same izvod differ more.
SAME_ICON = 17
GENERIC_TITLES = {'Maica Domnului', 'Iisus Hristos Mântuitorul', 'Icoană pe sticlă'}


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
        main = max(members, key=lambda e: len(e['text']))
        named = [m for m in members if int(m['id'][1:]) in TITLES and m['id'][0] == 'p']
        specific = [m for m in members if m['title'] not in GENERIC_TITLES]
        if named:
            best = named[0]
        elif specific:
            best = max(specific, key=lambda m: [s['title'] for s in specific].count(m['title']))
        else:
            best = main
        e = dict(main, title=best['title'], theme=best['theme'], date=members[0]['date'])
        if e['date'] != main['date']:
            e['text_date'] = main['date']
        if any(m.get('portfolio') for m in members) and members[0].get('portfolio'):
            e['portfolio'] = True
        else:
            e.pop('portfolio', None)
        images = list(main['images'])
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
        e['aliases'] = [m['id'] for m in members if m is not main]
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
            images.append((src, name))
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
            'text': '' if i in HIDE_TEXT else clean_customers(text),
            'images': add_images(media, eid),
        }
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
            'images': add_images([ph], eid),
        })

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

    profile = load(os.path.join(EXPORT, 'profile_information', 'profile_information', 'profile_information.json'))['profile_v2']
    site = {
        'name': 'Atelierul Bizantin de Icoane pe Sticlă',
        # The Facebook bio says "(cu peste 300 lucrari în portofoliu)"; the real count is ~250.
        'tagline': 'Pictor iconar inspirat de icoanele celebrilor pictori ardeleni',
        # Her Facebook "about" text, with the figures brought up to date (approved by the user):
        # it was written ~2022 ("acum aproape 3 ani", "aproape 80 icoane").
        'about': profile['about_me'].replace(' \nBunei', ' Bunei')
                 .replace('acum aproape 3 ani, în ziua', 'în 2019, în ziua')
                 .replace('aproape 80 icoane', 'aproximativ 250 de icoane'),
        'facebook': profile['profile_uri'],
        'since': datetime.datetime.fromtimestamp(profile['registration_timestamp']).strftime('%Y-%m-%d'),
        'themes': [{'key': k, 'label': l} for k, l in THEMES],
    }
    # Photos still used on the site (unmatched drawings and merged duplicates are not).
    used = {n for e in entries for n in e['images'] + [m for s in e.get('stages', []) for m in s['images']]}

    os.makedirs(os.path.join(SITE, 'data'), exist_ok=True)
    with open(os.path.join(SITE, 'data', 'lucrari.json'), 'w', encoding='utf-8') as f:
        json.dump({'site': site, 'lucrari': entries}, f, ensure_ascii=False, indent=1)
    # All candidate photos are listed, so measure_colour.ps1 and hash_images.ps1 see them
    # all; the third column marks the ones make_images.ps1 puts on the site.
    with open(os.path.join(HERE, 'images.txt'), 'w', encoding='utf-8-sig') as f:
        for src, name in images:
            f.write(os.path.join(POSTS, 'media', *src.split('/')) + '\t' + name + '\t' + str(int(name in used)) + '\n')

    print(len(entries), 'entries,', len(used), 'of', len(images), 'photos used')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
