import os

import requests, json, time
TOK=os.environ.get('EXCURSIONS_TOKEN','7795659732:AAFjnsBxLndGWUllspEp-TcFmZ6_k9hKVT4')
API=f'https://api.telegram.org/bot{TOK}'
ADMIN=1486595631
MENU={"inline_keyboard":[
 [{"text":"🚤 Забронировать прогулку","callback_data":"book"}],
 [{"text":"📋 Программа и что входит","callback_data":"prog"}],
 [{"text":"💰 Цены","callback_data":"price"}],
 [{"text":"🐟 Морепродукты","url":"https://t.me/murmansk_moreprodukt"}],
 [{"text":"💬 Написать напрямую","url":"https://t.me/Vkus_morey51"}]]}

def api(m,**kw):
    for _ in range(5):
        try: return requests.post(f'{API}/{m}', data=kw, timeout=30).json()
        except Exception: time.sleep(2)
    return {'ok':False}

def send(chat_id,text,kb=None):
    d={'chat_id':chat_id,'text':text}
    if kb: d['reply_markup']=json.dumps(kb)
    return api('sendMessage',**d)

PROGRAM="""🚤 Программа прогулки в Териберке

Что входит:
• выход в Баренцево море на катере
• базальтовые скалы и бухты
• крабовое сафари
• рыбалка (снасти выдаём)
• дегустация на борту: морской еж, гребешок, устрицы, краб
• чай с термоса

📍 Териберка, Мурманская область
Группы по 6–10 человек. Выход по предоплате."""

PRICE="""💰 Прогулка с дегустацией

⏱ 2 часа
💰 15 000 ₽/час — 30 000 ₽ за 2 часа (за пароход)
👥 Группа до 10 человек
🎁 Бонус новым гостям — дегустация морского ежа и гребешка

Забронировать: @Vkus_morey51"""

def handle_cb(d,cid):
    if d=='book':
        send(cid,"📩 Забронировать прогулку\n\nНапишите сюда дату и количество человек — например: «5 ноября, 2 взрослых и ребёнок». Заявка уйдёт Андрею, он подтвердит место и пришлёт оплату.",MENU)
    elif d=='prog': send(cid,PROGRAM,MENU)
    elif d=='price': send(cid,PRICE,MENU)

def handle(u):
    if 'callback_query' in u:
        cq=u['callback_query']; cid=cq['message']['chat']['id']
        api('answerCallbackQuery', callback_query_id=cq['id'])
        handle_cb(cq.get('data'),cid); return
    m=u.get('message')
    if not m: return
    ch=m['chat']; cid=ch['id']; txt=(m.get('text') or '').strip()
    if txt.startswith('/start') or txt.startswith('/menu'):
        send(cid,'👋 Вкус Морей · Прогулки в Териберке\n\nМорские прогулки по Баренцевому морю: базальтовые скалы, крабовое сафари, рыбалка, дегустация морепродуктов на борту и киты.\n\nВыберите, что вас интересует:',MENU)
    elif txt.startswith('/booking'): handle_cb('book',cid)
    elif txt.startswith('/program'): handle_cb('prog',cid)
    elif txt.startswith('/prices'): handle_cb('price',cid)
    elif txt.startswith('/help'):
        send(cid,'❓ Помощь\n\nЧто взять: тёплое, нескользящая обувь, термос, чехол для телефона.\nЧай и кофе на борту свои.\n\nОплата и бронирование — по кнопке ниже или напрямую @Vkus_morey51',MENU)
    elif txt and not txt.startswith('/'):
        api('sendMessage', chat_id=ADMIN, text=f"📩 Заявка на прогулку\n\nОт: {ch.get('first_name','')} (@{ch.get('username','—')})\nТекст: {txt}")
        send(cid,'✅ Заявка отправлена. Андрей подтвердит дату и пришлёт оплату — обычно в течение 15 минут.',MENU)

def main():
    off=None
    while True:
        pr={'timeout':25,'limit':50}
        if off: pr['offset']=off
        try: r=requests.get(f'{API}/getUpdates',params=pr,timeout=40).json()
        except Exception:
            time.sleep(3); continue
        if not r.get('ok'):
            time.sleep(5); continue
        for u in r.get('result',[]):
            off=u['update_id']+1
            try: handle(u)
            except Exception as ex: print('ERR',ex,flush=True)
main()
