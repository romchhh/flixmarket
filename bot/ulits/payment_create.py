"""Створення інвойсів Monobank — спільне для бота і публічного API."""
from __future__ import annotations

from database.admin_db import get_product_payment_type
from database.client_db import (
    conn,
    cursor,
    get_product_full,
    save_payment_info,
)
from ulits.monopay_functions import PaymentManager


def parse_tariffs(price_str) -> list[tuple[int, float]]:
    tariffs: list[tuple[int, float]] = []
    if price_str is None:
        return tariffs
    raw = str(price_str).strip()
    if not raw:
        return tariffs
    parts = [p.strip() for p in raw.split(",")] if "," in raw else [raw]
    for part in parts:
        if "-" not in part:
            part = f"1-{part}"
        months_s, price_s = part.split("-", 1)
        try:
            months = int(months_s.strip())
            price = float(price_s.strip().replace(",", "."))
        except ValueError:
            continue
        tariffs.append((months, price))
    return tariffs


def price_for_months(product: dict, months: int) -> float | None:
    for m, price in parse_tariffs(product.get("product_price")):
        if m == months:
            return price
    return None


def create_invoice_for_user(
    user_id: int,
    product_id: int,
    months: int,
    source: str = "bot",
    redirect_url: str | None = None,
) -> dict:
    product = get_product_full(product_id)
    if not product:
        raise ValueError("Продукт не знайдено")

    amount = price_for_months(product, months)
    if amount is None:
        raise ValueError("Такого строку немає")

    payment_type = get_product_payment_type(product_id) or product.get("payment_type") or "one"
    is_subscription = payment_type == "subscription"
    manager = PaymentManager()
    name = product["product_name"] or "Підписка"

    if is_subscription:
        local_payment_id, invoice_id, payment_url, wallet_id = manager.create_payment_with_tokenization(
            user_id=user_id,
            product_name=name,
            months=months,
            price=amount,
            redirect_url=redirect_url,
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO payments_temp_data (invoice_id, wallet_id, payment_type, local_payment_id)
            VALUES (?, ?, ?, ?)
            """,
            (invoice_id, wallet_id, "subscription", local_payment_id),
        )
        conn.commit()
        stored_type = "subscription"
    else:
        local_payment_id, invoice_id, payment_url = manager.create_payment(
            user_id=user_id,
            product_name=name,
            months=months,
            price=amount,
            redirect_url=redirect_url,
        )
        stored_type = "one_time"

    save_payment_info(
        payment_id=local_payment_id,
        invoice_id=invoice_id,
        user_id=user_id,
        product_id=product_id,
        months=months,
        amount=amount,
        status="pending",
        payment_type=stored_type,
        source=source,
    )
    return {
        "payment_id": local_payment_id,
        "invoice_id": invoice_id,
        "page_url": payment_url,
        "amount": amount,
        "months": months,
        "product_id": product_id,
        "payment_type": stored_type,
        "source": source,
    }


def record_invoice_for_user(
    user_id: int,
    product_id: int,
    months: int,
    amount: float,
    invoice_id: str,
    payment_id: str,
    payment_type: str = "one_time",
    wallet_id: str | None = None,
    source: str = "site",
) -> dict:
    """Сайт уже створив рахунок Monobank — лише записати його в БД бота."""
    stored_type = "subscription" if payment_type in ("subscription", "recurring") else "one_time"
    if stored_type == "subscription" and wallet_id:
        cursor.execute(
            """
            INSERT OR REPLACE INTO payments_temp_data (invoice_id, wallet_id, payment_type, local_payment_id)
            VALUES (?, ?, ?, ?)
            """,
            (invoice_id, wallet_id, stored_type, payment_id),
        )
        conn.commit()
    ok = save_payment_info(
        payment_id=payment_id,
        invoice_id=invoice_id,
        user_id=user_id,
        product_id=product_id,
        months=months,
        amount=amount,
        status="pending",
        payment_type=stored_type,
        source=source,
    )
    if not ok:
        raise ValueError("Не вдалось записати платіж")
    return {
        "ok": True,
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "amount": amount,
        "months": months,
        "product_id": product_id,
        "payment_type": stored_type,
        "source": source,
        "wallet_id": wallet_id,
    }
