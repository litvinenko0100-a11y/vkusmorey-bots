import os, json, base64, subprocess, glob, shutil

PL = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
      'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
      'Dfp81qoRN3F', 'DfutcjmRsVt']

os.makedirs('audio', exist_ok=True)
os.makedirs('frames', exist_ok=True)

# 1) скачать рилсы
have = {}
for p in PL:
    mp4 = f'audio/{p}.mp4'
    if not os.path.exists(mp4):
        r = subprocess.run(['yt-dlp', '-f', 'bestvideo+bestaudio/best', '--merge-output-format', 'mp4',
                            '-o', mp4, '--no-playlist', '--quiet',
                            f'https://www.instagram.com/reel/{p}/'],
                           capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            print('DL FAIL', p, (r.stderr or '')[-150:], flush=True)
            continue
    have[p] = mp4
    print('downloaded', p, os.path.getsize(mp4), flush=True)

# 2) аудио 16k mono
for p, mp4 in have.items():
    wav = f'audio/{p}.wav'
    if os.path.exists(wav):
        continue
    subprocess.run(['ffmpeg', '-y', '-i', mp4, '-vn', '-ac', '1', '-ar', '16000', wav],
                   capture_output=True, timeout=300)

# 3) контактные листы по 6 кадров
for p, mp4 in have.items():
    sheet = f'frames/{p}.jpg'
    if os.path.exists(sheet):
        continue
    parts = []
    for i in range(6):
        parts += ['-ss', str(i * 3), '-i', mp4, '-frames:v', '1']
    tmp = [f'audio/f{i}_{p}.jpg' for i in range(6)]
    cmd = ['ffmpeg', '-y']
    for i in range(6):
        cmd += ['-ss', str(i * 3), '-i', mp4, '-frames:v', '1', '-vf', 'scale=270:480', tmp[i]]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    ok = [t for t in tmp if os.path.exists(t)]
    if not ok:
        print('FRAMES FAIL', p, (r.stderr or '')[-150:], flush=True)
        continue
    inputs = []
    for t in ok:
        inputs += ['-i', t]
    filt = ''.join(f'[{i}:v]' for i in range(len(ok)))
    filt += f'hstack=inputs={len(ok)}' if len(ok) == 6 else 'hstack=inputs=' + str(len(ok))
    subprocess.run(['ffmpeg', '-y'] + inputs + ['-filter_complex', filt, sheet],
                   capture_output=True, timeout=300)
    print('sheet', p, os.path.exists(sheet), flush=True)

# 4) распознавание речи
res = {}
try:
    from faster_whisper import WhisperModel
    m = WhisperModel('tiny', device='cpu', compute_type='int8')
    for f in sorted(glob.glob('audio/*.wav')):
        p = os.path.basename(f)[:-4]
        segs, _ = m.transcribe(f, language='ru', vad_filter=True)
        txt = ' '.join(s.text.strip() for s in segs)
        res[p] = txt
        print('ASR', p, '|', txt[:300], flush=True)
except Exception as e:
    res['_error'] = repr(e)
    print('ASR FAIL', repr(e), flush=True)

with open('reels_classified.json', 'w') as f:
    json.dump({'transcripts': res, 'downloaded': list(have.keys())}, f, ensure_ascii=False, indent=1)

gh = os.environ.get('GITHUB_TOKEN', '')
if gh:
    body = base64.b64encode(open('reels_classified.json', 'rb').read()).decode()
    requests_headers = {'Authorization': f'Bearer {gh}', 'Accept': 'application/vnd.github+json'}
    import requests
    requests.put('https://api.github.com/repos/litvinenko0100-a11y/vkusmorey-bots/contents/reels_classified.json',
                 headers=requests_headers,
                 json={'message': 'chore: reel classification (audio transcripts + frame sheets)',
                       'content': body, 'branch': 'main'}, timeout=60)
print('DONE')
