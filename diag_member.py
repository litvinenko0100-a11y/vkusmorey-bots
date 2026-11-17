import os, json, base64, requests

T = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{T}'
me = requests.get(f'{API}/getMe', timeout=30).json()['result']
BOT = me['id']
ADMIN = 1486595631
out = {'bot': me['username'], 'bot_id': BOT, 'checks': {}}

# может ли бот написать админу в личку (пользователь должен был /start боту)
for cid, label in [(ADMIN, 'admin_private'), ('@vkusmorey51', 'excursions_channel')]:
    rc = requests.get(f'{API}/getChat', params={'chat_id': cid}, timeout=30).json()
    res = rc.get('result') or {}
    out['checks'][label] = {'ok': rc.get('ok'), 'type': res.get('type'),
                            'title': res.get('title') or res.get('first_name'),
                            'chat_id': res.get('id'), 'error': rc.get('description')}

# реальная попытка отправки в личку админа (пустое тело нельзя — шлём тестовое сообщение)
r = requests.post(f'{API}/sendMessage',
                   data={'chat_id': ADMIN, 'text': 'test'}, timeout=30).json()
out['admin_send_test'] = {'ok': r.get('ok'), 'error': r.get('description'),
                          'message_id': (r.get('result') or {}).get('message_id')}
if r.get('ok'):
    requests.post(f'{API}/deleteMessage',
                  data={'chat_id': ADMIN, 'message_id': r['result']['message_id']}, timeout=30)

# проба отправки видео в канал прогулок (покажем точную ошибку)
out['send_probe_note'] = 'проверка идёт отдельным шагом'

with open('diag_member.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

gh = os.environ.get('GITHUB_TOKEN', '')
if gh:
    body = base64.b64encode(open('diag_member.json', 'rb').read()).decode()
    requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/diag_member.json',
                 headers={'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'},
                 json={'message': 'chore: admin dm + channel access probe', 'content': body, 'branch': 'main'}, timeout=60)
print('done')
