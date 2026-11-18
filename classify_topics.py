import os, json, base64, requests, re

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

r = requests.get(f'https://api.github.com/repos/{REPO}/contents/ocr_status.json',
                 headers=HEADERS, timeout=60).json()
d = json.loads(base64.b64decode(r['content']).decode())

PRODUCT = ['краб', 'крабовое', 'устриц', 'гребеш', 'морош', 'ёж', 'еж ', 'рыб', 'морск', 'продукт',
           'свеж', 'вылов', 'доставк', 'заказ', 'цен', '₽', 'кг', 'суп', 'деликатес', 'мурманск', 'лосос',
           'семга', 'треска', 'омут', 'камбала', 'парусник']
EXCURSION = ['прогул', 'териберк', 'катер', 'пароход', 'виктори', 'лодк', 'кораб', 'кит', 'дельфин',
             'морск', 'реис', 'борт', 'посещ', 'экскурс', 'круиз', 'улов', 'рыбалк', 'сафари', 'час']
AQUARIUM = ['аквариум', 'узв', 'витрин', 'насос', 'фильтр', 'соленост', 'солён', 'освещен', 'освещен',
            'циркуляц', 'коралл', 'мраморн', 'аквасистем', 'проект', 'спецификац', 'подрядчик']

def score(text, kws):
    t = text.lower()
    return sum(1 for k in kws if k in t)

out = {}
for pid, txt in d.get('ocr', {}).items():
    p = score(txt, PRODUCT)
    e = score(txt, EXCURSION)
    a = score(txt, AQUARIUM)
    best = max([('products', p), ('excursions', e), ('aquarium', a)], key=lambda x: x[1])
    hits = sorted(set(k.strip() for k in (PRODUCT + EXCURSION + AQUARIUM) if k.strip() in txt.lower()))
    out[pid] = {'topic': best[0] if best[1] > 0 else 'unknown',
                 'scores': {'products': p, 'excursions': e, 'aquarium': a},
                 'hits': hits[:14],
                 'chars': len(txt),
                 'snippet': ' '.join(txt.split())[:260]}
    print(pid, out[pid]['topic'], out[pid]['scores'], flush=True)

with open('reels_topics.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
body = base64.b64encode(open('reels_topics.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/reels_topics.json', headers=HEADERS,
             json={'message': 'chore: reel topics from ocr', 'content': body, 'branch': 'main'}, timeout=60)
print('DONE', len(out))
