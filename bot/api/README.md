# Публічне API FlixMarketBot

Сайт ходить сюди. Усі підписки, оплати й автосписання виконуються в боті.

Запускається разом з ботом на `API_HOST:API_PORT` (за замовчуванням `0.0.0.0:8088`).

## Авторизація

Усі маршрути, крім health / media / webhooks, потребують ключ:

```
X-API-Key: <API_KEY з .env>
```

Або:

```
Authorization: Bearer <API_KEY>
```

`SITE_URL` — мініапка (кнопка в боті, CORS, каталог). Той самий ключ можна слати з неї.

## Маршрути

| Метод | Шлях | Опис |
|---|---|---|
| GET | `/api/v1/health` | живий сервіс |
| GET | `/api/v1/catalog` | категорії + товари |
| GET | `/api/v1/products/{id\|slug}` | один товар |
| GET | `/api/v1/media/product/{id}` | фото товару |
| GET | `/api/v1/media/category/{id}` | фото категорії |
| POST | `/api/v1/users` | створити / знайти користувача (`email` або `telegram_id`) |
| GET | `/api/v1/users/{user_id}` | профіль |
| POST | `/api/v1/users/link` | привʼязати сайт-акаунт до Telegram і перенести підписки |
| GET | `/api/v1/users/{user_id}/subscriptions` | разові + recurring |
| GET | `/api/v1/users/{user_id}/payments` | платежі |
| POST | `/api/v1/users/{user_id}/recurring/{sub_id}/cancel` | вимкнути автосписання |
| POST | `/api/v1/payments` | створити інвойс Monobank (`user_id`, `product_id`, `months`, `source`, `redirect_url`) |
| GET | `/api/v1/payments/{invoice_id}` | статус платежу |
| POST | `/api/v1/webhooks/mono` | вебхук Monobank (без ключа) |
| GET | `/api/v1/admin/stats` | статистика |
| GET | `/api/v1/admin/users` | клієнти |
| GET | `/api/v1/admin/payments` | платежі |
| GET | `/api/v1/admin/products` | товари |

## .env

```
API_KEY=
API_HOST=0.0.0.0
API_PORT=8088
PUBLIC_API_URL=https://api.your-domain.com
SITE_URL=https://market.easyplayy.com
```

`PUBLIC_API_URL` потрібен, щоб Monobank слав вебхук. Якщо порожній — бот як і раніше перевіряє pending-платежі кроном кожні 30 секунд.
