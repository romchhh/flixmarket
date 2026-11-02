"""Створення інвойсів Monobank — спільне для бота і публічного API."""
from __future__ import annotations

from database.admin_db import get_product_payment_type
from database.client_db import (
    add_subscription,
    conn,
    cursor,
    get_product_full,
    get_product_type,
    save_payment_info,
)
from database.promo_db import (
    apply_promo_to_price,
    get_promo_by_id,
    mark_promo_used,
    validate_promo_code,
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


def resolve_recurring_price(
    *,
    paid_amount: float,
    product_id: int,
    months: int,
    invoice_id: str | None = None,
) -> float:
    """Ціна наступних списань: повний тариф. Промо діє лише на перший платіж."""
    if invoice_id:
        from database.client_db import get_payment_promo

        promo = get_payment_promo(invoice_id)
        saved = promo.get("promo_amount_saved") if promo else None
        if saved is not None and float(saved) > 0:
            return round(float(paid_amount) + float(saved), 2)

    product = get_product_full(product_id)
    if product:
        catalog = price_for_months(product, int(months))
        if catalog is not None:
            return float(catalog)
    return float(paid_amount)


def resolve_promo_pricing(*, base_price: float, months: int, promo_code: str | None) -> dict:
    """Повертає amount, months, promo fields після застосування коду."""
    if not promo_code:
        return {
            "amount": float(base_price),
            "months": int(months),
            "promo_code_id": None,
            "promo_code": None,
            "promo_amount_saved": None,
            "promo": None,
            "is_free": False,
        }
    validated = validate_promo_code(promo_code)
    if not validated.get("ok"):
        raise ValueError(validated.get("message") or "Невірний промокод")
    promo = validated["promo"]
    pricing = apply_promo_to_price(base_price=base_price, promo=promo, months=months)
    final_months = int(pricing["months"])
    # для free — беремо ціну відповідного тарифу як «економію», якщо є
    amount_saved = float(pricing["amountSaved"])
    return {
        "amount": float(pricing["priceAfterPromo"]),
        "months": final_months,
        "promo_code_id": int(promo["id"]),
        "promo_code": promo["code"],
        "promo_amount_saved": amount_saved,
        "promo": promo,
        "is_free": promo.get("type") == "free" or float(pricing["priceAfterPromo"]) <= 0,
    }


def _fulfill_free_payment(
    *,
    user_id: int,
    product: dict,
    months: int,
    source: str,
    promo_code_id: int,
    promo_code: str,
    promo_amount_saved: float,
) -> dict:
    from datetime import datetime, timedelta

    payment_id = f"promo_{user_id}_{int(datetime.now().timestamp())}"
    invoice_id = payment_id
    product_id = int(product["id"])
    name = product["product_name"] or "Підписка"
    marked = mark_promo_used(
        promo_id=promo_code_id,
        user_id=user_id,
        payment_id=payment_id,
        amount_saved=promo_amount_saved,
        months_granted=months,
    )
    if not marked:
        raise ValueError("Промокод уже використаний")

    save_payment_info(
        payment_id=payment_id,
        invoice_id=invoice_id,
        user_id=user_id,
        product_id=product_id,
        months=months,
        amount=0,
        status="success",
        payment_type="one_time",
        source=source,
        promo_code_id=promo_code_id,
        promo_code=promo_code,
        promo_amount_saved=promo_amount_saved,
    )

    start_date = datetime.now()
    end_date = start_date + timedelta(days=30 * months)
    product_type = get_product_type(product_id) or ""
    add_subscription(
        user_id=user_id,
        product_type=product_type,
        product_id=product_id,
        product_name=name,
        price=0,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        status="active",
        source=source,
    )
    return {
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "page_url": None,
        "amount": 0,
        "months": months,
        "product_id": product_id,
        "payment_type": "one_time",
        "source": source,
        "promo_code": promo_code,
        "promo_amount_saved": promo_amount_saved,
        "paid": True,
        "free": True,
    }


def create_invoice_for_user(
    user_id: int,
    product_id: int,
    months: int,
    source: str = "bot",
    redirect_url: str | None = None,
    promo_code: str | None = None,
) -> dict:
    product = get_product_full(product_id)
    if not product:
        raise ValueError("Продукт не знайдено")

    tariffs = parse_tariffs(product.get("product_price"))
    amount = price_for_months(product, months)

    # free-промо може дати 6/12 міс., навіть якщо такого тарифу немає в прайсі
    if promo_code:
        early = validate_promo_code(promo_code)
        if early.get("ok") and early["promo"].get("type") == "free":
            free_m = int(early["promo"].get("freeMonths") or months)
            base_for_free = price_for_months(product, free_m)
            if base_for_free is None and tariffs:
                # оцінка економії: той самий «місяць×ціна» або перший тариф
                per = min((p / m for m, p in tariffs if m > 0), default=tariffs[0][1])
                base_for_free = round(per * free_m, 2)
            if base_for_free is None:
                base_for_free = float(amount or 0)
            return _fulfill_free_payment(
                user_id=user_id,
                product=product,
                months=free_m,
                source=source,
                promo_code_id=int(early["promo"]["id"]),
                promo_code=early["promo"]["code"],
                promo_amount_saved=float(base_for_free),
            )

    if amount is None:
        raise ValueError("Такого строку немає")

    pricing = resolve_promo_pricing(base_price=amount, months=months, promo_code=promo_code)
    final_amount = pricing["amount"]
    final_months = pricing["months"]

    if pricing["is_free"]:
        return _fulfill_free_payment(
            user_id=user_id,
            product=product,
            months=final_months,
            source=source,
            promo_code_id=pricing["promo_code_id"],
            promo_code=pricing["promo_code"],
            promo_amount_saved=pricing["promo_amount_saved"] or float(amount),
        )

    payment_type = get_product_payment_type(product_id) or product.get("payment_type") or "one"
    is_subscription = payment_type == "subscription"
    manager = PaymentManager()
    name = product["product_name"] or "Підписка"

    if is_subscription:
        local_payment_id, invoice_id, payment_url, wallet_id = manager.create_payment_with_tokenization(
            user_id=user_id,
            product_name=name,
            months=final_months,
            price=final_amount,
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
            months=final_months,
            price=final_amount,
            redirect_url=redirect_url,
        )
        stored_type = "one_time"

    save_payment_info(
        payment_id=local_payment_id,
        invoice_id=invoice_id,
        user_id=user_id,
        product_id=product_id,
        months=final_months,
        amount=final_amount,
        status="pending",
        payment_type=stored_type,
        source=source,
        promo_code_id=pricing["promo_code_id"],
        promo_code=pricing["promo_code"],
        promo_amount_saved=pricing["promo_amount_saved"],
    )
    return {
        "payment_id": local_payment_id,
        "invoice_id": invoice_id,
        "page_url": payment_url,
        "amount": final_amount,
        "months": final_months,
        "product_id": product_id,
        "payment_type": stored_type,
        "source": source,
        "promo_code": pricing["promo_code"],
        "promo_amount_saved": pricing["promo_amount_saved"],
        "paid": False,
        "free": False,
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
    promo_code: str | None = None,
    promo_code_id: int | None = None,
    promo_amount_saved: float | None = None,
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

    # якщо сайт передав промокод — валідуємо і тримаємо на платежі до оплати
    if promo_code and not promo_code_id:
        pricing = resolve_promo_pricing(base_price=amount, months=months, promo_code=promo_code)
        # amount уже має бути зі знижкою з сайту; лише привʼязуємо id
        promo_code_id = pricing["promo_code_id"]
        promo_code = pricing["promo_code"]
        if promo_amount_saved is None:
            promo_amount_saved = pricing["promo_amount_saved"]

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
        promo_code_id=promo_code_id,
        promo_code=promo_code,
        promo_amount_saved=promo_amount_saved,
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
        "promo_code": promo_code,
        "promo_code_id": promo_code_id,
        "promo_amount_saved": promo_amount_saved,
    }


def mark_payment_promo_used(invoice_id: str) -> None:
    from database.client_db import get_payment_promo

    info = get_payment_promo(invoice_id)
    if not info:
        return
    promo = get_promo_by_id(int(info["promo_code_id"]))
    if not promo or promo.get("used_at"):
        return
    mark_promo_used(
        promo_id=int(info["promo_code_id"]),
        user_id=int(info["user_id"]),
        payment_id=info.get("payment_id") or invoice_id,
        amount_saved=float(info.get("promo_amount_saved") or 0),
        months_granted=int(info.get("months") or 0),
    )
