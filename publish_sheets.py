import os, json, base64, glob, requests, subprocess

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

PL = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
      'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
      'Dfp81qoRN3F', 'DfutcjmRsVt']

os.makedirs('audio', exist_ok=True)
os.makedirs('frames', exist_ok=True)


def sh(cmd, timeout=900):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


# 1) скачать рилсы (нужны для кадров)
for p in PL:
    mp4 = f'audio/{p}.mp4'
    if os.path.exists(mp4) and os.path.getsize(mp4) > 100000:
        print('have', p, flush=True)
        continue
    r = sh(['yt-dlp', '-f', 'bestvideo+bestaudio/best', '--merge-output-format', 'mp4',
            '-o', mp4, '--no-playlist', '--quiet',
            f'https://www.instagram.com/reel/{p}/'])
    print('dl', p, r.returncode, os.path.exists(mp4), flush=True)

# 2) построить контактные листы: 6 кадров в ряд
for p in PL:
    mp4 = f'audio/{p}.mp4'
    sheet = f'frames/{p}.jpg'
    if os.path.exists(sheet):
        continue
    if not os.path.exists(mp4):
        print('NO MP4', p, flush=True)
        continue
    try:
        dur = float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                         '-of', 'csv=p=0', mp4], 60).stdout.strip() or 0)
    except Exception:
        dur = 0
    if dur <= 0:
        dur = 15.0
    tmp = []
    for i in range(6):
        t = max(0.0, dur * (i + 0.5) / 6)
        out = f'audio/f{i}_{p}.jpg'
        sh(['ffmpeg', '-y', '-ss', str(t), '-i', mp4, '-frames:v', '1',
            '-vf', 'scale=270:480', out], 180)
        if os.path.exists(out):
            tmp.append(out)
    if not tmp:
        print('FRAMES FAIL', p, flush=True)
        continue
    cmd = ['ffmpeg', '-y']
    for t in tmp:
        cmd += ['-i', t]
    filt = ''.join(f'[{i}:v]' for i in range(len(tmp))) + f'hstack=inputs={len(tmp)}'
    sh(cmd + ['-filter_complex', filt, sheet], 180)
    print('sheet', p, os.path.exists(sheet), flush=True)

# 3) опубликовать листы через Contents API
sheets = sorted(glob.glob('frames/*.jpg'))
print('sheets:', len(sheets), flush=True)
urls = {}
for s in sheets:
    name = s.split('/')[-1]
    data = open(s, 'rb').read()
    path = f'sheets/{name}'
    payload = {'message': f'chore: frame sheet {name}',
               'content': base64.b64encode(data).decode(), 'branch': 'main'}
    r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}',
                     headers=HEADERS, json=payload, timeout=120)
    if r.status_code not in (200, 201):
        cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}',
                           headers=HEADERS, timeout=30).json()
        payload['sha'] = cur.get('sha')
        r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}',
                         headers=HEADERS, json=payload, timeout=120)
    print(name, r.status_code, len(data), flush=True)
    if r.status_code in (200, 201):
        urls[name] = f'https://raw.githubusercontent.com/{REPO}/main/{path}'

with open('sheets.json', 'w') as f:
    json.dump(urls, f, ensure_ascii=False, indent=1)

body = base64.b64encode(open('sheets.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/sheets.json',
             headers=HEADERS, json={'message': 'chore: sheet urls', 'content': body, 'branch': 'main'},
             timeout=60)
print('DONE', len(urls))
