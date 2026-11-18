import os, json, base64, requests, subprocess, glob

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

PL = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
      'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
      'Dfp81qoRN3F', 'DfutcjmRsVt']

os.makedirs('mont', exist_ok=True)
files = []
for i, p in enumerate(PL):
    src = f'sheets/{p}.jpg'
    dst = f'mont/{i:02d}_{p}.jpg'
    if not os.path.exists(dst):
        r = requests.get(f'https://raw.githubusercontent.com/{REPO}/main/{src}', timeout=60)
        if r.status_code != 200:
            print('skip', p, r.status_code, flush=True)
            continue
        open(dst, 'wb').write(r.content)
    files.append(dst)

print('have', len(files), flush=True)
if not files:
    raise SystemExit('no sheets')

args = ['ffmpeg', '-y']
for f in files:
    args += ['-i', f]
filt = ''.join(f'[{i}:v]' for i in range(len(files))) + f'vstack=inputs={len(files)}'
args += ['-filter_complex', filt, '-q:v', '3', 'mont/all.jpg']
r = subprocess.run(args, capture_output=True, text=True, timeout=300)
print('rc', r.returncode, (r.stderr or '')[-300:], flush=True)

data = open('mont/all.jpg', 'rb').read()
payload = {'message': 'chore: montage of all reel sheets',
           'content': base64.b64encode(data).decode(), 'branch': 'main'}
resp = requests.put(f'https://api.github.com/repos/{REPO}/contents/montage.jpg', headers=HEADERS, json=payload, timeout=180)
if resp.status_code not in (200, 201):
    cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/montage.jpg', headers=HEADERS, timeout=30).json()
    payload['sha'] = cur.get('sha')
    resp = requests.put(f'https://api.github.com/repos/{REPO}/contents/montage.jpg', headers=HEADERS, json=payload, timeout=180)
print('push', resp.status_code, len(data), flush=True)

with open('mont/order.json', 'w') as f:
    json.dump({'files': files, 'ids': PL}, f, indent=1)
body = base64.b64encode(open('mont/order.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/montage_order.json', headers=HEADERS,
             json={'message': 'chore: montage order', 'content': body, 'branch': 'main'}, timeout=60)
print('DONE')
