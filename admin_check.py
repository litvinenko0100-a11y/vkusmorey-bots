import os, json, requests

TOK = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
ADMIN = 1486595631
BOT_ID = 9194586932

out = {}
# читаем личный чат админа: если бот уже с ним общался — сможет слать в личку
r = requests.get(f'{API}/getChat', params={'chat_id': ADMIN}, timeout=30).json()
out['admin_chat'] = r
print('admin_chat ok:', r.get('ok'), r.get('description'), flush=True)

# проверка: админ ли бот в закреплённых чатах, список участников через getChat
for c in ['@vkusmorey51', '@morskieakvarium', '@murmansk_moreprodukt']:
    rc = requests.get(f'{API}/getChat', params={'chat_id': c}, timeout=30).json()
    res = rc.get('result') or {}
    out[c] = {'ok': rc.get('ok'), 'title': res.get('title'), 'id': res.get('id'),
              'perms': res.get('permissions')}
    print(c, 'chat_ok', rc.get('ok'), '| perms', res.get('permissions'), flush=True)

# есть ли в очереди неопубликованные рилсы для @vkusmorey51
def gh_get(path):
    import base64
    u = f'https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/{path}'
    rr = requests.get(u, headers={'Authorization': f"Bearer {os.environ.get('GITHUB_TOKEN','')}",
                                  'Accept': 'application/vnd.github+json'}, timeout=60).json()
    return json.loads(base64.b64decode(rr['content']).decode())

q = gh_get('reels.json')
st = gh_get('reels_state.json')
pub = set(st.get('published') or [])
pending = [x for x in q if x['permalink'] not in pub]
out['pending'] = pending
out['published_count'] = len(pub)
print('published', len(pub), 'pending', len(pending), flush=True)
from collections import Counter
print(Counter(x['chat'] for x in pending), flush=True)

with open('admin_check.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

import base64
body = open('admin_check.json', 'rb').read()
h = {'Authorization': f"Bearer {os.environ.get('GITHUB_TOKEN','')}", 'Accept': 'application/vnd.github+json'}
resp = requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/admin_check.json',
                    headers=h, json={'message': 'chore: admin check', 'content': base64.b64encode(body).decode(), 'branch': 'main'}, timeout=60)
print('saved', resp.status_code)
