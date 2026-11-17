import os, requests

CHATS = ['@murmansk_moreprodukt', '@vkusmorey51', '-1003715433172', '@morskieakvarium']
names = ['CONTENT_TOKEN', 'EXCURSIONS_TOKEN', 'PRODUCTS_TOKEN']

for n in names:
    t = os.environ.get(n, '')
    if not t:
        print(n, 'EMPTY')
        continue
    r = requests.get(f'https://api.telegram.org/bot{t}/getMe', timeout=30).json()
    print(n, 'getMe ok=', r.get('ok'), (r.get('result') or {}).get('username'), r.get('description', ''))
    for c in CHATS:
        rc = requests.get(f'https://api.telegram.org/bot{t}/getChat', params={'chat_id': c}, timeout=30).json()
        res = rc.get('result') or {}
        print(n, c, 'ok=', rc.get('ok'), 'title=', res.get('title'), res.get('description', ''))