import os, json, base64, requests

TOK = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
CHAT = '@murmansk_moreprodukt'
LOG = []


def log(*a):
    line = ' '.join(str(x) for x in a)
    LOG.append(line); print(line)


def gh_put(path, data, msg):
    gh = os.environ.get('GITHUB_TOKEN', '')
    body = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=1).encode('utf-8')).decode()
    headers = {'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'}
    payload = {'message': msg, 'content': body, 'branch': 'main'}
    r = requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/' + path,
                     headers=headers, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        cur = requests.get('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/' + path,
                           headers=headers, timeout=30).json()
        payload['sha'] = cur['sha']
        r = requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/' + path,
                         headers=headers, json=payload, timeout=60)
    log('gh_put', path, r.status_code)


# 1) удалить сообщение 62 (осталось со старой подписью)
d = requests.post(f'{API}/deleteMessage', data={'chat_id': CHAT, 'message_id': 62}, timeout=30).json()
log('delete 62:', json.dumps(d, ensure_ascii=False)[:250])

# 2) собрать описания рилсов Instagram для проверки каталогизации
PERMALINKS = [
    'https://www.instagram.com/reel/DfutcjmRsVt/',
    'https://www.instagram.com/reel/Dft8_zaxaeh/',
    'https://www.instagram.com/reel/DfsSvXER3zo/',
    'https://www.instagram.com/reel/DfpQTqIovvG/',
    'https://www.instagram.com/reel/Df2tXDuIh4X/',
    'https://www.instagram.com/reel/Df2ssCyIpqd/',
    'https://www.instagram.com/reel/Df2sOQYoYHW/',
    'https://www.instagram.com/reel/Df0Dnj0RQcZ/',
    'https://www.instagram.com/reel/Dfxvor8xYXi/',
    'https://www.instagram.com/reel/DfxcubsRhHZ/',
    'https://www.instagram.com/reel/DfvDT0oxpQ7/',
    'https://www.instagram.com/reel/Dfp81qoRN3F/',
]
info = {}
for p in PERMALINKS:
    try:
        r = requests.get(p, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        html = r.text
        desc = ''
        i = html.find('"description"')
        if i > 0:
            desc = html[i:i+700]
        i2 = html.find('og:description')
        if i2 > 0:
            desc = html[i2:i2+700]
        info[p] = {'status': r.status_code, 'snippet': desc[:600]}
    except Exception as e:
        info[p] = {'error': repr(e)[:200]}

gh_put('reels_descriptions.json', info, 'chore: instagram reel descriptions for review')

# 3) обновить state: 62 удалён, первый рилс снова в очереди
try:
    st = requests.get('https://raw.githubusercontent.com/litvinenko0100-a11y/vkusmorey-bots/main/reels_state.json', timeout=30).json()
except Exception:
    st = {'published': [], 'skipped': []}
st.setdefault('published', [])
st.setdefault('skipped', [])
if 'https://www.instagram.com/reel/DfutcjmRsVt/' in st['published']:
    st['published'].remove('https://www.instagram.com/reel/DfutcjmRsVt/')
st['deleted'] = [{'message_id': 62, 'permalink': 'https://www.instagram.com/reel/DfutcjmRsVt/',
                  'reason': 'published with old caption before captionless mode'}]
gh_put('reels_state.json', st, 'reels: deleted message 62, restored reel to queue')

log('done')