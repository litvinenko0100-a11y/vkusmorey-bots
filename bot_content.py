import os, json, time, base64, requests

TOK = os.environ.get('CONTENT_TOKEN') or os.environ.get('EXCURSIONS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
CHANNEL = '@morskieakvarium'
BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, 'content_queue.json')
STATE = os.path.join(BASE, 'content_state.json')

OWNER = 'litvinenko0100-a11y'
REPO = 'vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')

# Публикуем один пост в сутки. Защита от дублей - файл content_state.json
# в репозитории: в нём дата последней публикации. Он НО в эфемерном раннере,
# поэтому переживает перезапуски и не может потеряться.
# Выбор поста детерминирован по номеру дня - гонки между прогонами невозможны.


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


def today_utc():
    return time.strftime('%Y-%m-%d', time.gmtime())


def read_state():
    try:
        url = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/main/content_state.json'
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def write_state(data):
    if not GH:
        print('no GITHUB_TOKEN, state not persisted')
        return
    try:
        body = json.dumps(data, ensure_ascii=False, indent=1).encode('utf-8')
        payload = {
            'message': f'content: published {data.get("date")}',
            'content': base64.b64encode(body).decode(),
            'branch': 'main',
            'path': 'content_state.json',
        }
        # если файл есть - нужен его sha
        raw = requests.get(
            f'https://api.github.com/repos/{OWNER}/{REPO}/contents/content_state.json',
            headers={'Authorization': f'Bearer {GH}'}, timeout=30).json()
        if isinstance(raw, dict) and raw.get('sha'):
            payload['sha'] = raw['sha']
        h = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}
        r = requests.put(f'https://api.github.com/repos/{OWNER}/{REPO}/contents/content_state.json',
                         json=payload, headers=h, timeout=40)
        print('state saved:', r.status_code)
    except Exception as e:
        print('state write failed:', str(e)[:150])


def main():
    if not TOK:
        print('no token')
        return
    today = today_utc()
    st = read_state()
    if st.get('date') == today:
        print('already published today (%s), skipping' % today)
        return
    try:
        with open(QUEUE, encoding='utf-8') as f:
            items = json.load(f)
    except Exception as e:
        print('queue error:', e)
        return
    if not items:
        print('queue empty')
        return
    day_index = int(time.time() // 86400)
    target = items[day_index % len(items)]
    print('selected:', target.get('id'), 'day_index', day_index, 'date', today)
    r = api('sendMessage', chat_id=CHANNEL, text=target['text'],
            disable_web_page_preview=True)
    if r.get('ok'):
        mid = r.get('result', {}).get('message_id')
        print('published', target.get('id'), 'msg', mid)
        write_state({'date': today, 'post_id': target.get('id'), 'message_id': mid})
    else:
        print('failed:', str(r)[:250])


if __name__ == '__main__':
    main()
