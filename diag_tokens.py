import os, json, base64, requests

CHATS = ['@murmansk_moreprodukt', '@vkusmorey51', '-1003715433172', '@morskieakvarium']
names = ['CONTENT_TOKEN', 'EXCURSIONS_TOKEN', 'PRODUCTS_TOKEN']
out = []

for n in names:
    t = os.environ.get(n, '')
    if not t:
        out.append({'token': n, 'present': False})
        continue
    r = requests.get(f'https://api.telegram.org/bot{t}/getMe', timeout=30).json()
    entry = {'token': n, 'present': True, 'getMe_ok': r.get('ok'),
             'username': (r.get('result') or {}).get('username'),
             'error': r.get('description'), 'chats': {}}
    for c in CHATS:
        rc = requests.get(f'https://api.telegram.org/bot{t}/getChat', params={'chat_id': c}, timeout=30).json()
        res = rc.get('result') or {}
        entry['chats'][c] = {'ok': rc.get('ok'), 'title': res.get('title'),
                             'type': res.get('type'), 'error': rc.get('description')}
    out.append(entry)

with open('diag_result.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

gh = os.environ.get('GITHUB_TOKEN', '')
if gh:
    body = base64.b64encode(open('diag_result.json','rb').read()).decode()
    requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/diag_result.json',
                 headers={'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'},
                 json={'message': 'chore: diag result', 'content': body, 'branch': 'main'}, timeout=60)
print('done')