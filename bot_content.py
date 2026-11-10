import os, json, time, requests

TOK = os.environ.get('CONTENT_TOKEN') or os.environ.get('EXCURSIONS_TOKEN') or '7795659732:AAFjnsBxLndGWUllspEp-TcFmZ6_k9hKVT4'
API = f'https://api.telegram.org/bot{TOK}'
CHANNEL = '@morskieakvarium'
BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, 'content_queue.json')
STATE = os.path.join(BASE, 'content_state.json')
MIN_GAP = 4 * 3600


def api(method, **kw):
    for _ in range(5):
        try:
            r = requests.post(f'{API}/{method}', data=kw, timeout=30).json()
            if r.get('ok'):
                return r
            time.sleep(3)
        except Exception:
            time.sleep(3)
    return {'ok': False}


def load(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def save(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def main():
    if not TOK:
        print('no token')
        return
    items = load(QUEUE, [])
    if not items:
        print('content queue is empty')
        return
    state = load(STATE, {'last_posted': '', 'last_at': 0})
    now = int(time.time())
    if now - state.get('last_at', 0) < MIN_GAP:
        print('gap not reached, skipping')
        return
    target = None
    for it in items:
        if it.get('id') != state.get('last_posted'):
            target = it
            break
    if not target:
        print('nothing new')
        return
    r = api('sendMessage', chat_id=CHANNEL, text=target['text'], disable_web_page_preview=True)
    if r.get('ok'):
        state['last_posted'] = target['id']
        state['last_at'] = now
        save(STATE, state)
        print('published', target['id'])
    else:
        print('failed', str(r)[:200])


if __name__ == '__main__':
    main()
