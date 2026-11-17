import os, json, base64, requests

T = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{T}'
out = {'tests': {}}

def call(method, **kw):
    try:
        return requests.post(f'{API}/{method}', data=kw, timeout=60).json()
    except Exception as e:
        return {'ok': False, 'description': repr(e)}

# 1) список админов канала (видны только боты/админы, если бот участник)
for c in ['@vkusmorey51', '@morskieakvarium', '@murmansk_moreprodukt']:
    r = call('getChatAdministrators', chat_id=c)
    admins = []
    for a in (r.get('result') or []):
        u = a.get('user') or {}
        admins.append({'id': u.get('id'), 'username': u.get('username'),
                       'status': a.get('status'), 'can_post_messages': a.get('can_post_messages')})
    out['tests'][c] = {'admins_ok': r.get('ok'), 'error': r.get('description'), 'admins': admins}

# 2) бот может писать тебе в личку? (тест без публикации в каналы)
r = call('sendMessage', chat_id='1486595631', text='ping')
out['tests']['admin_dm'] = {'ok': r.get('ok'), 'error': r.get('description')}
if r.get('ok'):
    mid = r['result']['message_id']
    call('deleteMessage', chat_id='1486595631', message_id=mid)
    out['tests']['admin_dm']['message_id'] = mid

# 3) пробная отправка в канал прогулок — ТЕСТОВЫЙ ФАЙЛ, удаляется сразу
TEST_URL = 'https://raw.githubusercontent.com/litvinenko0100-a11y/vkusmorey-bots/main/prices.json'
r = call('sendDocument', chat_id='@vkusmorey51', document=TEST_URL)
out['tests']['send_probe_vkusmorey51'] = {'ok': r.get('ok'), 'error': r.get('description')}
if r.get('ok'):
    mid = r['result']['message_id']
    call('deleteMessage', chat_id='@vkusmorey51', message_id=mid)
    out['tests']['send_probe_vkusmorey51']['deleted'] = True

# 4) то же для аквариумов (не публикуем контент — только проверка прав)
r = call('sendDocument', chat_id='@morskieakvarium', document=TEST_URL)
out['tests']['send_probe_morskieakvarium'] = {'ok': r.get('ok'), 'error': r.get('description')}
if r.get('ok'):
    mid = r['result']['message_id']
    call('deleteMessage', chat_id='@morskieakvarium', message_id=mid)
    out['tests']['send_probe_morskieakvarium']['deleted'] = True

with open('probe_access.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

gh = os.environ.get('GITHUB_TOKEN', '')
if gh:
    body = base64.b64encode(open('probe_access.json', 'rb').read()).decode()
    requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/probe_access.json',
                 headers={'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'},
                 json={'message': 'chore: probe access rights', 'content': body, 'branch': 'main'}, timeout=60)
print('done')
