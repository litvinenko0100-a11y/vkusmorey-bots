import os, json, base64, subprocess, requests

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
BRANCH = 'main'
GH = os.environ.get('GITHUB_TOKEN', '')
TOK = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
ADMIN = 1486595631
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


def gh_get(path):
    r = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}',
                     headers={'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}, timeout=60)
    return json.loads(base64.b64decode(r.json()['content']).decode())


def gh_put(path, data, msg):
    body = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=1).encode('utf-8')).decode()
    h = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}
    payload = {'message': msg, 'content': body, 'branch': BRANCH}
    r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=h, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=h, timeout=30).json()
        payload['sha'] = cur.get('sha')
        r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=h, json=payload, timeout=60)
    log('gh_put', path, r.status_code)
    return r.status_code in (200, 201)


# ---- 1. Прайс: заполняем ТОЛЬКО подтверждённое (краб 1 фал — 8 900 ₽ из описания канала)
prices = gh_get('prices.json')
prices['crab'] = 890000          # XTR, копейки
prices['crab_label'] = 'Краб камчатский, 1 фал'
log('prices before:', json.dumps({k: prices.get(k) for k in ['fish', 'squid', 'crab', 'salmon']}, ensure_ascii=False))
gh_put('prices.json', prices, 'prices: set crab from channel description')
log('prices after:', json.dumps({k: prices.get(k) for k in ['fish', 'squid', 'crab', 'salmon']}, ensure_ascii=False))

# ---- 2. Доставляем 8 неопубликованных рилсов в личный чат админа
queue = gh_get('reels.json')
state = gh_get('reels_state.json')
pub = set(state.get('published') or [])
pending = [x for x in queue if x['permalink'] not in pub]
log('pending', len(pending))

sent = []
for item in pending:
    url = item['permalink']
    rc = subprocess.run(['yt-dlp', '-f', 'mp4', '-o', 'reel.mp4', '--quiet', url],
                        capture_output=True, text=True, timeout=180)
    if rc.returncode != 0 or not os.path.exists('reel.mp4'):
        log('yt-dlp fail', url, rc.stderr[-120:])
        continue
    size = os.path.getsize('reel.mp4')
    with open('reel.mp4', 'rb') as f:
        r = requests.post(f'{API}/sendVideo', data={'chat_id': ADMIN, 'caption': url,
                                                    'supports_streaming': 'true'},
                          files={'video': ('reel.mp4', f, 'video/mp4')}, timeout=300).json()
    ok = r.get('ok')
    log('sendVideo', url, ok, (r.get('result') or {}).get('message_id'), str(r.get('description'))[:100])
    if ok:
        sent.append(url)
    os.remove('reel.mp4')

result = {'sent': sent, 'pending_total': len(pending), 'log': LOG[-60:]}
with open('delivery_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
body = open('delivery_result.json', 'rb').read()
h = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}
requests.put(f'https://api.github.com/repos/{REPO}/contents/delivery_result.json', headers=h,
             json={'message': 'chore: reel delivery + prices', 'content': base64.b64encode(body).decode(), 'branch': BRANCH}, timeout=60)
print('DONE', len(sent), flush=True)
