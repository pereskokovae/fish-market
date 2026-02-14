 # Fish Market Telegram Bot (Strapi + Redis)

Телеграм-бот магазина: показывает товары из Strapi, открывает карточку товара с фото, добавляет/удаляет товары из корзины, запрашивает email для оформления заказа.  
Данные хранятся в Strapi CMS, состояние диалога — в Redis.

---

## Требования
- Python 3.10+ 
- Redis
- Strapi (локально)
- Node.js + npm (для Strapi)

---

## Установка проекта
1) Клонировать репозиторий
```bash
git clone 
cd fish-market
```
2) Виртуальное окружение и зависимости
```bash 
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```
```bash 
pip install -r requirements.txt
```

## Переменные окружения
Создайте .env в корне проекта:
```bash 
TG_TOKEN=your_telegram_bot_token

STRAPI_URL=http://localhost:1337
STRAPI_TOKEN=your_strapi_api_token

DATABASE_HOST=localhost
DATABASE_PORT=6379
DATABASE_PASSWORD=
```

### Где получить STRAPI_TOKEN
 1. Откройте Strapi Admin: http://localhost:1337/admin
 2. Settings → API Tokens
 3. Create new API Token
 4. Скопируйте токен и вставь в .env как STRAPI_TOKEN=...

## Запуск

1. Redis
Убедитесь, что Redis запущен:
```bash
sudo service redis-server start
```

2. Strapi
В папке проекта Strapi:
```bash
npm run develop
```

3. Telegram bot
В корне проекта бота:
```bash
python tg_bot.py
```

Проверка, что всё работает
 1. Открой бота в Telegram → /start
 2. Должно быть:
 - список товаров (кнопки)
 - карточка товара (текст + фото, если есть)
 - кнопка “Добавить в корзину” добавляет товар в Strapi cart
 - “Моя корзина” показывает позиции и итог
 - “Оплатить” просит email и сохраняет в clients
Структура проекта (пример)
.
├── tg_bot.py
├── store_api.py
├── redis_storage.py
├── create_keyboards.py
├── requirements.txt
├── .env
└── README.md
