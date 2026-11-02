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
            created_by NUMERIC
        )
        """
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_promo_codes_code ON promo_codes(code COLLATE NOCASE)"
    )
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
) -> dict:
    if promo_type not in ("percent", "free"):
        raise ValueError("Invalid promo_type")
    if promo_type == "percent":
        if discount_percent is None or not (1 <= float(discount_percent) <= 100):
            raise ValueError("discount_percent must be 1..100")
        free_months = None
    else:
        if free_months not in (1, 3, 6, 12):
            raise ValueError("free_months must be 1/3/6/12")
        discount_percent = None

    final_code = _normalize_code(code) if code else generate_promo_code()
    if not final_code:
        raise ValueError("Empty code")

    created_at = now_kyiv().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        cursor.execute(
            """
            INSERT INTO promo_codes (
                code, promo_type, discount_percent, free_months, expires_at,
                is_active, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                final_code,
                promo_type,
                discount_percent,
                free_months,
                expires_at,
                created_at,
                created_by,
            ),
        )
        conn.commit()
    except Exception as exc:
        raise ValueError("Promo code already exists") from exc

    return get_promo_by_id(cursor.lastrowid)


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
    cursor.execute("DELETE FROM promo_codes WHERE id = ? AND used_at IS NULL", (promo_id,))
    conn.commit()


def _columns() -> list[str]:
    return [
        "id",
        "code",
        "promo_type",
        "discount_percent",
        "free_months",
        "expires_at",
        "is_active",
        "used_by",
        "used_at",
        "payment_id",
        "amount_saved",
        "months_granted",
        "created_at",
        "created_by",
    ]


def _row_to_dict(row) -> dict:
    return dict(zip(_columns(), row))


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


def promo_status(promo: dict) -> str:
    if not promo.get("is_active"):
        return "inactive"
    if promo.get("used_at") or promo.get("used_by"):
        return "used"
    if is_promo_expired(promo):
        return "expired"
    return "available"


def validate_promo_code(code: str) -> dict:
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
    # pending lock: another created/pending payment holding this promo
    cursor.execute(
        """
        SELECT 1 FROM payments
        WHERE promo_code_id = ?
          AND lower(COALESCE(status, '')) IN ('created', 'pending')
        LIMIT 1
        """,
        (promo["id"],),
    )
    if cursor.fetchone():
        return {"ok": False, "error": "used", "message": "Промокод уже використаний"}
    return {
        "ok": True,
        "promo": {
            "id": promo["id"],
            "code": promo["code"],
            "type": promo["promo_type"],
            "discountPercent": promo.get("discount_percent"),
            "freeMonths": promo.get("free_months"),
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
    used_at = now_kyiv().strftime("%Y-%m-%dT%H:%M:%S")
    cursor.execute(
        """
        UPDATE promo_codes
        SET used_by = ?,
            used_at = ?,
            payment_id = ?,
            amount_saved = ?,
            months_granted = ?
        WHERE id = ?
          AND is_active = 1
          AND used_at IS NULL
        """,
        (user_id, used_at, str(payment_id) if payment_id is not None else None, amount_saved, months_granted, promo_id),
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

    expires = promo.get("expires_at") or "безстроковий"
    lines = [
        f"<b>🎟 Промокод:</b> <code>{promo['code']}</code>",
        f"<b>Тип:</b> {benefit}",
        f"<b>Термін дії:</b> {expires}",
        f"<b>Статус:</b> {status_labels.get(status, status)}",
        f"<b>Створено:</b> {promo.get('created_at') or '—'}",
    ]
    if status == "used":
        lines.extend(
            [
                "",
                "<b>📊 Активація:</b>",
                f"• Хто: <code>{promo.get('used_by')}</code>",
                f"• Коли: {promo.get('used_at')}",
                f"• Період: {promo.get('months_granted') or '—'} міс.",
                f"• Економія: {float(promo.get('amount_saved') or 0):.2f} грн",
            ]
        )
    return "\n".join(lines)
