import os, json, base64, requests

TOK = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
CHATS = {'@murmansk_moreprodukt': 'Морепродукты Мурманска',
         '@vkusmorey51': 'Вкус Морей',
         '@morskieakvarium': 'Морские аквариумы'}
out = {'me': None, 'chats': {}}
r = requests.get(f'{API}/getMe', timeout=30).json()
out['me'] = r.get('result')
for c in CHATS:
    rc = requests.get(f'{API}/getChat', params={'chat_id': c}, timeout=30).json()
    res = rc.get('result') or {}
    entry = {'ok': rc.get('ok'), 'title': res.get('title'), 'type': res.get('type')}
    ra = requests.get(f'{API}/getChatAdministrators', params={'chat_id': c}, timeout=30).json()
    admins = []
    for a in (ra.get('result') or []):
        u = a.get('user') or {}
        admins.append({'username': u.get('username'), 'id': u.get('id'),
                       'status': a.get('status'),
                       'can_post_messages': a.get('can_post_messages'),
                       'can_post_stories': a.get('can_post_stories'),
                       'can_edit_messages': a.get('can_edit_messages')})
    entry['admins_error'] = ra.get('description')
    entry['admins'] = admins
    out['chats'][c] = entry

gh = os.environ.get('GITHUB_TOKEN', '')
body = base64.b64encode(json.dumps(out, ensure_ascii=False, indent=1).encode('utf-8')).decode()
headers = {'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'}
requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/diag_admins.json',
             headers=headers, json={'message': 'chore: admins diag', 'content': body, 'branch': 'main'}, timeout=60)
print('done')