import os, json, base64, requests

TOK = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
BOT_ID = 9194586932
CHATS = ['@murmansk_moreprodukt', '@vkusmorey51', '@morskieakvarium', '-1003715433172']
out = {}
for c in CHATS:
    rc = requests.get(f'{API}/getChatMember', params={'chat_id': c, 'user_id': BOT_ID}, timeout=30).json()
    res = rc.get('result') or {}
    out[c] = {'ok': rc.get('ok'), 'status': res.get('status'),
              'can_post_messages': res.get('can_post_messages'),
              'error': rc.get('description')}
gh = os.environ.get('GITHUB_TOKEN', '')
body = base64.b64encode(json.dumps(out, ensure_ascii=False, indent=1).encode('utf-8')).decode()
headers = {'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'}
requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/diag_member.json',
             headers=headers, json={'message': 'chore: membership diag', 'content': body, 'branch': 'main'}, timeout=60)
print('done')