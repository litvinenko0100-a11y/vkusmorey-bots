import os, json, base64, requests, subprocess

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

r = requests.get(f'https://api.github.com/repos/{REPO}/contents/montage_order.json', headers=HEADERS, timeout=60).json()
order = json.loads(base64.b64decode(r['content']).decode())
ids = order['ids']
print('ids', len(ids), flush=True)

os.makedirs('split', exist_ok=True)
src = 'montage.jpg'
if not os.path.exists(src):
    data = requests.get(f'https://raw.githubusercontent.com/{REPO}/main/montage.jpg', timeout=180).content
    open(src, 'wb').write(data)

try:
    from PIL import Image
    im = Image.open(src)
    W, H = im.size
    print('size', W, H, flush=True)
    n = len(ids)
    step = H // n
    for i, pid in enumerate(ids):
        box = (0, i * step, W, (i + 1) * step if i < n - 1 else H)
        crop = im.crop(box)
        crop.thumbnail((900, 9000))
        crop.save(f'split/{i:02d}_{pid}.jpg', quality=88)
        print('crop', i, pid, crop.size, flush=True)
except Exception as e:
    print('PIL FAIL', e, flush=True)
    raise

for i, pid in enumerate(ids):
    path = f'sheets_split/{i:02d}_{pid}.jpg'
    data = open(f'split/{i:02d}_{pid}.jpg', 'rb').read()
    payload = {'message': f'chore: sheet {pid}', 'content': base64.b64encode(data).decode(), 'branch': 'main'}
    resp = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, json=payload, timeout=180)
    if resp.status_code not in (200, 201):
        cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, timeout=30).json()
        payload['sha'] = cur.get('sha')
        resp = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, json=payload, timeout=180)
    print('push', path, resp.status_code, len(data), flush=True)

idx = {'order': ids, 'files': [f'sheets_split/{i:02d}_{p}.jpg' for i, p in enumerate(ids)]}
with open('sheets_split/index.json', 'w') as f:
    json.dump(idx, f, indent=1)
body = base64.b64encode(open('sheets_split/index.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/sheets_split/index.json', headers=HEADERS,
             json={'message': 'chore: sheets index', 'content': body, 'branch': 'main'}, timeout=60)
print('DONE')
