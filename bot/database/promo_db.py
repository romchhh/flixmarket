import secrets
import string
from datetime import datetime

import pytz

from database.client_db import conn, cursor

KYIV = pytz.timezone("Europe/Kyiv")


def now_kyiv() -> datetime:
    return datetime.now(KYIV).replace(tzinfo=None)


def create_table_promo_codes():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL UNIQUE COLLATE NOCASE,
            promo_type TEXT NOT NULL,
            discount_percent REAL,
            free_months INTEGER,
            expires_at TEXT,
            is_active INTEGER DEFAULT 1,
            used_by NUMERIC,
            used_at TEXT,
            payment_id TEXT,
            amount_saved REAL,
            months_granted INTEGER,
            created_at TEXT,
            created_by NUMERIC,
            product_id INTEGER,
            max_uses INTEGER DEFAULT 1,
            use_count INTEGER DEFAULT 0
        )
        """
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_promo_codes_code ON promo_codes(code COLLATE NOCASE)"
    )
    conn.commit()
    migrate_promo_codes_columns()


def migrate_promo_codes_columns():
    cursor.execute("PRAGMA table_info(promo_codes)")
    cols = {row[1] for row in cursor.fetchall()}
    if "product_id" not in cols:
        cursor.execute("ALTER TABLE promo_codes ADD COLUMN product_id INTEGER")
    if "max_uses" not in cols:
        cursor.execute("ALTER TABLE promo_codes ADD COLUMN max_uses INTEGER DEFAULT 1")
    if "use_count" not in cols:
        cursor.execute("ALTER TABLE promo_codes ADD COLUMN use_count INTEGER DEFAULT 0")
    cursor.execute("UPDATE promo_codes SET max_uses = 1 WHERE max_uses IS NULL")
    cursor.execute(
        """
        UPDATE promo_codes
        SET use_count = 1
        WHERE used_at IS NOT NULL
          AND (use_count IS NULL OR use_count = 0)
        """
    )
    cursor.execute("UPDATE promo_codes SET use_count = 0 WHERE use_count IS NULL")
    conn.commit()


def migrate_payments_promo_columns():
    cursor.execute("PRAGMA table_info(payments)")
    cols = {row[1] for row in cursor.fetchall()}
    if "promo_code_id" not in cols:
        cursor.execute("ALTER TABLE payments ADD COLUMN promo_code_id INTEGER")
    if "promo_amount_saved" not in cols:
        cursor.execute("ALTER TABLE payments ADD COLUMN promo_amount_saved REAL")
    if "promo_code" not in cols:
        cursor.execute("ALTER TABLE payments ADD COLUMN promo_code TEXT")
    conn.commit()


def _normalize_code(code: str) -> str:
    return (code or "").strip().upper()


def generate_promo_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    while True:
        raw = "".join(secrets.choice(alphabet) for _ in range(length))
        code = f"FLIX-{raw[:4]}-{raw[4:]}"
        cursor.execute("SELECT 1 FROM promo_codes WHERE code = ? COLLATE NOCASE", (code,))
        if cursor.fetchone() is None:
            return code


def create_promo_code(
    *,
    promo_type: str,
    discount_percent: float | None = None,
    free_months: int | None = None,
    expires_at: str | None = None,
    code: str | None = None,
    created_by: int | None = None,
    product_id: int | None = None,
    max_uses: int = 1,
) -> dict:
    if promo_type not in ("percent", "free"):
        raise ValueError("Invalid promo_type")
    if promo_type == "percent":
        if discount_percent is None or not (1 <= float(discount_percent) <= 100):
            raise ValueError("discount_percent must be 1..100")
        free_months = None
        product_id = None
        if max_uses is None:
            max_uses = 1
        max_uses = int(max_uses)
        # 0 = без ліміту, інакше ≥ 1
        if max_uses < 0:
            raise ValueError("max_uses must be >= 0")
    else:
        if free_months not in (1, 3, 6, 12):
            raise ValueError("free_months must be 1/3/6/12")
        if not product_id:
            raise ValueError("Для безкоштовного доступу оберіть товар")
        discount_percent = None
        max_uses = 1

    final_code = _normalize_code(code) if code else generate_promo_code()
    if not final_code:
        raise ValueError("Empty code")

    created_at = now_kyiv().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        cursor.execute(
            """
            INSERT INTO promo_codes (
                code, promo_type, discount_percent, free_months, expires_at,
                is_active, created_at, created_by, product_id, max_uses, use_count
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, 0)
            """,
            (
                final_code,
                promo_type,
                discount_percent,
                free_months,
                expires_at,
                created_at,
                created_by,
                int(product_id) if product_id is not None else None,
                int(max_uses),
            ),
        )
        conn.commit()
    except Exception as exc:
        raise ValueError("Promo code already exists") from exc

    return get_promo_by_id(cursor.lastrowid)


def _row_to_dict(row) -> dict:
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def get_promo_by_id(promo_id: int) -> dict | None:
    cursor.execute("SELECT * FROM promo_codes WHERE id = ?", (promo_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return _row_to_dict(row)


def get_promo_by_code(code: str) -> dict | None:
    cursor.execute(
        "SELECT * FROM promo_codes WHERE code = ? COLLATE NOCASE",
        (_normalize_code(code),),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return _row_to_dict(row)


def get_all_promos(limit: int = 50) -> list[dict]:
    cursor.execute(
        """
        SELECT * FROM promo_codes
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [_row_to_dict(row) for row in cursor.fetchall()]


def delete_promo(promo_id: int) -> None:
    promo = get_promo_by_id(promo_id)
    if not promo:
        return
    if promo_status(promo) == "used":
        raise ValueError("Не можна видалити вичерпаний промокод")
    cursor.execute("DELETE FROM promo_codes WHERE id = ?", (promo_id,))
    conn.commit()


def is_promo_expired(promo: dict, now: datetime | None = None) -> bool:
    expires_at = promo.get("expires_at")
    if not expires_at:
        return False
    current = now or now_kyiv()
    try:
        if len(expires_at) == 10:
            end = datetime.strptime(expires_at, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            end = datetime.fromisoformat(expires_at.replace("Z", ""))
    except ValueError:
        return True
    return current > end


def _max_uses(promo: dict) -> int:
    value = promo.get("max_uses")
    if value is None:
        return 1
    return int(value)


def _use_count(promo: dict) -> int:
    return int(promo.get("use_count") or 0)


def remaining_uses(promo: dict) -> int | None:
    """None = без ліміту."""
    max_uses = _max_uses(promo)
    if max_uses <= 0:
        return None
    return max(0, max_uses - _use_count(promo))


def promo_status(promo: dict) -> str:
    if not promo.get("is_active"):
        return "inactive"
    if is_promo_expired(promo):
        return "expired"
    rem = remaining_uses(promo)
    if rem is not None and rem <= 0:
        return "used"
    # legacy single-use без use_count
    if _max_uses(promo) == 1 and promo.get("used_at") and _use_count(promo) == 0:
        return "used"
    return "available"


def _pending_holds(promo_id: int) -> int:
    cursor.execute(
        """
        SELECT COUNT(*) FROM payments
        WHERE promo_code_id = ?
          AND lower(COALESCE(status, '')) IN ('created', 'pending')
        """,
        (promo_id,),
    )
    row = cursor.fetchone()
    return int(row[0] if row else 0)


def _user_already_used(promo_id: int, user_id: int) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM payments
        WHERE promo_code_id = ?
          AND user_id = ?
          AND lower(COALESCE(status, '')) = 'success'
        LIMIT 1
        """,
        (promo_id, user_id),
    )
    return cursor.fetchone() is not None


def validate_promo_code(
    code: str,
    *,
    product_id: int | None = None,
    user_id: int | None = None,
) -> dict:
    """Повертає {ok, promo?} або {ok:False, error, message}."""
    promo = get_promo_by_code(code)
    if not promo:
        return {"ok": False, "error": "not_found", "message": "Невірний промокод"}
    status = promo_status(promo)
    if status == "inactive":
        return {"ok": False, "error": "inactive", "message": "Промокод вимкнено"}
    if status == "used":
        return {"ok": False, "error": "used", "message": "Промокод уже використаний"}
    if status == "expired":
        return {"ok": False, "error": "expired", "message": "Термін дії промокоду закінчився"}

    bound_product = promo.get("product_id")
    if promo.get("promo_type") == "free":
        if not bound_product:
            return {
                "ok": False,
                "error": "misconfigured",
                "message": "Промокод без привʼязки до товару — створіть новий",
            }
        if product_id is None:
            return {
                "ok": False,
                "error": "product_required",
                "message": "Оберіть товар для цього промокоду",
            }
        if int(product_id) != int(bound_product):
            return {
                "ok": False,
                "error": "wrong_product",
                "message": "Цей промокод лише для іншого товару",
            }

    rem = remaining_uses(promo)
    holds = _pending_holds(int(promo["id"]))
    if rem is not None and holds >= rem:
        return {"ok": False, "error": "used", "message": "Промокод уже використаний"}

    if user_id is not None and _max_uses(promo) != 1:
        if _user_already_used(int(promo["id"]), int(user_id)):
            return {
                "ok": False,
                "error": "used_by_you",
                "message": "Ви вже використали цей промокод",
            }

    return {
        "ok": True,
        "promo": {
            "id": promo["id"],
            "code": promo["code"],
            "type": promo["promo_type"],
            "discountPercent": promo.get("discount_percent"),
            "freeMonths": promo.get("free_months"),
            "productId": promo.get("product_id"),
            "maxUses": _max_uses(promo),
            "useCount": _use_count(promo),
        },
    }


def apply_promo_to_price(*, base_price: float, promo: dict, months: int) -> dict:
    """promo: raw DB row or validate payload with type/discountPercent/freeMonths."""
    ptype = promo.get("promo_type") or promo.get("type")
    if ptype == "free":
        free_months = int(promo.get("free_months") or promo.get("freeMonths") or months)
        return {
            "priceAfterPromo": 0.0,
            "amountSaved": float(base_price),
            "months": free_months,
        }
    pct = float(promo.get("discount_percent") or promo.get("discountPercent") or 0)
    pct = max(0.0, min(100.0, pct))
    after = round(float(base_price) * (1 - pct / 100.0), 2)
    return {
        "priceAfterPromo": after,
        "amountSaved": round(float(base_price) - after, 2),
        "months": int(months),
    }


def mark_promo_used(
    *,
    promo_id: int,
    user_id: int,
    payment_id: str | int | None,
    amount_saved: float,
    months_granted: int,
) -> bool:
    promo = get_promo_by_id(promo_id)
    if not promo or not promo.get("is_active"):
        return False

    used_at = now_kyiv().strftime("%Y-%m-%dT%H:%M:%S")
    max_uses = _max_uses(promo)
    params = (
        user_id,
        used_at,
        str(payment_id) if payment_id is not None else None,
        amount_saved,
        months_granted,
        promo_id,
    )

    if max_uses <= 0:
        cursor.execute(
            """
            UPDATE promo_codes
            SET use_count = COALESCE(use_count, 0) + 1,
                used_by = ?,
                used_at = ?,
                payment_id = ?,
                amount_saved = ?,
                months_granted = ?
            WHERE id = ?
              AND is_active = 1
            """,
            params,
        )
    elif max_uses == 1:
        cursor.execute(
            """
            UPDATE promo_codes
            SET use_count = 1,
                used_by = ?,
                used_at = ?,
                payment_id = ?,
                amount_saved = ?,
                months_granted = ?
            WHERE id = ?
              AND is_active = 1
              AND used_at IS NULL
              AND COALESCE(use_count, 0) = 0
            """,
            params,
        )
    else:
        cursor.execute(
            """
            UPDATE promo_codes
            SET use_count = COALESCE(use_count, 0) + 1,
                used_by = ?,
                used_at = ?,
                payment_id = ?,
                amount_saved = ?,
                months_granted = ?
            WHERE id = ?
              AND is_active = 1
              AND COALESCE(use_count, 0) < ?
            """,
            (*params, max_uses),
        )
    conn.commit()
    return cursor.rowcount > 0


def get_promo_stats_text(promo: dict) -> str:
    status = promo_status(promo)
    status_labels = {
        "available": "✅ Доступний",
        "used": "🔒 Використаний",
        "expired": "⏰ Прострочений",
        "inactive": "❌ Вимкнений",
    }
    if promo["promo_type"] == "percent":
        benefit = f"Знижка {float(promo['discount_percent'] or 0):.0f}%"
    else:
        benefit = f"Безкоштовно {promo['free_months']} міс."

    max_uses = _max_uses(promo)
    use_count = _use_count(promo)
    if max_uses <= 0:
        uses_line = f"Без ліміту (використано {use_count})"
    elif max_uses == 1:
        uses_line = "Одноразовий"
    else:
        uses_line = f"{use_count}/{max_uses}"

    product_line = "будь-який"
    if promo.get("product_id"):
        try:
            from database.client_db import get_product_full

            product = get_product_full(int(promo["product_id"]))
            product_line = (
                f"{product.get('product_name')} (#{promo['product_id']})"
                if product
                else f"#{promo['product_id']}"
            )
        except Exception:
            product_line = f"#{promo['product_id']}"

    expires = promo.get("expires_at") or "безстроковий"
    lines = [
        f"<b>🎟 Промокод:</b> <code>{promo['code']}</code>",
        f"<b>Тип:</b> {benefit}",
        f"<b>Товар:</b> {product_line}",
        f"<b>Використання:</b> {uses_line}",
        f"<b>Термін дії:</b> {expires}",
        f"<b>Статус:</b> {status_labels.get(status, status)}",
        f"<b>Створено:</b> {promo.get('created_at') or '—'}",
    ]
    if use_count > 0:
        lines.extend(
            [
                "",
                "<b>📊 Остання активація:</b>",
                f"• Хто: <code>{promo.get('used_by')}</code>",
                f"• Коли: {promo.get('used_at')}",
                f"• Період: {promo.get('months_granted') or '—'} міс.",
                f"• Економія: {float(promo.get('amount_saved') or 0):.2f} грн",
            ]
        )
    return "\n".join(lines)
