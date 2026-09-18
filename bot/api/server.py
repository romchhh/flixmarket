"""Публічне HTTP API бота. Сайт — лише точка входу, усі списання тут."""
from __future__ import annotations

import hmac
import json
import logging
import os
from datetime import datetime, timedelta

from aiohttp import web

from config import API_HOST, API_KEY, API_PORT, BOT_DIR, BOT_USERNAME, PUBLIC_API_URL, SITE_URL, WEB_SITE_URL
from database.admin_db import get_admin_subscriptions_stats, get_all_categories, get_category_image
from database.client_db import (
    add_user,
    check_user,
    create_site_user,
    create_web_login_token,
    deactivate_subscription,
    get_all_products,
    get_full_payment,
    get_product_full,
    get_product_types_full,
    get_recurring_subscription,
    get_user_payments,
    get_user_recurring_subscriptions,
    get_user_row,
    get_user_subscriptions,
    get_web_login,
    list_recent_payments,
    list_users,
    merge_site_user_to_telegram,
    set_user_email,
)
from ulits.payment_create import create_invoice_for_user, record_invoice_for_user
from ulits.path_utils import resolve_media_path

from .catalog import serialize_category, serialize_product, slug_for

log = logging.getLogger(__name__)

ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://flix-market.com",
    "https://www.flix-market.com",
    "https://market.easyplayy.com",
}
if SITE_URL:
    ALLOWED_ORIGINS.add(SITE_URL)
if WEB_SITE_URL:
    ALLOWED_ORIGINS.add(WEB_SITE_URL)


def _json(data, status=200):
    return web.json_response(data, status=status, dumps=lambda o: json.dumps(o, ensure_ascii=False, default=str))


def _public_url() -> str:
    return PUBLIC_API_URL or f"http://127.0.0.1:{API_PORT}"


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
        resp = await handler(request)
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS or origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        resp.headers["Vary"] = "Origin"
    return resp


def _request_api_key(request: web.Request) -> str:
    header = (request.headers.get("X-API-Key") or "").strip()
    if header:
        return header
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def _api_key_ok(given: str) -> bool:
    expected = (API_KEY or "").strip()
    if not expected or not given:
        return False
    if len(given) != len(expected):
        hmac.compare_digest(expected, expected)
        return False
    return hmac.compare_digest(given, expected)


@web.middleware
async def api_key_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return await handler(request)
    path = request.path
    open_prefixes = ("/api/v1/health", "/api/v1/webhooks/", "/api/v1/media/")
    if path == "/api/v1/health" or any(path.startswith(p) for p in open_prefixes):
        return await handler(request)
    if not _api_key_ok(_request_api_key(request)):
        return _json({"error": "unauthorized"}, 401)
    return await handler(request)


def _product_by_slug(slug: str) -> dict | None:
    for product in get_all_products():
        if slug_for(product) == slug or str(product["id"]) == slug:
            return product
    return None


def _sub_payload(user_id: int) -> dict:
    one_time = []
    for sub in get_user_subscriptions(user_id):
        product = get_product_full(sub.get("product_id") or 0) if sub.get("product_id") else None
        start = sub.get("start_date") or ""
        end = sub.get("end_date") or ""
        try:
            starts_iso = datetime.strptime(start, "%Y-%m-%d").isoformat() + "Z"
        except ValueError:
            starts_iso = start
        try:
            expires_iso = datetime.strptime(end, "%Y-%m-%d").isoformat() + "Z"
        except ValueError:
            expires_iso = end
        one_time.append({
            "id": f"one-{sub.get('id')}",
            "botId": sub.get("id"),
            "kind": "one_time",
            "productId": str(sub.get("product_id") or ""),
            "name": sub.get("product_name"),
            "price": sub.get("price"),
            "startsAt": starts_iso,
            "expiresAt": expires_iso,
            "status": sub.get("status"),
            "source": sub.get("source") or "bot",
            "slug": slug_for(product) if product else "",
            "icon": serialize_product(product, _public_url())["icon"] if product else "",
            "color": serialize_product(product, _public_url())["color"] if product else "#2B5CF6",
        })

    recurring = []
    for row in get_user_recurring_subscriptions(user_id):
        sub_id, product_name, months, price, next_payment_date, status, payment_failures = row[:7]
        src = row[7] if len(row) > 7 else "bot"
        product = None
        full = get_recurring_subscription(sub_id)
        if full:
            product = get_product_full(full.get("product_id") or 0)
        try:
            nxt = datetime.strptime(next_payment_date, "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            nxt = datetime.now()
        start = nxt - timedelta(days=30 * int(months or 1))
        serialized = serialize_product(product, _public_url()) if product else None
        recurring.append({
            "id": f"rec-{sub_id}",
            "botId": sub_id,
            "kind": "recurring",
            "productId": str(full.get("product_id") if full else ""),
            "name": product_name,
            "price": price,
            "months": months,
            "startsAt": start.isoformat() + "Z",
            "expiresAt": nxt.isoformat() + "Z",
            "nextPaymentAt": nxt.isoformat() + "Z",
            "status": status,
            "paymentFailures": payment_failures,
            "source": (full.get("source") if full else None) or src or "bot",
            "slug": serialized["slug"] if serialized else "",
            "icon": serialized["icon"] if serialized else "",
            "color": serialized["color"] if serialized else "#2B5CF6",
        })
    return {"oneTime": one_time, "recurring": recurring}


async def health(_request):
    return _json({"ok": True, "service": "flixmarket-bot-api"})


async def web_login_create(request):
    origin = ""
    if request.body_exists:
        try:
            body = await request.json()
            origin = (body.get("origin") or "").rstrip("/")
        except Exception:
            origin = ""
    token = create_web_login_token(origin)
    bot = (BOT_USERNAME or "FlixMarketBot").lstrip("@")
    return _json({
        "token": token,
        "botUrl": f"https://t.me/{bot}?start=w0{token}",
        "origin": origin,
    })


async def web_login_get(request):
    token = request.match_info["token"]
    row = get_web_login(token)
    if not row:
        return _json({"error": "not found"}, 404)
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    if row.get("confirmedAt") and row.get("telegramId"):
        return _json({
            "status": "confirmed",
            "telegramId": row["telegramId"],
            "username": row["username"],
        })
    if row.get("expiresAt") and row["expiresAt"] < now:
        return _json({"status": "expired"})
    return _json({"status": "pending"})


async def catalog_list(_request):
    types = get_product_types_full()
    public = _public_url()
    categories = [
        serialize_category(
            item["catalog_id"],
            item["product_type"],
            item["count"],
            item.get("image_path"),
            public,
        )
        for item in types
    ]
    products = [serialize_product(p, public) for p in get_all_products()]
    return _json({"categories": categories, "products": products})


async def product_get(request):
    raw = request.match_info["id"]
    product = None
    if raw.isdigit():
        product = get_product_full(int(raw))
    if not product:
        product = _product_by_slug(raw)
    if not product:
        return _json({"error": "not found"}, 404)
    return _json(serialize_product(product, _public_url()))


def _media_file(stored_path: str | None):
    if not stored_path:
        raise web.HTTPNotFound()
    path = resolve_media_path(stored_path)
    if not path or not os.path.isfile(path):
        raise web.HTTPNotFound()
    content_root = os.path.abspath(os.path.join(BOT_DIR, "Content"))
    if not os.path.abspath(path).startswith(content_root):
        raise web.HTTPForbidden()
    return web.FileResponse(path)


async def media_product(request):
    product_id = int(request.match_info["id"])
    product = get_product_full(product_id)
    if not product:
        raise web.HTTPNotFound()
    return _media_file(product.get("product_photo"))


async def media_category(request):
    catalog_id = int(request.match_info["id"])
    return _media_file(get_category_image(catalog_id))


def _user_payload(user_id: int) -> dict | None:
    row = get_user_row(user_id)
    if not row:
        return None
    return {
        "userId": row["user_id"],
        "username": row["user_name"],
        "email": row.get("email"),
        "source": row.get("source") or "telegram",
        "joinDate": row.get("join_date"),
        "partnerBalance": row.get("partner_balance") or 0,
        "refId": row.get("ref_id"),
    }


async def users_create(request):
    body = await request.json()
    email = (body.get("email") or "").strip().lower() or None
    telegram_id = body.get("telegram_id")
    username = body.get("username")
    ref_id = body.get("ref_id")

    if telegram_id:
        telegram_id = int(telegram_id)
        if not check_user(telegram_id):
            add_user(telegram_id, username, ref_id)
        if email:
            set_user_email(telegram_id, email)
        payload = _user_payload(telegram_id)
        return _json(payload)

    if not email:
        return _json({"error": "email or telegram_id required"}, 400)
    user_id = create_site_user(email, username)
    return _json(_user_payload(user_id))


async def users_get(request):
    user_id = int(request.match_info["user_id"])
    payload = _user_payload(user_id)
    if not payload:
        return _json({"error": "not found"}, 404)
    return _json(payload)


async def users_link(request):
    body = await request.json()
    site_user_id = int(body.get("site_user_id"))
    telegram_id = int(body.get("telegram_id"))
    username = body.get("username")
    email = (body.get("email") or "").strip().lower() or None
    if email:
        set_user_email(site_user_id, email)
    merged = merge_site_user_to_telegram(site_user_id, telegram_id, username)
    if email:
        set_user_email(merged, email)
    subs = _sub_payload(merged)
    imported = len(subs["oneTime"]) + len(subs["recurring"])
    return _json({"user": _user_payload(merged), "imported": imported, **subs})


async def users_subscriptions(request):
    user_id = int(request.match_info["user_id"])
    if not get_user_row(user_id):
        return _json({"error": "not found"}, 404)
    return _json(_sub_payload(user_id))


async def users_payments(request):
    user_id = int(request.match_info["user_id"])
    return _json({"payments": get_user_payments(user_id)})


async def cancel_recurring(request):
    user_id = int(request.match_info["user_id"])
    sub_id = int(request.match_info["sub_id"])
    sub = get_recurring_subscription(sub_id, user_id)
    if not sub:
        return _json({"error": "not found"}, 404)
    if sub["status"] != "active":
        return _json({"ok": True, "status": sub["status"]})
    if not deactivate_subscription(sub_id):
        return _json({"error": "failed"}, 500)
    try:
        from main import bot
        from config import admin_chat_id
        from Content.texts import get_admin_subscription_cancelled_text, get_user_subscription_cancelled_text
        from database.client_db import get_username_by_id
        from keyboards.admin_keyboards import get_write_to_user_keyboard
        await bot.send_message(
            user_id,
            get_user_subscription_cancelled_text(sub["product_name"]),
            parse_mode="HTML",
        )
        if admin_chat_id:
            await bot.send_message(
                admin_chat_id,
                get_admin_subscription_cancelled_text(
                    user_id,
                    get_username_by_id(user_id),
                    sub["product_name"],
                    source=sub.get("source") or "bot",
                    reason="Скасовано користувачем (сайт / API)",
                ),
                parse_mode="HTML",
                reply_markup=get_write_to_user_keyboard(user_id),
            )
    except Exception as e:
        log.warning("cancel notify: %s", e)
    return _json({"ok": True, "status": "inactive"})


async def payments_create(request):
    body = await request.json()
    try:
        user_id = int(body["user_id"])
        product_id = int(body["product_id"])
        months = int(body["months"])
    except (KeyError, TypeError, ValueError):
        return _json({"error": "user_id, product_id, months required"}, 400)

    source = body.get("source") or "site"
    redirect_url = body.get("redirect_url")
    if not redirect_url and SITE_URL and source == "site":
        redirect_url = f"{SITE_URL}/cabinet"

    if not get_user_row(user_id) and not check_user(user_id):
        add_user(user_id, body.get("username"), None)

    try:
        result = create_invoice_for_user(
            user_id=user_id,
            product_id=product_id,
            months=months,
            source=source,
            redirect_url=redirect_url,
        )
    except ValueError as e:
        return _json({"error": str(e)}, 400)
    except Exception as e:
        log.exception("create invoice")
        return _json({"error": f"Не вдалось створити рахунок: {e}"}, 502)
    return _json({"ok": True, **result})


async def payments_record(request):
    body = await request.json()
    try:
        user_id = int(body["user_id"])
        product_id = int(body["product_id"])
        months = int(body["months"])
        amount = float(body["amount"])
        invoice_id = str(body["invoice_id"]).strip()
        payment_id = str(body.get("payment_id") or body["invoice_id"]).strip()
    except (KeyError, TypeError, ValueError):
        return _json({"error": "user_id, product_id, months, amount, invoice_id required"}, 400)
    if not invoice_id:
        return _json({"error": "invoice_id required"}, 400)

    if not get_user_row(user_id) and not check_user(user_id):
        add_user(user_id, body.get("username"), None)

    try:
        result = record_invoice_for_user(
            user_id=user_id,
            product_id=product_id,
            months=months,
            amount=amount,
            invoice_id=invoice_id,
            payment_id=payment_id,
            payment_type=body.get("payment_type") or "one_time",
            wallet_id=(body.get("wallet_id") or None),
            source=body.get("source") or "site",
        )
    except ValueError as e:
        return _json({"error": str(e)}, 400)
    except Exception as e:
        log.exception("record invoice")
        return _json({"error": f"Не вдалось записати платіж: {e}"}, 502)
    return _json(result)


async def payments_get(request):
    invoice_id = request.match_info["invoice_id"]
    info = get_full_payment(invoice_id)
    if not info:
        return _json({"error": "not found"}, 404)
    return _json(info)


async def mono_webhook(request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    invoice_id = data.get("invoiceId") or data.get("invoice_id")
    status = (data.get("status") or "").strip().lower()
    log.info("mono webhook: %s status=%s", invoice_id, status)
    if invoice_id:
        try:
            from database.client_db import save_mono_event
            save_mono_event(str(invoice_id), status, data)
        except Exception:
            log.exception("webhook save event")
    try:
        from ulits.monopay_functions import check_pending_payments
        await check_pending_payments()
    except Exception:
        log.exception("webhook fulfill")
    return _json({"ok": True})


async def admin_stats(_request):
    return _json(get_admin_subscriptions_stats() or {})


async def admin_users(request):
    limit = int(request.query.get("limit", "100"))
    offset = int(request.query.get("offset", "0"))
    return _json({"users": list_users(limit, offset)})


async def admin_payments(_request):
    return _json({"payments": list_recent_payments(100)})


async def admin_categories(_request):
    types = get_product_types_full()
    public = _public_url()
    if types:
        return _json({
            "categories": [
                serialize_category(
                    item["catalog_id"],
                    item["product_type"],
                    item["count"],
                    item.get("image_path"),
                    public,
                )
                for item in types
            ],
        })
    cats = get_all_categories()
    return _json({
        "categories": [serialize_category(cid, name, 0, None, public) for cid, name in cats],
    })


async def admin_products(_request):
    return _json({"products": [serialize_product(p, _public_url()) for p in get_all_products()]})


def build_app() -> web.Application:
    app = web.Application(middlewares=[cors_middleware, api_key_middleware])
    app.router.add_get("/api/v1/health", health)
    app.router.add_get("/api/v1/catalog", catalog_list)
    app.router.add_get("/api/v1/products/{id}", product_get)
    app.router.add_get("/api/v1/media/product/{id}", media_product)
    app.router.add_get("/api/v1/media/category/{id}", media_category)

    app.router.add_post("/api/v1/web-login", web_login_create)
    app.router.add_get("/api/v1/web-login/{token}", web_login_get)

    app.router.add_post("/api/v1/users", users_create)
    app.router.add_get("/api/v1/users/{user_id}", users_get)
    app.router.add_post("/api/v1/users/link", users_link)
    app.router.add_get("/api/v1/users/{user_id}/subscriptions", users_subscriptions)
    app.router.add_get("/api/v1/users/{user_id}/payments", users_payments)
    app.router.add_post("/api/v1/users/{user_id}/recurring/{sub_id}/cancel", cancel_recurring)

    app.router.add_post("/api/v1/payments", payments_create)
    app.router.add_post("/api/v1/payments/record", payments_record)
    app.router.add_get("/api/v1/payments/{invoice_id}", payments_get)
    app.router.add_post("/api/v1/webhooks/mono", mono_webhook)

    app.router.add_get("/api/v1/admin/stats", admin_stats)
    app.router.add_get("/api/v1/admin/users", admin_users)
    app.router.add_get("/api/v1/admin/payments", admin_payments)
    app.router.add_get("/api/v1/admin/categories", admin_categories)
    app.router.add_get("/api/v1/admin/products", admin_products)
    return app


async def start_http_api():
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, API_HOST, API_PORT)
    await site.start()
    log.info("Bot public API listening on %s:%s", API_HOST, API_PORT)
    print(f"🌐 Public API: http://{API_HOST}:{API_PORT}/api/v1/health")
