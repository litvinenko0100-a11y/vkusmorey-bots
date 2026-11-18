import os, json, base64, glob, requests, subprocess, sys, traceback

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

PL = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
      'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
      'Dfp81qoRN3F', 'DfutcjmRsVt']

STATUS = {'steps': [], 'sheets': {}}
def log(m):
    STATUS['steps'].append(str(m))
    print(m, flush=True)
    try:
        with open('publish_status.json', 'w') as f:
            json.dump(STATUS, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def publish_status():
    try:
        body = base64.b64encode(open('publish_status.json', 'rb').read()).decode()
        r = requests.put(f'https://api.github.com/repos/{REPO}/contents/publish_status.json',
                         headers=HEADERS, json={'message': 'chore: publish status', 'content': body, 'branch': 'main'},
                         timeout=60)
        log('status pushed ' + str(r.status_code))
    except Exception as e:
        log('status push fail ' + repr(e))


os.makedirs('audio', exist_ok=True)
os.makedirs('frames', exist_ok=True)
log('start ' + sys.version.split()[0])

# 1) скачать
for p in PL:
    try:
        cands = glob.glob(f'audio/{p}*.mp4')
        if not cands:
            r = subprocess.run(['yt-dlp', '-f', 'bestvideo+bestaudio/best', '--merge-output-format', 'mp4',
                                '-o', f'audio/{p}.mp4', '--no-playlist',
                                f'https://www.instagram.com/reel/{p}/'],
                               capture_output=True, text=True, timeout=600)
            cands = glob.glob(f'audio/{p}*.mp4')
            log(f'dl {p} rc={r.returncode} files={len(cands)} err={(r.stderr or "")[-160:]}')
        else:
            log(f'have {p}')
    except Exception:
        log(f'dl EXC {p} ' + traceback.format_exc()[-300:])

# 2) кадры + лист
for p in PL:
    try:
        sheet = f'frames/{p}.jpg'
        cands = glob.glob(f'audio/{p}*.mp4')
        if not cands:
            log(f'no mp4 {p}')
            continue
        mp4 = sorted(cands, key=os.path.getsize)[-1]
        pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                             '-of', 'csv=p=0', mp4], capture_output=True, text=True, timeout=60)
        try:
            dur = float(pr.stdout.strip())
        except Exception:
            dur = 15.0
        tmp = []
        for i in range(6):
            t = max(0.0, dur * (i + 0.5) / 6)
            out = f'audio/f{i}_{p}.jpg'
            subprocess.run(['ffmpeg', '-y', '-ss', str(t), '-i', mp4, '-frames:v', '1',
                            '-vf', 'scale=270:480', out], capture_output=True, timeout=180)
            if os.path.exists(out):
                tmp.append(out)
        if not tmp:
            log(f'no frames {p}')
            continue
        cmd = ['ffmpeg', '-y']
        for t in tmp:
            cmd += ['-i', t]
        filt = ''.join(f'[{i}:v]' for i in range(len(tmp))) + f'hstack=inputs={len(tmp)}'
        subprocess.run(cmd + ['-filter_complex', filt, sheet], capture_output=True, timeout=180)
        ok = os.path.exists(sheet)
        log(f'sheet {p} {ok}')
        if ok:
            data = open(sheet, 'rb').read()
            path = f'sheets/{p}.jpg'
            payload = {'message': f'chore: frame sheet {p}', 'content': base64.b64encode(data).decode(), 'branch': 'main'}
            r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, json=payload, timeout=120)
            if r.status_code not in (200, 201):
                cur = requests.get(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, timeout=30).json()
                payload['sha'] = cur.get('sha')
                r = requests.put(f'https://api.github.com/repos/{REPO}/contents/{path}', headers=HEADERS, json=payload, timeout=120)
            log(f'push {p} {r.status_code} {len(data)}')
            if r.status_code in (200, 201):
                STATUS['sheets'][p] = f'https://raw.githubusercontent.com/{REPO}/main/{path}'
    except Exception:
        log(f'frames EXC {p} ' + traceback.format_exc()[-300:])

with open('sheets.json', 'w') as f:
    json.dump(STATUS['sheets'], f, ensure_ascii=False, indent=1)
body = base64.b64encode(open('sheets.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/sheets.json',
             headers=HEADERS, json={'message': 'chore: sheet urls', 'content': body, 'branch': 'main'}, timeout=60)
publish_status()
log('DONE sheets=' + str(len(STATUS['sheets'])))
