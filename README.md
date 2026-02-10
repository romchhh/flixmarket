# Flix Market Bot

Телеграм-бот та веб-додаток з спільною базою даних.

## Структура проєкту

```
FlixMarketBot/
├── bot/                 # Телеграм-бот (Python, aiogram)
│   ├── config.py        # Токен, DB_PATH (корінь/database/data.db)
│   ├── main.py
│   ├── database/        # Модулі роботи з БД (admin_db, client_db)
│   ├── handlers/
│   ├── keyboards/
│   ├── Content/
│   ├── data/            # Локальні дані бота (без data.db — БД у корені)
│   └── ulits/
├── app/                 # Веб-додаток (Next.js + React)
│   ├── app/             # Сторінки та API
│   ├── lib/             # Telegram init data, доступ до БД
│   ├── types/
│   └── package.json
└── database/            # Спільна база даних
    └── data.db          # SQLite (користувачі, підписки, каталог)
```

- **Користувач** у веб-додатку визначається за **Telegram ID** з init data (перевірка підпису через BOT_TOKEN).
- **Дані** (профіль, підписки, каталог) — одна БД для бота та апки.

## Спільний .env

У корені проєкту один файл для бота та апки:

```bash
cp .env.example .env
# Заповни BOT_TOKEN та інші змінні в .env
```

Обидва сервіси читають з `FlixMarketBot/.env` (бот — через python-dotenv, апка — через dotenv у next.config).

## Запуск бота

```bash
cd bot
pip install -r requirements.txt
python main.py
```

## Запуск апки

```bash
cd app
npm install
npm run dev
```

Апка підхоплює змінні з кореневого `.env` автоматично.

## База даних

Файл `database/data.db` — спільний для `bot` та `app`. Шлях за замовчуванням — `database/data.db` у корені; опційно задається в `.env` як `DATABASE_PATH`.
