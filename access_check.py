import os, json, requests

TOK = os.environ.get('PRODUCTS_TOKEN', '')
EXC = os.environ.get('EXCURSIONS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
BOT_ID = 9194586932
CHATS = ['@murmansk_moreprodukt', '@vkusmorey51', '@morskieakvarium']

out = {'token_present': bool(TOK), 'exc_token_present': bool(EXC), 'chats': {}}
for c in CHATS:
    rec = {}
    r = requests.get(f'{API}/getChatMember', params={'chat_id': c, 'user_id': BOT_ID}, timeout=30).json()
    rec['me'] = r
    r2 = requests.get(f'{API}/getChat', params={'chat_id': c}, timeout=30).json()
    rec['chat'] = r2
    out['chats'][c] = rec
    print(c, r.get('ok'), (r.get('result') or {}).get('status'),
          (r.get('result') or {}).get('can_post_messages'), r.get('description'), flush=True)

# заявки: getUpdates по обоим ботам
for name, t in [('products', TOK), ('excursions', EXC)]:
    if not t:
        out[name + '_updates'] = {'error': 'no token'}
        continue
    rr = requests.get(f'https://api.telegram.org/bot{t}/getUpdates', params={'timeout': 0, 'limit': 100}, timeout=30).json()
    msgs = rr.get('result') or []
    out[name + '_updates'] = {'ok': rr.get('ok'), 'count': len(msgs),
                              'error': rr.get('description'),
                              'messages': [{'chat': (m.get('message') or {}).get('chat', {}).get('id'),
                                            'text': ((m.get('message') or {}).get('text') or '')[:500]}
                                           for m in msgs if 'message' in m]}
    print(name, 'updates', rr.get('ok'), len(msgs), rr.get('description'), flush=True)

with open('access_result.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

body = open('access_result.json', 'rb').read()
import base64
h = {'Authorization': f"Bearer {os.environ.get('GITHUB_TOKEN','')}", 'Accept': 'application/vnd.github+json'}
resp = requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/access_result.json',
                    headers=h, json={'message': 'chore: access check', 'content': base64.b64encode(body).decode(), 'branch': 'main'}, timeout=60)
print('saved', resp.status_code)
