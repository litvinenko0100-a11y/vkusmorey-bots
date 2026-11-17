import os, json, base64, subprocess, glob, traceback, shutil, sys

PL = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
      'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
      'Dfp81qoRN3F', 'DfutcjmRsVt']

os.makedirs('audio', exist_ok=True)
os.makedirs('frames', exist_ok=True)
log = []

def step(msg):
    print(msg, flush=True)
    log.append(msg)

have = {}
for p in PL:
    mp4 = f'audio/{p}.mp4'
    if not os.path.exists(mp4):
        r = subprocess.run(['yt-dlp', '-f', 'bestvideo+bestaudio/best',
                            '--merge-output-format', 'mp4', '-o', mp4,
                            '--no-playlist', '--quiet',
                            f'https://www.instagram.com/reel/{p}/'],
                           capture_output=True, text=True, timeout=900)
        if r.returncode != 0 or not os.path.exists(mp4):
            step(f'DL FAIL {p}: {(r.stderr or "")[-200:]}')
            continue
    have[p] = mp4
    step(f'downloaded {p} {os.path.getsize(mp4)}')

for p, mp4 in have.items():
    wav = f'audio/{p}.wav'
    if os.path.exists(wav):
        continue
    rr = subprocess.run(['ffmpeg', '-y', '-i', mp4, '-vn', '-ac', '1', '-ar', '16000', wav],
                        capture_output=True, text=True, timeout=300)
    if not os.path.exists(wav):
        step(f'WAV FAIL {p}')

# контактные листы: 6 кадров вертикальной сеткой 2x3
for p, mp4 in have.items():
    sheet = f'frames/{p}.jpg'
    if os.path.exists(sheet):
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
    if len(tmp) < 1:
        step(f'FRAMES FAIL {p}')
        continue
    cmd = ['ffmpeg', '-y']
    for t in tmp:
        cmd += ['-i', t]
    filt = ''.join(f'[{i}:v]' for i in range(len(tmp))) + f'hstack=inputs={len(tmp)}'
    subprocess.run(cmd + ['-filter_complex', filt, sheet], capture_output=True, timeout=180)
    step(f'sheet {p} {os.path.exists(sheet)}')

# распознавание речи
res = {}
try:
    from faster_whisper import WhisperModel
    m = WhisperModel('tiny', device='cpu', compute_type='int8')
    for f in sorted(glob.glob('audio/*.wav')):
        p = os.path.basename(f)[:-4]
        try:
            segs, _ = m.transcribe(f, language='ru', vad_filter=True)
            txt = ' '.join(s.text.strip() for s in segs)
        except Exception as e:
            txt = f'__ERR__ {e!r}'
        res[p] = txt
        step(f'ASR {p} | {txt[:300]}')
except Exception:
    step('ASR INIT FAIL: ' + traceback.format_exc()[-800:])

with open('reels_classified.json', 'w') as f:
    json.dump({'transcripts': res, 'downloaded': list(have.keys()), 'log': log},
              f, ensure_ascii=False, indent=1)

gh = os.environ.get('GITHUB_TOKEN', '')
if gh:
    import requests
    body = base64.b64encode(open('reels_classified.json', 'rb').read()).decode()
    resp = requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/reels_classified.json',
                        headers={'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'},
                        json={'message': 'chore: reel classification v2', 'content': body, 'branch': 'main'},
                        timeout=60)
    step('PUSH ' + str(resp.status_code))

step('DONE')
print('\n'.join(log[-5:]), flush=True)
