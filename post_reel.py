import os, json, base64, subprocess, sys, time, requests

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
BRANCH = 'main'
GH = os.environ.get('GITHUB_TOKEN', '')
TOK = os.environ.get('PRODUCTS_TOKEN') or os.environ.get('EXCURSIONS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
STATE_PATH = 'reels_state.json'
QUEUE_PATH = 'reels.json'
DRY = os.environ.get('DRY_RUN', '0') == '1'


def gh_get(path):
    r = requests.get(f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}', timeout=30)
    r.raise_for_status()
    return r.json()


def gh_put(path, data, msg):
    body = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=1).encode('utf-8')).decode()
    payload = {'message': msg, 'content': body, 'branch': BRANCH}
    r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}',
                     headers={'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'},
                     json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def download(url, out):
    cmd = ['yt-dlp', '-f', 'bestvideo+bestaudio/best', '--merge-output-format', 'mp4',
           '-o', out, '--no-playlist', '--quiet', url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print('yt-dlp failed:', r.stderr[-800:])
        return None
    base = out.rsplit('.', 1)[0]
    for ext in ('.mp4', '.mkv', '.webm'):
        if os.path.exists(base + ext):
            return base + ext
    return None


def main():
    queue = gh_get(QUEUE_PATH)
    try:
        state = gh_get(STATE_PATH)
    except Exception:
        state = {'published': []}
    pending = [q for q in queue if q['permalink'] not in state['published']]
    if not pending:
        print('no pending reels')
        return
    item = pending[0]
    print('next reel:', item['permalink'], '->', item['chat'])
    if DRY:
        print('DRY RUN caption:', item['caption'])
        return
    path = download(item['permalink'], 'reel.mp4')
    if not path:
        print('download failed, nothing published')
        return
    print('downloaded', path, os.path.getsize(path))
    with open(path, 'rb') as f:
        r = requests.post(f'{API}/sendVideo',
                          data={'chat_id': item['chat'], 'caption': item['caption'],
                                'supports_streaming': 'true'},
                          files={'video': ('reel.mp4', f, 'video/mp4')}, timeout=900).json()
    if not r.get('ok'):
        print('sendVideo failed:', r)
        return
    msg = r['result']
    print('published to', item['chat'], 'message_id', msg.get('message_id'))
    state['published'].append(item['permalink'])
    state['last'] = {'permalink': item['permalink'], 'chat': item['chat'],
                     'date': item['date'], 'message_id': msg.get('message_id')}
    gh_put(STATE_PATH, state, f'reels: published {item["date"]} -> {item["chat"]}')


if __name__ == '__main__':
    main()