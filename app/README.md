# Flix Market — веб-додаток (Next.js + React)

Міні-додаток для Telegram. Профіль користувача та каталог з’єднані з спільною БД; користувач визначається за **Telegram ID** з init data.

## Структура

- **app/** — App Router (layout, сторінки)
- **app/api/** — API: перевірка init data, профіль, каталог
- **lib/** — валідація Telegram init data, робота з БД (better-sqlite3)
- **types/** — типи User, Product, Telegram

## Запуск

```bash
cp .env.example .env.local
# Заповнити BOT_TOKEN у .env.local

npm install
npm run dev
```

Відкривати через Telegram Web App (посилання з бота), щоб у заголовках була init data.

## Змінні оточення

- `BOT_TOKEN` — токен бота для перевірки підпису init data
- `DATABASE_PATH` — опційно, шлях до `database/data.db`
- **Посилання на бота** (для «Поділитися» та реферального посилання):
  - `NEXT_PUBLIC_BOT_LINK` — повне посилання, напр. `https://t.me/FlixMarketBot` (доступне в браузері)
  - або `BOT_LINK_FOR_REDIRECT` — те саме, тільки на сервері
  - або **`BOT_USERNAME`** — лише юзернейм бота, напр. `FlixMarketBot` (без @); посилання збереться як `https://t.me/FlixMarketBot`
- **Сайт і webhook Monobank:**
  - **`SITE_URL`** — повне посилання на сайт (веб-додаток), напр. `https://your-app.ngrok-free.dev` або `https://yourdomain.com` (без слеша в кінці). Використовується для webhook після оплати Mono: на цю адресу Monobank надсилає POST на `/api/mono/webhook` при зміні статусу рахунку. Якщо не вказано — webhook не передається при створенні інвойсу.

БД спільна з ботом: `../database/data.db`.
