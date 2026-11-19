import os, json, requests

TOK = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
out = {}
for c in ['@vkusmorey51', '@morskieakvarium', '@murmansk_moreprodukt']:
    rec = {}
    # безопасная проверка права писать: индикатор набора, без публикации контента
    r = requests.post(f'{API}/sendChatAction', data={'chat_id': c, 'action': 'typing'}, timeout=30).json()
    rec['sendChatAction'] = {'ok': r.get('ok'), 'desc': r.get('description')}
    r2 = requests.get(f'{API}/getChatAdministrators', params={'chat_id': c}, timeout=30).json()
    rec['admins'] = {'ok': r2.get('ok'), 'desc': r2.get('description'),
                      'names': [a.get('user', {}).get('username') for a in (r2.get('result') or [])]}
    out[c] = rec
    print(c, 'action_ok=', r.get('ok'), r.get('description'), '| admins_ok=', r2.get('ok'), r2.get('description'), rec['admins']['names'], flush=True)

with open('write_test.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

import base64
h = {'Authorization': f"Bearer {os.environ.get('GITHUB_TOKEN','')}", 'Accept': 'application/vnd.github+json'}
body = open('write_test.json', 'rb').read()
resp = requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/write_test.json',
                    headers=h, json={'message': 'chore: write permission test', 'content': base64.b64encode(body).decode(), 'branch': 'main'}, timeout=60)
print('saved', resp.status_code)
