#!/usr/bin/env python3
"""Fetch state-level laws of Bosnia and Herzegovina from the Parliamentary Assembly of BiH
(https://www.parlament.ba): adopted laws (all mandates since 1996) and the Assembly's
(unofficial) consolidated texts, as PDF in the official languages (bs, hr, sr; en if any).

robots.txt of parlament.ba disallows /olaw/OLawDetails* and /oact/* - those are not used.

Usage: ba_fetch.py [RAW_DIR]
"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_raw', 'ba')
BASE = 'https://www.parlament.ba'
UA = 'LawCodex/1.0 (+https://github.com/LawCodex)'
S = requests.Session(); S.headers['User-Agent'] = UA
DELAY = 0.5
LANGS = ['bs', 'hr', 'sr', 'en']


def get(url, **kw):
    for i in range(6):
        try:
            r = S.get(url, timeout=180, **kw)
            if r.status_code >= 500 or r.status_code == 429:
                raise requests.RequestException('HTTP %d' % r.status_code)
            time.sleep(DELAY)
            return r
        except requests.RequestException as e:
            w = 5 * 2 ** i
            print('  retry', url, e, w, file=sys.stderr, flush=True); time.sleep(w)
    raise SystemExit('give up ' + url)


def ids_from(url_tpl):
    ids, page = [], 1
    while True:
        h = get(url_tpl % page).text
        new = [int(x) for x in re.findall(r'LawDetails\?lawId=(\d+)', h)]
        new = [x for x in dict.fromkeys(new) if x not in ids]
        if not new:
            return ids
        ids += new
        page += 1


def main():
    os.makedirs(RAW + '/details', exist_ok=True); os.makedirs(RAW + '/pdf', exist_ok=True)
    lf = RAW + '/lists.json'
    if os.path.exists(lf):
        lists = json.load(open(lf))
    else:
        lists = {}
        for c in (2, 3, 8):
            lists['cat%d' % c] = ids_from(BASE + '/law/Read?categoryId=%d&page=%%d' % c)
            print('cat', c, len(lists['cat%d' % c]), file=sys.stderr, flush=True)
        json.dump(lists, open(lf, 'w'))
    ids = sorted({i for v in lists.values() for i in v})
    print(len(ids), 'laws', file=sys.stderr, flush=True)

    def one(lid):
        for lang in LANGS:
            fn = RAW + '/details/%d.%s.html' % (lid, lang)
            if not os.path.exists(fn):
                h = get(BASE + '/law/LawDetails?lawId=%d&lang=%s' % (lid, lang)).text
                s = BeautifulSoup(h, 'lxml')
                el = s.find(string=lambda x: x and x.strip() in ('Podaci o zakonu', 'Подаци о закону', 'Law details', 'Podatci o zakonu', 'Law data'))
                box = el.find_parent('div').find_parent('div') if el else None
                title = s.title.get_text(' ', strip=True) if s.title else ''
                open(fn, 'w').write('<html><head><title>%s</title></head><body>%s</body></html>' % (title.replace('<', '&lt;'), str(box) if box else ''))
            h = open(fn).read()
            for doc, lt in re.findall(r'DownloadDocument\?lawDocumentId=([0-9a-f-]+)&(?:amp;)?langTag=(\w+)', h):
                pf = RAW + '/pdf/%s.%s.pdf' % (doc, lt)
                if any(os.path.exists(pf + e) for e in ('', '.docx', '.doc', '.none')):
                    continue
                r = get(BASE + '/law/DownloadDocument', params={'lawDocumentId': doc, 'langTag': lt})
                if r.status_code == 200 and r.content[:4] in (b'%PDF', b'PK\x03\x04', b'\xd0\xcf\x11\xe0'):
                    ext = {b'%PDF': '', b'PK\x03\x04': '.docx', b'\xd0\xcf\x11\xe0': '.doc'}[r.content[:4]]
                    open(pf + ext + '.tmp', 'wb').write(r.content); os.replace(pf + ext + '.tmp', pf + ext)
                else:
                    open(pf + '.none', 'w').write(str(r.status_code))
    with ThreadPoolExecutor(2) as ex:
        for n, _ in enumerate(ex.map(one, ids)):
            if n % 100 == 0:
                print('law', n, file=sys.stderr, flush=True)
    # Constitution of BiH (Annex 4 to the Dayton Agreement) from the Constitutional Court of BiH
    for lang in ('bs', 'hr', 'sr'):
        fn = RAW + '/ustav.%s.pdf' % lang
        if os.path.exists(fn):
            continue
        h = get('https://www.ustavnisud.ba/%s/ustav-bosne-i-hercegovine?force_locale=true' % lang).text
        m = re.search(r'uploads/documents/ustav[^"]*\.pdf', h)
        if m:
            open(fn, 'wb').write(get('https://www.ustavnisud.ba/' + m.group(0)).content)
            open(fn + '.url', 'w').write('https://www.ustavnisud.ba/' + m.group(0))
    print('done', file=sys.stderr)


if __name__ == '__main__':
    main()
