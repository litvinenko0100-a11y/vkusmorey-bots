import os, json, base64, requests

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

CANDS = {
    'CONTENT_TOKEN': os.environ.get('CONTENT_TOKEN', ''),
    'EXCURSIONS_TOKEN': os.environ.get('EXCURSIONS_TOKEN', ''),
    'PRODUCTS_TOKEN': os.environ.get('PRODUCTS_TOKEN', ''),
}

out = {}
for name, tok in CANDS.items():
    entry = {'token_present': bool(tok)}
    if not tok:
        out[name] = entry
        continue
    api = f'https://api.telegram.org/bot{tok}'
    try:
        me = requests.get(f'{api}/getMe', timeout=30).json()
        entry['getMe'] = {'ok': me.get('ok'), 'username': (me.get('result') or {}).get('username'),
                          'id': (me.get('result') or {}).get('id'), 'error': me.get('description')}
    except Exception as e:
        entry['getMe'] = {'ok': False, 'error': repr(e)}
    # права на каналы
    entry['channels'] = {}
    for ch in ['@morskieakvarium', '@vkusmorey51', '@murmansk_moreprodukt']:
        try:
            r = requests.post(f'{api}/getChatMember',
                              data={'chat_id': ch, 'user_id': (me.get('result') or {}).get('id')},
                              timeout=30).json()
            st = r.get('result') or {}
            entry['channels'][ch] = {'ok': r.get('ok'), 'status': st.get('status'),
                                     'can_post_messages': st.get('can_post_messages'),
                                     'error': r.get('description')}
        except Exception as e:
            entry['channels'][ch] = {'ok': False, 'error': repr(e)}
    # заявки в боте: getUpdates (offset=-1 — только свежие, без конфликта с getUpdates-поллером)
    try:
        r = requests.post(f'{api}/getUpdates', data={'offset': -1, 'limit': 100, 'timeout': 0}, timeout=30).json()
        upd = r.get('result') or []
        msgs = []
        for u in upd:
            m = u.get('message') or {}
            msgs.append({'chat_id': (m.get('chat') or {}).get('id'),
                         'chat_title': (m.get('chat') or {}).get('title'),
                         'username': (m.get('from') or {}).get('username'),
                         'text': (m.get('text') or '')[:400],
                         'date': u.get('message_id')})
        entry['getUpdates'] = {'ok': r.get('ok'), 'error': r.get('description'), 'count': len(upd), 'messages': msgs}
    except Exception as e:
        entry['getUpdates'] = {'ok': False, 'error': repr(e)}
    out[name] = entry

with open('bot_probe.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
body = base64.b64encode(open('bot_probe.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/bot_probe.json', headers=HEADERS,
             json={'message': 'chore: bot token probe', 'content': body, 'branch': 'main'}, timeout=60)
print(json.dumps(out, ensure_ascii=False)[:3000])
