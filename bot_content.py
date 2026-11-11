import os, json, time, requests

TOK = os.environ.get('CONTENT_TOKEN') or os.environ.get('EXCURSIONS_TOKEN') or '7795659732:AAFjnsBxLndGWUllspEp-TcFmZ6_k9hKVT4'
API = f'https://api.telegram.org/bot{TOK}'
CHANNEL = '@morskieakvarium'
BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, 'content_queue.json')

# Публикуем ровно один раз в сутки: cron срабатывает ежечасно в :07 минут,
# и только один из этих запусков попадает в PUBLISH_HOURS.
# Выбор поста детерминирован по номеру дня - state-файл не нужен,
# поэтому повторные публикации и гонка между прогонами невозможны.
PUBLISH_HOURS = {6}   # 06:07 UTC = 09:07 MSK


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


def main():
    if not TOK:
        print('no token')
        return
    now = time.gmtime()
    if now.tm_hour not in PUBLISH_HOURS:
        print('not publish hour, skipping (hour=%s)' % now.tm_hour)
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
    print('selected:', target.get('id'), 'day_index', day_index)
    r = api('sendMessage', chat_id=CHANNEL, text=target['text'],
            disable_web_page_preview=True)
    if r.get('ok'):
        print('published', target.get('id'), 'msg', r.get('result', {}).get('message_id'))
    else:
        print('failed:', str(r)[:250])


if __name__ == '__main__':
    main()
