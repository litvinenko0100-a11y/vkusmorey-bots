
import requests, json, time, os, random
import os
D=os.environ.get('BOT_DIR','/opt/vkusmorey')
GROUP='211184771'
def get_token():
    try: return open(D+'/vk_token.txt').read().strip()
    except Exception: return ''

POSTS=json.load(open(D+'/vk_posts.json'))
STATE=D+'/vk_state.json'
ADMIN_VK='https://vk.com/club211184771'

def api(method, **kw):
    tok=get_token()
    if not tok: return {'error':{'error_msg':'no token'}}
    kw['access_token']=tok; kw['v']='5.199'
    for _ in range(4):
        try:
            r=requests.post('https://api.vk.com/method/'+method, data=kw, timeout=45).json()
            if 'error' in r:
                err=r['error']
                if err.get('error_code') in (5,6): time.sleep(3); continue
            return r
        except Exception:
            time.sleep(3)
    return {'error':{'error_msg':'timeout'}}
    for _ in range(4):
        try:
            r=requests.post('https://api.vk.com/method/'+method, data=kw, timeout=45).json()
            if 'error' in r:
                err=r['error']
                if err.get('error_code') in (6,): time.sleep(2); continue
                if err.get('error_code') in (5,): time.sleep(3); continue
            return r
        except Exception as e:
            time.sleep(3)
    return {'error':{'error_msg':'timeout'}}

def load_state():
    try: return json.load(open(STATE))
    except Exception: return {'posted':{}, 'last_day':None}

def save_state(s): json.dump(s, open(STATE,'w'), ensure_ascii=False, indent=1)

def get_state():
    r=api('groups.getById', group_ids=GROUP, fields='members_count,status,description,site,activity')
    g=(r.get('response') or {}).get('groups',[{}])[0]
    return g

def upload_photo(path):
    # upload to VK upload server, then save
    tok=get_token()
    if not tok: return None, {'error':'no token'}
    r=requests.post('https://api.vk.com/method/photos.getMessagesUploadServer', data={'access_token':tok,'v':'5.199','group_id':GROUP}, timeout=40).json()
    srv=r.get('response')
    if not srv: return None, r
    fields={'photo':'', 'server':srv['server'], 'v':srv['v'], 'group_id':GROUP}
    with open(path,'rb') as f:
        rr=requests.post(srv['upload_url'], data=fields, files={'photo':('photo.jpg', f, 'image/jpeg')}, timeout=90).json()
    p=rr.get('response')
    if not p: return None, rr
    p['group_id']=GROUP
    s=api('photos.save', **p)
    return (s.get('response') or {}).get('photo'), s

def post_to_wall(text, photos=None):
    kw={'owner_id':'-'+GROUP, 'message':text, 'publish_date':0}
    if photos: kw['attachments']=json.dumps(photos)
    r=api('wall.post', **kw)
    return r

def publish(text, photo_path=None):
    att=[]
    if photo_path and os.path.exists(photo_path):
        pid,s=upload_photo(photo_path)
        if pid: att=[pid]
        else: print('PHOTO FAIL', str(s)[:200], flush=True)
    kw={'owner_id':'-'+GROUP, 'message':text}
    if att: kw['attachments']=json.dumps(att)
    r=api('wall.post', **kw)
    if 'error' in r:
        # retry without photo
        r=api('wall.post', owner_id='-'+GROUP, message=text)
    print('POST', 'ok' if 'response' in r else str(r)[:300], flush=True)
    return r

def pick_photo(kind):
    cands={'seafood':['cards/seafood.jpg'],
           'fish':['media/18107193491364688.jpg'],
           'trip':['media/18086750699329787.jpg','media/18112256774461138.jpg']}[kind]
    for c in cands:
        p=os.path.join(D,c)
        if os.path.exists(p): return p
    return None

def reply_comment(cid, text, owner=None):
    kw={'comment_id':cid, 'message':text}
    if owner: kw['owner_id']=owner
    return api('wall.reply', **kw)

def handle_comments():
    r=api('wall.get', owner_id='-'+GROUP, count=20, filter='new', fields='comments')
    if 'error' in r: return
    items=(r.get('response') or {}).get('items',[])
    for it in items:
        for cm in (it.get('comments') or {}).get('items',[]) or []:
            cid=cm.get('id'); txt=(cm.get('text') or '').lower()
            if cm.get('replies') is not None and cm.get('processed'): continue
            if not cid: continue
            if any(k in txt for k in ['цена','сколько','стоимо','прайс','цена?','₽','руб']):
                reply_comment(cid, '💰 Прогулка — 15 000 ₽/час, 2 часа = 30 000 ₽ за пароход, группа до 10 человек. Бонус новым гостям — дегустация морского ежа и гребешка.\n\nЗабронировать и оплатить: @vkusmorey_bot', cm.get('owner_id'))
            elif any(k in txt for k in ['забронир','бронь','записа','заявк','пойти','хочу','свободн','дата','когда']):
                reply_comment(cid, '✅ Заявка принята! Напишите, пожалуйста, в личку @Vkus_morey51 дату и количество человек — подтвердим место и пришлём оплату. Или сразу в бот: @vkusmorey_bot', cm.get('owner_id'))
            elif any(k in txt for k in ['морепродукт','креветк','краб','рыба','заказать','заказ','доставк','наличие','гребеш','устриц','кальмар']):
                reply_comment(cid, '🐟 Свежие морепродукты с Баренцева моря — доставка и самовывоз по Мурманску, оплата прямо в Telegram.\n\nЗаказать и оплатить: @Kkrraabb51_bot\nЦены и наличие: @Kosha_Markova', cm.get('owner_id'))
            elif any(k in txt for k in ['тебер','терибер','северн','сиян','снаряд','сафари','лодк','катер','кот','маршрут','погод','костюм','спасат','внутр','кают','комфорт','далеко','идти ли','холодно']):
                reply_comment(cid, '🌊 Териберка — это Баренцево море, Мурманская область. Прогулка на катере 2 часа к базальтовым скалам, с рыбалкой и дегустацией на борту.\n\nЧто взять: тёплое, нескользящая обувь, термос, чехол для телефона. Чай и кофе на борту свои.\n\nВсе детали и бронирование: @vkusmorey_bot', cm.get('owner_id'))
            else:
                reply_comment(cid, 'Спасибо за вопрос! Напишите, пожалуйста, в личку @Vkus_morey51 — ответим подробно. Прогулка: @vkusmorey_bot, морепродукты: @Kkrraabb51_bot', cm.get('owner_id'))
            time.sleep(0.7)

def do_schedule():
    st=load_state()
    today=time.strftime('%a').lower()  # mon,tue...
    wdmap={'mon':'mon','tue':'tue','wed':'wed','thu':'thu','fri':'fri','sat':'sat','sun':'sun'}
    wd=wdmap.get(today,'sun')
    lst=POSTS.get('vkusmorey51',[])
    entry=None
    for e in lst:
        if e['wd']==wd: entry=e; break
    if not entry: return
    key=str(time.strftime('%Y-%m-%d'))
    if st.get('posted',{}).get(wd)==key: return
    kind = 'seafood' if wd in ('tue','thu','sat') else 'trip'
    photo = pick_photo(kind)
    publish(entry['text'], photo)
    st.setdefault('posted',{})[wd]=key
    save_state(st)

def main():
    print('VK BOT START', flush=True)
    last=None
    while True:
        try:
            g=get_state()
            if g and g.get('members_count') is not None:
                st=load_state()
                st['members']=g.get('members_count'); save_state(st)
            if get_token():
                now=time.strftime('%H:%M')
                if now=='10:00' and last!=now:
                    do_schedule(); last=now
                handle_comments()
        except Exception as ex:
            print('ERR', str(ex)[:200], flush=True)
        time.sleep(45)
main()
