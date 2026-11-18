import os, json, base64, requests

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

r = requests.get(f'https://api.github.com/repos/{REPO}/contents/ocr_status.json',
                 headers=HEADERS, timeout=60).json()
d = json.loads(base64.b64decode(r['content']).decode())

for k, v in d.get('ocr', {}).items():
    path = f'ocr/{k}.txt'
    payload = {'message': f'chore: ocr {k}', 'content': base64.b64encode(v.encode()).decode(), 'branch': 'main'}
    resp = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, json=payload, timeout=90)
    if resp.status_code not in (200, 201):
        cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, timeout=30).json()
        payload['sha'] = cur.get('sha')
        resp = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, json=payload, timeout=90)
    print(k, resp.status_code, len(v), flush=True)

with open('ocr_index.json', 'w') as f:
    json.dump({k: len(v) for k, v in d.get('ocr', {}).items()}, f, indent=1)
body = base64.b64encode(open('ocr_index.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/ocr_index.json', headers=HEADERS,
             json={'message': 'chore: ocr index', 'content': body, 'branch': 'main'}, timeout=60)
print('DONE')
