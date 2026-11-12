import os

import requests, json, time
TOK = os.environ.get('PRODUCTS_TOKEN', '')
API=f'https://api.telegram.org/bot{TOK}'
ADMIN=1486595631
PRICES=os.path.join(os.environ.get('BOT_DIR','/opt/vkusmorey'),'prices.json')
MENU_BTN={"inline_keyboard":[
 [{"text":"🐟 Свежая рыба","callback_data":"buy_fish"}],
 [{"text":"🦑 Кальмар","callback_data":"buy_squid"}],
 [{"text":"🦀 Краб, гребешок","callback_data":"buy_crab"}],
 [{"text":"🐟 Сёмга, форель, икра","callback_data":"buy_salmon"}],
 [{"text":"📋 Весь прайс","callback_data":"prices"}],
 [{"text":"📦 Доставка и оплата","callback_data":"help"}],
 [{"text":"💬 Написать","url":"https://t.me/Vkus_morey51"}]]}

def api(m,**kw):
    for _ in range(5):
        try: return requests.post(f'{API}/{m}', data=kw, timeout=30).json()
        except Exception: time.sleep(2)
    return {'ok':False}

def load():
    try: return json.load(open(PRICES))
    except Exception: return {}

def send(chat_id,text,kb=None):
    d={'chat_id':chat_id,'text':text}
    if kb: d['reply_markup']=json.dumps(kb)
    return api('sendMessage',**d)

CAT={'buy_fish':'Рыба','buy_squid':'Кальмар','buy_crab':'Краб и гребешок','buy_salmon':'Сёмга, форель, икра'}
KEY={'buy_fish':'fish','buy_squid':'squid','buy_crab':'crab','buy_salmon':'salmon'}

def handle_cb(d,cid):
    p=load()
    if d in CAT:
        price=p.get(KEY[d])
        if not price:
            # уведомляем администратора: кто и что спрашивает
            api('sendMessage', chat_id=ADMIN,
                text=f"🛒 Запрос цены: {CAT[d]}\nПокупатель: {cid}\n\nБот не знает цену — уточни и впиши в prices.json.")
            send(cid,f"📋 {CAT[d]}: уточняем наличие и цену на сегодня. Напишите нам — вышлем актуальный прайс и забронируем.",
                 {"inline_keyboard":[[{"text":"Написать","url":"https://t.me/Vkus_morey51"}]]})
            return
        api('sendInvoice', chat_id=cid, title=p.get(KEY[d]+'_label',CAT[d]+', 1 кг'),
            description='Оплата: '+p.get(KEY[d]+'_label',CAT[d])+'. Вес и свежесть подтвердим перед отправкой.',
            payload=json.dumps({'item':KEY[d]}), currency='XTR',
            prices=json.dumps([{'label':p.get(KEY[d]+'_label',CAT[d]),'amount':price}]),
            need_name=False, need_phone_number=False, need_shipping_address=False, need_email=False)
    elif d=='prices':
        lines=p.get('lines')
        txt=('📋 Актуальный прайс\n\n'+'\n'.join(lines)) if lines else '📋 Прайс обновляется. Напишите нам — вышлем актуальные цены и наличие.'
        send(cid,txt,{"inline_keyboard":[[{"text":"🔄 Обновить","callback_data":"prices"}]]})
    elif d=='help':
        send(cid,'📦 Доставка и оплата\n\nОплата прямо здесь, в Telegram. Доставка по Мурманску и самовывоз — по договорённости.\n\nАссортимент: треска, палтус, камбала, скумбрия, корюшка, мойва, сельдь, кальмар командорский (в т.ч. очищ), гребешок, краб камчатский, сёмга, форель, икра, печень трески.\n\nКаждая партия — с датой вылова.',MENU_BTN)

def handle(u):
    if 'callback_query' in u:
        cq=u['callback_query']; cid=cq['message']['chat']['id']
        api('answerCallbackQuery', callback_query_id=cq['id'])
        handle_cb(cq.get('data'),cid); return
    m=u.get('message')
    if not m: return
    ch=m['chat']; cid=ch['id']; txt=(m.get('text') or '').strip()
    if txt.startswith('/start') or txt.startswith('/menu'):
        send(cid,'👋 Вкус Морей · Морепродукты\n\nСвежий улов с Баренцева моря и северных морей: треска, палтус, камбала, скумбрия, кальмар, гребешок, краб камчатский, сёмга, форель, икра, печень трески.\n\nКаждая партия — с датой вылова. Оплата прямо в Telegram.\n\nВыберите, что вас интересует:',MENU_BTN)
    elif txt.startswith('/prices'): handle_cb('prices',cid)
    elif txt.startswith('/order'): handle_cb('buy_fish',cid)
    elif txt.startswith('/help'): handle_cb('help',cid)
    elif txt and not txt.startswith('/'):
        send(cid,'Спасибо! Ответим в течение 15 минут. А пока — каталог:',MENU_BTN)

DEADLINE = time.time() + 50 * 60  # graceful exit -> job concludes success


def main():
    off=None
    while time.time() < DEADLINE:
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
