import os, json, base64, glob, requests, subprocess, sys, traceback

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}

PL = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
      'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
      'Dfp81qoRN3F', 'DfutcjmRsVt']

STATUS = {'steps': [], 'ocr': {}}


def log(m):
    STATUS['steps'].append(str(m))
    print(m, flush=True)
    try:
        with open('ocr_status.json', 'w') as f:
            json.dump(STATUS, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


os.makedirs('audio', exist_ok=True)
os.makedirs('frames', exist_ok=True)

for p in PL:
    try:
        cands = glob.glob(f'audio/{p}*.mp4')
        if not cands:
            r = subprocess.run(['yt-dlp', '-f', 'bestvideo+bestaudio/best', '--merge-output-format', 'mp4',
                                '-o', f'audio/{p}.mp4', '--no-playlist',
                                f'https://www.instagram.com/reel/{p}/'],
                               capture_output=True, text=True, timeout=600)
            cands = glob.glob(f'audio/{p}*.mp4')
            log(f'dl {p} rc={r.returncode} files={len(cands)}')
        else:
            log(f'have {p}')
        if not cands:
            continue
        mp4 = sorted(cands, key=os.path.getsize)[-1]
        pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                             '-of', 'csv=p=0', mp4], capture_output=True, text=True, timeout=60)
        try:
            dur = float(pr.stdout.strip())
        except Exception:
            dur = 15.0
        texts = []
        for i in range(9):
            t = max(0.0, dur * (i + 0.5) / 9)
            out = f'frames/f{i}_{p}.png'
            subprocess.run(['ffmpeg', '-y', '-ss', str(t), '-i', mp4, '-frames:v', '1',
                            '-vf', 'scale=540:960', out], capture_output=True, timeout=180)
            if not os.path.exists(out):
                continue
            oc = subprocess.run(['tesseract', out, 'stdout', '-l', 'rus+eng'],
                                capture_output=True, text=True, timeout=180)
            txt = ' '.join((oc.stdout or '').split())
            if txt:
                texts.append(txt)
        STATUS['ocr'][p] = ' | '.join(texts)
        log(f'ocr {p} chars={len(STATUS["ocr"][p])} :: {STATUS["ocr"][p][:300]}')
    except Exception:
        log(f'EXC {p} ' + traceback.format_exc()[-300:])

with open('ocr_status.json', 'w') as f:
    json.dump(STATUS, f, ensure_ascii=False, indent=1)
body = base64.b64encode(open('ocr_status.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/ocr_status.json',
             headers=HEADERS, json={'message': 'chore: reel OCR', 'content': body, 'branch': 'main'}, timeout=60)
log('DONE')
