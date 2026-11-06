# Боты «Вкус Морей»

Постоянный хостинг: DigitalOcean (Ubuntu) + systemd, автоперезапуск.

## Состав
| Файл | Назначение |
|---|---|
| `bot_excursions.py` | Telegram @vkusmorey_bot — прогулки, программа, цены, заявки |
| `bot_products.py` | Telegram @Kkrraabb51_bot — морепродукты, прайс, счета |
| `bot_vk.py` | VK-бот vk.com/club211184771 — публикации по расписанию |
| `prices.json` | Прайс морепродуктов |
| `vk_posts.json` | Тексты постов для VK |
| `setup.sh` | Установка + systemd-юниты |
| `*.service` | Юниты с `Restart=always` |

## Переменные окружения
- `BOT_DIR` — рабочая папка (по умолчанию `/opt/vkusmorey`)
- `EXCURSIONS_TOKEN` — токен Telegram-бота прогулок
- `PRODUCTS_TOKEN` — токен Telegram-бота морепродуктов

## Деплой
```bash
apt-get install -y python3 python3-pip
mkdir -p /opt/vkusmorey && cd /opt/vkusmorey
# скопировать файлы сюда
pip3 install -r requirements.txt
bash setup.sh
systemctl status vkusmorey-excursions
```

## Важно
- `vk_token.txt` нужно заполнить токеном сообщества VK, иначе публикации в стену не идут.
- `prices.json` заполнить реальными ценами — иначе бот морепродуктов отвечает «уточняем наличие».
