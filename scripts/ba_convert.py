#!/usr/bin/env python3
"""Convert BiH state laws fetched by ba_fetch.py (parlament.ba PDFs) to Markdown.

Usage: ba_convert.py RAW_DIR OUT_DIR
"""
import datetime, glob, json, os, re, sys, unicodedata
from bs4 import BeautifulSoup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ba_textmd import structure, pdftotext

RAW, OUT = sys.argv[1], sys.argv[2]
TODAY = datetime.date.today().isoformat()
CYR = dict(zip('абвгдђежзијклљмнњопрстћуфхцчџш',
               ['a', 'b', 'v', 'g', 'd', 'dj', 'e', 'z', 'z', 'i', 'j', 'k', 'l', 'lj', 'm', 'n', 'nj', 'o', 'p',
                'r', 's', 't', 'c', 'u', 'f', 'h', 'c', 'c', 'dz', 's']))
DIRS = {'bs': ('zakoni', 'preciscen-tekst'), 'hr': ('zakoni', 'prociscen-tekst'),
        'sr': ('zakoni', 'preciscen-tekst'), 'en': ('laws', 'consolidated')}


def slug(s, n=70):
    s = ''.join(CYR.get(c, c) for c in s.lower()).replace('đ', 'dj')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:n].rstrip('-')


def yq(s):
    return '"' + re.sub(r'\s+', ' ', s).strip().replace('\\', '\\\\').replace('"', '\\"') + '"'


def dmy(s):
    m = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', s or '')
    if m:
        try:
            return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            return None


def details(fn):
    s = BeautifulSoup(open(fn).read(), 'lxml')
    t = s.body.get_text(' | ', strip=True) if s.body else ''
    if not t or 'Content Not Available' in t:
        return None
    parts = t.split(' | ')
    rec = {'title': parts[0]}

    def field(*labs):
        for lab in labs:
            m = re.search(r'(?:^|\| )' + re.escape(lab) + r' \| ([^|]+)', t)
            if m:
                return m.group(1).strip()
        return ''
    rec['gazette'] = field('Broj službenog glasnika BiH', 'Број службеног гласника БиХ', 'Broj službenog glasila BiH', 'Број службеног гласила БиХ')
    rec['hor'] = dmy(field('Usvojen u Predstavničkom domu', 'Усвојен у Представничком дому', 'Usvojen u Zastupničkom domu'))
    rec['hop'] = dmy(field('Usvojen u Domu naroda', 'Усвојен у Дому народа'))
    rec['docs'] = re.findall(r'DownloadDocument\?lawDocumentId=([0-9a-f-]+)&(?:amp;)?langTag=(\w+)', str(s))
    return rec


def main():
    lists = json.load(open(os.path.join(RAW, 'lists.json')))
    cons_ids = set(lists.get('cat3', []))
    ids = sorted({i for v in lists.values() for i in v})
    counts = {}
    for lid in ids:
        bsd = details(os.path.join(RAW, 'details', '%d.bs.html' % lid)) if os.path.exists(os.path.join(RAW, 'details', '%d.bs.html' % lid)) else None
        for lang, (dz, dc) in DIRS.items():
            fn = os.path.join(RAW, 'details', '%d.%s.html' % (lid, lang))
            if not os.path.exists(fn):
                continue
            d = details(fn)
            if not d or not d['docs']:
                continue
            meta = bsd or d
            texts = []
            for doc, lt in d['docs']:
                if lt != lang:
                    continue
                pf = os.path.join(RAW, 'pdf', '%s.%s.pdf' % (doc, lt))
                if os.path.exists(pf):
                    t = pdftotext(pf)
                elif os.path.exists(pf + '.docx') or os.path.exists(pf + '.doc'):
                    import subprocess
                    src = pf + '.docx' if os.path.exists(pf + '.docx') else pf + '.doc'
                    t = subprocess.run(['textutil', '-convert', 'txt', '-stdout', src], capture_output=True).stdout.decode('utf-8', 'replace')
                else:
                    continue
                if len(t.strip()) > 100:
                    texts.append(t)
            if not texts:
                continue
            md = '\n\n'.join(structure(t) for t in texts)
            consolidated = lid in cons_ids or 'prečišćen' in d['title'].lower() or 'пречишћен' in d['title'].lower() or 'pročišćen' in d['title'].lower()
            g = meta.get('gazette', '')
            m = re.match(r'\s*(\d+)\s*/\s*(\d{2,4})', g)
            if m:
                yy = int(m.group(2)); year = yy if yy > 100 else (1900 + yy if yy > 90 else 2000 + yy)
                gnum = '%s/%02d' % (m.group(1), yy % 100)
            else:
                year = int((meta.get('hop') or meta.get('hor') or '0000')[:4]); gnum = ''
                if not year:
                    ym = re.search(r'\b((?:19|20)\d{2})\.?\s*(?:godine|године)', texts[0])
                    year = int(ym.group(1)) if ym else 0
            if consolidated:
                sub = dc
                fname = '%s.md' % slug(re.sub(r'\s*-\s*(Neslužbeni|Неслужбени|Neslužbeni)\b.*$', '', d['title']), 90)
                cm = re.search(r'\(([^()]*\d{4})\.?\)\s*$', d['title'])
            else:
                sub = '%s/%s' % (dz, year or 'bez-godine')
                fname = '%d-%s-%s.md' % (year, slug(gnum.replace('/', '-'), 10) or 'x', slug(d['title'], 80))
            path = os.path.join(OUT, lang, sub, fname)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fm = ['---', 'title: ' + yq(d['title']), 'identifier: ' + yq(('Službeni glasnik BiH ' + g) if g else 'parlament.ba law %d' % lid),
                  'type: act', 'jurisdiction: ba', 'language: ' + lang]
            date = meta.get('hop') or meta.get('hor')
            if date and not consolidated:
                fm.append('date: ' + date)
            fm += ['status: ' + ('in_force' if consolidated else 'unknown'),
                   'text_version: ' + ('unofficial_consolidated' if consolidated else 'original_as_adopted'),
                   'source: ' + yq('https://www.parlament.ba/law/LawDetails?lawId=%d&lang=%s' % (lid, lang)),
                   'retrieved: ' + TODAY, '---']
            open(path, 'w').write('\n'.join(fm) + '\n\n# ' + d['title'] + '\n\n' + md + '\n')
            k = (lang, 'consolidated' if consolidated else 'adopted')
            counts[k] = counts.get(k, 0) + 1
    titles = {'bs': 'Ustav Bosne i Hercegovine', 'hr': 'Ustav Bosne i Hercegovine', 'sr': 'Устав Босне и Херцеговине'}
    for lang, t in titles.items():
        pf = os.path.join(RAW, 'ustav.%s.pdf' % lang)
        if not os.path.exists(pf):
            continue
        url = open(pf + '.url').read().strip() if os.path.exists(pf + '.url') else 'https://www.ustavnisud.ba/%s/ustav-bosne-i-hercegovine' % lang
        md = structure(pdftotext(pf))
        path = os.path.join(OUT, lang, 'ustav', 'ustav-bosne-i-hercegovine.md')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fm = ['---', 'title: ' + yq(t), 'identifier: ' + yq('Annex 4, General Framework Agreement for Peace in BiH'),
              'type: constitution', 'jurisdiction: ba', 'language: ' + lang, 'date: 1995-12-14',
              'status: in_force', 'text_version: as_published_by_constitutional_court',
              'source: ' + yq(url), 'retrieved: ' + TODAY, '---']
        open(path, 'w').write('\n'.join(fm) + '\n\n# ' + t + '\n\n' + md + '\n')
        counts[(lang, 'constitution')] = 1
    for k, v in sorted(counts.items()):
        print(k, v, file=sys.stderr)


if __name__ == '__main__':
    main()
