"""Серіалізація каталогу бота у формат сайту."""
from __future__ import annotations

import os
import re

from ulits.admin_functions import strip_html_for_button
from ulits.path_utils import resolve_media_path
from ulits.payment_create import parse_tariffs

_ICON_MAP = (
    ("netflix", "netflix", "#E50914"),
    ("chatgpt", "openai", "#10A37F"),
    ("openai", "openai", "#10A37F"),
    ("grok", "x", "#111111"),
    ("claude", "anthropic", "#D4A27F"),
    ("spotify", "spotify", "#1DB954"),
    ("youtube", "youtube", "#FF0000"),
    ("disney", "disneyplus", "#113CCF"),
    ("hbo", "hbo", "#000000"),
    ("sweet", "youtube", "#E31E24"),
    ("vpn", "protonvpn", "#6D4AFF"),
    ("ipvanish", "protonvpn", "#6D4AFF"),
    ("filmix", "imdb", "#F5C518"),
    ("iptv", "youtube", "#FF0000"),
    ("apple", "apple", "#111111"),
    ("adobe", "adobe", "#FF0000"),
    ("gemini", "google", "#4285F4"),
)


def clean_text(value) -> str:
    if not value:
        return ""
    text = strip_html_for_button(str(value))
    text = re.sub(r"[\U0001F300-\U0001FAFF]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_description(value) -> str:
    if not value:
        return ""
    text = strip_html_for_button(str(value))
    text = re.sub(r"[\U0001F300-\U0001FAFF]", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    out: list[str] = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty and out:
                out.append("")
            prev_empty = True
        else:
            out.append(line)
            prev_empty = False
    return "\n".join(out).strip()


def slug_for(product: dict) -> str:
    name = clean_text(product.get("product_name") or "product")
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    if not ascii_name:
        ascii_name = "item"
    return f"{ascii_name}-{product['id']}"


def icon_for(product: dict) -> tuple[str, str]:
    hay = f"{product.get('product_type') or ''} {product.get('product_name') or ''}".lower()
    for needle, icon, color in _ICON_MAP:
        if needle in hay:
            return icon, color
    return "", "#2B5CF6"


def uah_to_kop(amount: float) -> int:
    return int(round(float(amount) * 100))


def is_recurring(product: dict) -> bool:
    return (product.get("payment_type") or "") == "subscription"


def media_version(stored_path: str | None) -> int | None:
    """Мітка версії фото — змінюється при заміні файлу в боті."""
    if not stored_path:
        return None
    path = resolve_media_path(stored_path)
    if path and os.path.isfile(path):
        return int(os.path.getmtime(path))
    return None


def serialize_product(product: dict, public_api_url: str = "") -> dict:
    tariffs = parse_tariffs(product.get("product_price"))
    by_months = {m: uah_to_kop(p) for m, p in tariffs}
    recurring = is_recurring(product)
    monthly = by_months.get(1, 0)
    if not monthly and tariffs:
        months, price = min(tariffs, key=lambda t: t[1] / max(t[0], 1))
        monthly = uah_to_kop(price / months)

    icon, color = icon_for(product)
    name = clean_text(product.get("product_name"))
    description = clean_description(product.get("product_description"))
    photo = product.get("product_photo") or ""
    photo_version = media_version(photo) if photo else None
    photo_url = None
    if photo:
        base = (public_api_url or "").rstrip("/")
        photo_url = f"{base}/api/v1/media/product/{product['id']}" if base else f"/api/v1/media/product/{product['id']}"
    badge = (product.get("product_badge") or "").strip()

    plans = [
        {
            "months": m,
            "total": uah_to_kop(p),
            "perMonth": uah_to_kop(p / m) if m else 0,
            "label": "щомісяця" if recurring and m == 1 else f"{m} міс",
            "off": 0,
        }
        for m, p in tariffs
    ]
    if monthly:
        for plan in plans:
            full = monthly * plan["months"]
            if full > 0:
                plan["off"] = max(0, round((1 - plan["total"] / full) * 100))

    return {
        "id": str(product["id"]),
        "botId": product["id"],
        "slug": slug_for(product),
        "name": name,
        "icon": icon,
        "color": color,
        "description": description,
        "features": "",
        "recurring": recurring,
        "price": monthly,
        "price3": by_months.get(3, 0),
        "price6": by_months.get(6, 0),
        "price12": by_months.get(12, 0),
        "faq": "",
        "deliveryNote": "Після оплати менеджер надішле доступ у Telegram або на пошту.",
        "visible": True,
        "autoIssue": False,
        "categoryId": str(product.get("catalog_id") or ""),
        "categoryName": clean_text(product.get("product_type") or "Інше"),
        "photoUrl": photo_url,
        "photoVersion": photo_version,
        "badge": badge or None,
        "tariff": str(product.get("product_price") or ""),
        "paymentType": "subscription" if recurring else "one_time",
        "plans": plans,
    }


def serialize_category(catalog_id, name, count: int, image_path=None, public_api_url: str = "") -> dict:
    icon, color = icon_for({"product_type": name, "product_name": name})
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", clean_text(name)).strip("-").lower() or f"cat-{catalog_id}"
    photo_version = media_version(image_path) if image_path else None
    photo_url = None
    if image_path:
        base = (public_api_url or "").rstrip("/")
        photo_url = f"{base}/api/v1/media/category/{catalog_id}" if base else f"/api/v1/media/category/{catalog_id}"
    return {
        "id": str(catalog_id),
        "slug": f"{slug}-{catalog_id}",
        "name": clean_text(name),
        "icon": icon,
        "color": color,
        "sortOrder": catalog_id or 0,
        "active": True,
        "count": count,
        "photoUrl": photo_url,
        "photoVersion": photo_version,
    }
