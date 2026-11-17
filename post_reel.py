import os, json, base64, subprocess, time, requests

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
BRANCH = 'main'
GH = os.environ.get('GITHUB_TOKEN', '')
TOK = os.environ.get('PRODUCTS_TOKEN', '')
API = f'https://api.telegram.org/bot{TOK}'
STATE_PATH = 'reels_state.json'
QUEUE_PATH = 'reels.json'
REPORT_PATH = 'reels_report.json'
DRY = os.environ.get('DRY_RUN', '0') == '1'
LOG = []


def log(*a):
    line = ' '.join(str(x) for x in a)
    LOG.append(line)
    print(line)


def gh_get(path):
    r = requests.get(f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}', timeout=30)
    r.raise_for_status()
    return r.json()


def gh_put(path, data, msg):
    body = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=1).encode('utf-8')).decode()
    headers = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}
    payload = {'message': msg, 'content': body, 'branch': BRANCH}
    r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=headers, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        try:
            cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=headers, timeout=30).json()
            payload['sha'] = cur['sha']
            r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=headers, json=payload, timeout=60)
        except Exception as e:
            log('sha retry failed', e)
    if r.status_code not in (200, 201):
        log('gh_put failed', r.status_code, r.text[:200])
        return False
    log('gh_put ok', path)
    return True


def save_report():
    try:
        gh_put(REPORT_PATH, {'log': LOG[-40:]}, 'reels: report')
    except Exception as e:
        log('report failed', e)


def download(url, out):
    cmd = ['yt-dlp', '-f', 'bestvideo+bestaudio/best', '--merge-output-format', 'mp4',
           '-o', out, '--no-playlist', url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    log('yt-dlp rc', r.returncode)
    if r.returncode != 0:
        log((r.stderr or '')[-400:])
        return None
    base = out.rsplit('.', 1)[0]
    for ext in ('.mp4', '.mkv', '.webm'):
        if os.path.exists(base + ext):
            return base + ext
    return None


def try_send(item, path):
    with open(path, 'rb') as f:
        return requests.post(f'{API}/sendVideo',
                             data={'chat_id': item['chat'], 'caption': item['caption'],
                                   'supports_streaming': 'true'},
                             files={'video': ('reel.mp4', f, 'video/mp4')}, timeout=900).json()


def main():
    try:
        queue = gh_get(QUEUE_PATH)
    except Exception as e:
        log('queue fetch failed', e); save_report(); return
    try:
        state = gh_get(STATE_PATH)
    except Exception:
        state = {'published': [], 'skipped': []}
    state.setdefault('published', [])
    state.setdefault('skipped', [])

    pending = [q for q in queue
               if q['permalink'] not in state['published'] and q['permalink'] not in state['skipped']]
    log('pending', len(pending), 'published', len(state['published']), 'skipped', len(state['skipped']))
    if not pending:
        log('nothing to publish'); save_report(); return

    for item in pending:
        log('trying', item['permalink'], '->', item['chat'])
        path = download(item['permalink'], 'reel.mp4')
        if not path:
            log('download failed, skip this reel')
            state['skipped'].append(item['permalink'])
            gh_put(STATE_PATH, state, 'reels: skipped (download)')
            continue
        log('downloaded', path, os.path.getsize(path), 'bytes')
        if DRY:
            log('DRY RUN - not sending. caption:', item['caption'])
            save_report()
            return
        r = try_send(item, path)
        log('sendVideo', json.dumps(r, ensure_ascii=False)[:300])
        if not r.get('ok'):
            desc = r.get('description', '')
            log('send failed:', desc)
            if 'member' in desc.lower() or 'forbidden' in desc.lower() or 'not a member' in desc.lower():
                state['skipped'].append(item['permalink'])
                gh_put(STATE_PATH, state, f'reels: skipped {item["chat"]} (no access)')
                log('skipped (no access), trying next')
                continue
            log('hard failure, stop')
            save_report()
            return
        msg = r['result']
        log('PUBLISHED to', item['chat'], 'message_id', msg.get('message_id'))
        state['published'].append(item['permalink'])
        state['last'] = {'permalink': item['permalink'], 'chat': item['chat'],
                         'date': item['date'], 'message_id': msg.get('message_id')}
        gh_put(STATE_PATH, state, f'reels: published {item["date"]} -> {item["chat"]}')
        save_report()
        return
    save_report()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log('FATAL', repr(e))
        save_report()
        raise