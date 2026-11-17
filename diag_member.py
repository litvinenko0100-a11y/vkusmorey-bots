import os, json, base64, requests

T = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{T}'
me = requests.get(f'{API}/getMe', timeout=30).json()['result']
BOT = me['id']
CHATS = ['@vkusmorey51', '@murmansk_moreprodukt', '@morskieakvarium']
out = {'bot': me['username'], 'bot_id': BOT, 'chats': {}}

for c in CHATS:
    info = requests.get(f'{API}/getChat', params={'chat_id': c}, timeout=30).json()
    res = info.get('result') or {}
    cid = res.get('id')
    entry = {'chat_id': cid, 'title': res.get('title'), 'getChat_ok': info.get('ok')}
    # статус своего членства
    mm = requests.get(f'{API}/getChatMember', params={'chat_id': c, 'user_id': BOT}, timeout=30).json()
    st = mm.get('result') or {}
    entry['member'] = {'ok': mm.get('ok'), 'status': st.get('status'),
                       'can_post_messages': st.get('can_post_messages'),
                       'can_post_stories': st.get('can_post_stories'),
                       'can_edit_messages': st.get('can_edit_messages'),
                       'error': mm.get('description')}
    out['chats'][c] = entry

with open('diag_member.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

gh = os.environ.get('GITHUB_TOKEN', '')
if gh:
    body = base64.b64encode(open('diag_member.json', 'rb').read()).decode()
    requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/diag_member.json',
                 headers={'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'},
                 json={'message': 'chore: member diag', 'content': body, 'branch': 'main'}, timeout=60)
print('done')
