import os, json, base64, glob, requests, subprocess

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

PL = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
      'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
      'Dfp81qoRN3F', 'DfutcjmRsVt']

os.makedirs('frames', exist_ok=True)

# если листов нет — строим заново из уже скачанных mp4
if not glob.glob('frames/*.jpg'):
    for p in PL:
        mp4 = f'audio/{p}.mp4'
        if not os.path.exists(mp4):
            continue
        try:
            dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                        'format=duration', '-of', 'csv=p=0', mp4],
                                       capture_output=True, text=True, timeout=60).stdout.strip() or 0)
        except Exception:
            dur = 0
        tmp = []
        for i in range(6):
            t = max(0.0, dur * (i + 0.5) / 6)
            out = f'audio/f{i}_{p}.jpg'
            subprocess.run(['ffmpeg', '-y', '-ss', str(t), '-i', mp4, '-frames:v', '1',
                            '-vf', 'scale=270:480', out], capture_output=True, timeout=180)
            if os.path.exists(out):
                tmp.append(out)
        if not tmp:
            continue
        cmd = ['ffmpeg', '-y']
        for t in tmp:
            cmd += ['-i', t]
        filt = ''.join(f'[{i}:v]' for i in range(len(tmp))) + f'hstack=inputs={len(tmp)}'
        subprocess.run(cmd + ['-filter_complex', filt, f'frames/{p}.jpg'],
                       capture_output=True, timeout=180)

sheets = sorted(glob.glob('frames/*.jpg'))
print('sheets:', len(sheets), flush=True)

urls = {}
for s in sheets:
    name = s.split('/')[-1]
    data = open(s, 'rb').read()
    body = base64.b64encode(data).decode()
    path = f'sheets/{name}'
    payload = {'message': f'chore: frame sheet {name}', 'content': body, 'branch': 'main'}
    r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}',
                     headers=HEADERS, json=payload, timeout=90)
    if r.status_code not in (200, 201):
        cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}',
                           headers=HEADERS, timeout=30).json()
        payload['sha'] = cur.get('sha')
        r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}',
                         headers=HEADERS, json=payload, timeout=90)
    print(name, r.status_code, len(data), flush=True)
    if r.status_code in (200, 201):
        urls[name] = f'https://raw.githubusercontent.com/{REPO}/main/{path}'

with open('sheets.json', 'w') as f:
    json.dump(urls, f, ensure_ascii=False, indent=1)

gh = os.environ.get('GITHUB_TOKEN', '')
if gh:
    body = base64.b64encode(open('sheets.json', 'rb').read()).decode()
    requests.put(f'https://api.github.com/repos/{REPO}/contents/sheets.json',
                 headers=HEADERS, json={'message': 'chore: sheet urls', 'content': body, 'branch': 'main'},
                 timeout=60)
print('DONE', len(urls))
