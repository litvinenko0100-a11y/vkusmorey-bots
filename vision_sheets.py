import os, json, base64, requests

REPO = 'litvinenko0100-a11y/vkusmorey-bots'
GH = os.environ.get('GITHUB_TOKEN', '')
HEADERS = {'Authorization': f'Bearer {GH}', 'Accept': 'application/vnd.github+json'}
IDS = ['Dft8_zaxaeh', 'DfsSvXER3zo', 'DfpQTqIovvG', 'Df2tXDuIh4X', 'Df2ssCyIpqd',
       'Df2sOQYoYHW', 'Df0Dnj0RQcZ', 'Dfxvor8xYXi', 'DfxcubsRhHZ', 'DfvDT0oxpQ7',
       'Dfp81qoRN3F', 'DfutcjmRsVt']

os.makedirs('vis', exist_ok=True)
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration

proc = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-base')
model = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-base')
model.eval()

out = {}
for pid in IDS:
    path = f'vis/{pid}.jpg'
    if not os.path.exists(path):
        r = requests.get(f'https://raw.githubusercontent.com/{REPO}/main/sheets/{pid}.jpg', timeout=120)
        if r.status_code != 200:
            print('miss', pid, r.status_code, flush=True)
            continue
        open(path, 'wb').write(r.content)
    try:
        im = Image.open(path).convert('RGB')
        im.thumbnail((768, 768))
        caps = []
        for prompt in ['', 'a reel about', 'sea', 'crab', 'boat', 'aquarium']:
            inputs = proc(images=im, text=prompt if prompt else None, return_tensors='pt')
            with torch.no_grad():
                gen = model.generate(**inputs, max_new_tokens=30, num_beams=3)
            caps.append(proc.decode(gen[0], skip_special_tokens=True))
        out[pid] = {'size': list(im.size), 'captions': caps}
        print(pid, caps, flush=True)
    except Exception as e:
        print('ERR', pid, repr(e)[:200], flush=True)

with open('vis_captions.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
body = base64.b64encode(open('vis_captions.json', 'rb').read()).decode()
requests.put(f'https://api.github.com/repos/{REPO}/contents/vis_captions.json', headers=HEADERS,
             json={'message': 'chore: vision captions for reels', 'content': body, 'branch': 'main'}, timeout=90)
print('DONE', len(out))
