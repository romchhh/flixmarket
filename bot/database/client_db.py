import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
import pytz

from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id NUMERIC,
            user_name TEXT,
            ref_id NUMERIC,
            join_date TEXT,
            discounts INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    
    
def create_products_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            catalog_id INTEGER,
            product_type TEXT,
            product_name TEXT,
            product_description TEXT,
            product_price NUMERIC,
            product_photo TEXT,
            payment_type TEXT DEFAULT 'one'
        )
    ''')
    conn.commit()


def create_catalog_images_table():
    """Зображення категорій для маркетплейсу (catalog_id -> шлях до файлу)."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalog_images (
            catalog_id INTEGER PRIMARY KEY,
            image_path TEXT NOT NULL
        )
    ''')
    conn.commit()


def migrate_products_table():
    """Додає поле payment_type до існуючої таблиці products"""
    try:
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'payment_type' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN payment_type TEXT DEFAULT 'one'")
            conn.commit()
            print("Поле payment_type успішно додано до таблиці products")
        else:
            print("Поле payment_type вже існує в таблиці products")
        if 'product_badge' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN product_badge TEXT")
            conn.commit()
            print("Поле product_badge успішно додано до таблиці products")
    except sqlite3.Error as e:
        print(f"Помилка при міграції таблиці products: {e}")


def create_contest_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contest (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            invite_id INTEGER,
            invite_date TEXT
        )
    ''')
    conn.commit()
    
    
    




def get_username_by_id(user_id: int) -> str:
    cursor.execute("SELECT user_name FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return (row[0] or str(user_id)) if row else str(user_id)
    
    
def migrate_users_marketing_link():
    cursor.execute("PRAGMA table_info(users)")
    columns = {column[1] for column in cursor.fetchall()}
    if "marketing_link_id" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN marketing_link_id INTEGER")
        conn.commit()


def migrate_users_site_fields():
    """Поля для користувачів із сайту: email і джерело реєстрації."""
    cursor.execute("PRAGMA table_info(users)")
    columns = {column[1] for column in cursor.fetchall()}
    if "email" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
    if "source" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN source TEXT DEFAULT 'telegram'")
        conn.commit()


def migrate_payments_source():
    """Звідки створено платіж: bot | site."""
    cursor.execute("PRAGMA table_info(payments)")
    columns = {column[1] for column in cursor.fetchall()}
    if "source" not in columns:
        cursor.execute("ALTER TABLE payments ADD COLUMN source TEXT DEFAULT 'bot'")
        conn.commit()


def enable_wal():
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Помилка WAL: {e}")


def create_web_logins_table():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS web_logins (
            token TEXT PRIMARY KEY,
            telegram_id INTEGER,
            username TEXT,
            created_at TEXT,
            confirmed_at TEXT,
            expires_at TEXT,
            origin TEXT
        )
        """
    )
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(web_logins)").fetchall()}
    if "origin" not in cols:
        cursor.execute("ALTER TABLE web_logins ADD COLUMN origin TEXT")
    conn.commit()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_web_login_token(origin=None):
    create_web_logins_table()
    token = secrets.token_hex(8)
    now = _utc_now()
    cursor.execute(
        "INSERT INTO web_logins (token, created_at, expires_at, origin) VALUES (?, ?, ?, ?)",
        (
            token,
            now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            (now + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            (origin or "").rstrip("/"),
        ),
    )
    conn.commit()
    return token


def confirm_web_login(token, telegram_id, username, origin=None):
    """Підтвердити вхід. Якщо токена ще немає в цій базі — створюємо (сайт і бот можуть бути на різних машинах)."""
    token = (token or "").strip()
    if not token or len(token) < 8:
        return False
    create_web_logins_table()
    now = _utc_now()
    now_s = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires = (now + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = (username or str(telegram_id)).lstrip("@")
    origin = (origin or "").rstrip("/")
    cursor.execute("SELECT token, origin FROM web_logins WHERE token = ?", (token,))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            """
            UPDATE web_logins
            SET telegram_id = ?, username = ?, confirmed_at = ?, origin = COALESCE(NULLIF(?, ''), origin)
            WHERE token = ?
            """,
            (telegram_id, name, now_s, origin, token),
        )
    else:
        cursor.execute(
            """
            INSERT INTO web_logins (token, telegram_id, username, created_at, confirmed_at, expires_at, origin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (token, telegram_id, name, now_s, now_s, expires, origin),
        )
    conn.commit()
    return True


def get_web_login(token):
    create_web_logins_table()
    cursor.execute(
        "SELECT token, telegram_id, username, confirmed_at, expires_at, origin FROM web_logins WHERE token = ?",
        (token,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "token": row[0],
        "telegramId": row[1],
        "username": row[2],
        "confirmedAt": row[3],
        "expiresAt": row[4],
        "origin": row[5],
    }


def get_marketing_link_id_by_user(user_id: int):
    cursor.execute(
        "SELECT marketing_link_id FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else None


def add_user(user_id, user_name, ref_id, marketing_link_id=None):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    if existing_user is None:
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute('''
                INSERT INTO users (user_id, user_name, ref_id, join_date, marketing_link_id)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, user_name, ref_id, current_date, marketing_link_id))
            conn.commit()
            if marketing_link_id:
                from database.links_db import link_exists, increment_link_registrations
                if link_exists(marketing_link_id):
                    increment_link_registrations(marketing_link_id)
            print(f"User {user_id} added successfully")  # Логування
        except Exception as e:
            print(f"Error inserting user: {e}")  # Вивід помилки

        
def check_user(user_id):
    cursor.execute(f'SELECT * FROM users WHERE user_id = {user_id}')
    user = cursor.fetchone()
    if user:
        return True
    return False

def get_product_types():
    cursor.execute('''
        SELECT catalog_id, product_type, COUNT(*) as count 
        FROM products 
        GROUP BY catalog_id, product_type
        ORDER BY catalog_id
    ''')
    return cursor.fetchall()


def get_product_types_full():
    """Категорії з кількістю товарів і фото з catalog_images (як у мініапці)."""
    try:
        cursor.execute("""
            SELECT p.catalog_id, p.product_type, COUNT(*) as count, c.image_path
            FROM products p
            LEFT JOIN catalog_images c ON p.catalog_id = c.catalog_id
            GROUP BY p.catalog_id, p.product_type
            ORDER BY p.catalog_id
        """)
        return [
            {
                "catalog_id": row[0],
                "product_type": row[1],
                "count": row[2],
                "image_path": row[3],
            }
            for row in cursor.fetchall()
        ]
    except sqlite3.Error as e:
        print(f"Помилка get_product_types_full: {e}")
        return [
            {
                "catalog_id": cid,
                "product_type": name,
                "count": count,
                "image_path": None,
            }
            for cid, name, count in get_product_types()
        ]


def _product_from_row(row, cols=None):
    if cols is None:
        cols = [d[0] for d in cursor.description]
    data = dict(zip(cols, row))
    return {
        "id": data.get("id"),
        "catalog_id": data.get("catalog_id"),
        "product_type": data.get("product_type"),
        "product_name": data.get("product_name"),
        "product_description": data.get("product_description"),
        "product_price": data.get("product_price"),
        "product_photo": data.get("product_photo"),
        "payment_type": data.get("payment_type") or "one",
        "product_badge": data.get("product_badge") or "",
    }

def get_products_by_catalog(catalog_id: int):
    cursor.execute('''
        SELECT id, product_name, product_price
        FROM products 
        WHERE catalog_id = ?
    ''', (catalog_id,))
    return cursor.fetchall()

def get_product_by_id(product_id: int):
    try:
        cursor.execute("""
            SELECT product_name, product_description, product_price, product_photo 
            FROM products 
            WHERE id = ?
        """, (product_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Помилка при отриманні продукту: {e}")
        return None


def get_product_full(product_id: int):
    try:
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _product_from_row(row)
    except sqlite3.Error as e:
        print(f"Помилка get_product_full: {e}")
        return None


def get_all_products():
    try:
        cursor.execute("SELECT * FROM products ORDER BY catalog_id, id")
        cols = [d[0] for d in cursor.description]
        return [_product_from_row(row, cols) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Помилка get_all_products: {e}")
        return []

def create_payments_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT,
            invoice_id TEXT PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            months INTEGER,
            amount REAL,
            status TEXT,
            payment_type TEXT DEFAULT 'one_time',
            created_at DATETIME,
            updated_at DATETIME
        )
    ''')
    conn.commit()

def save_payment_info(payment_id: str, invoice_id: str, user_id: int, product_id: int, months: int, amount: float, status: str, payment_type: str = 'one_time', source: str = 'bot') -> bool:
    try:
        cursor.execute("""
            INSERT INTO payments (
                payment_id, invoice_id, user_id, product_id, months, amount, status, payment_type, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (payment_id, invoice_id, user_id, product_id, months, amount, status, payment_type, source))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при збереженні платежу: {e}")
        return False


def get_full_payment(invoice_id: str):
    try:
        cursor.execute("""
            SELECT payment_id, invoice_id, user_id, product_id, months, amount, status, payment_type, source
            FROM payments
            WHERE invoice_id = ? OR payment_id = ?
        """, (invoice_id, invoice_id))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "payment_id": row[0],
            "invoice_id": row[1],
            "user_id": row[2],
            "product_id": row[3],
            "months": row[4],
            "amount": row[5],
            "status": row[6],
            "payment_type": row[7],
            "source": row[8] if len(row) > 8 else "bot",
        }
    except sqlite3.Error as e:
        print(f"Помилка get_full_payment: {e}")
        return None

def get_payment_info(invoice_id: str) -> tuple:
    try:
        cursor.execute("""
            SELECT user_id, product_id, months 
            FROM payments 
            WHERE invoice_id = ?
        """, (invoice_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Помилка при отриманні інформації про платіж: {e}")
        return None

def update_payment_status(invoice_id: str, status: str) -> bool:
    try:
        cursor.execute("""
            UPDATE payments 
            SET status = ?, updated_at = datetime('now')
            WHERE invoice_id = ?
        """, (status, invoice_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при оновленні статусу платежу: {e}")
        return False

def get_pending_payments(hours: int = 24):
    try:
        cursor.execute("""
            SELECT invoice_id, user_id, product_id, months, amount, payment_type
            FROM payments 
            WHERE status = 'pending' 
            AND created_at >= datetime('now', ?)
        """, (f'-{hours} hours',))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Помилка при отриманні pending платежів: {e}")
        return []

def create_subscriptions_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_type TEXT,
            product_id INTEGER,
            product_name TEXT,
            price REAL,
            start_date TEXT,
            end_date TEXT,
            status TEXT
        )
    ''')
    conn.commit()


def create_user_tokens_table():
    """Таблиця для збереження токенів карток користувачів"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tokens (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            wallet_id TEXT UNIQUE,
            card_token TEXT,
            masked_card TEXT,
            card_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()


def create_recurring_subscriptions_table():
    """Таблиця для управління активними підписками з повторюваними платежами"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recurring_subscriptions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            months INTEGER,
            price REAL,
            wallet_id TEXT,
            next_payment_date TEXT,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            payment_failures INTEGER DEFAULT 0,
            FOREIGN KEY (wallet_id) REFERENCES user_tokens(wallet_id)
        )
    ''')
    conn.commit()


def create_subscription_payments_table():
    """Таблиця для історії платежів по підписках"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_payments (
            id INTEGER PRIMARY KEY,
            subscription_id INTEGER,
            user_id INTEGER,
            amount REAL,
            payment_date TEXT,
            status TEXT,
            invoice_id TEXT,
            payment_id TEXT,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subscription_id) REFERENCES recurring_subscriptions(id)
        )
    ''')
    conn.commit()


def create_payments_temp_data_table():
    """Таблиця для тимчасових даних платежів"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments_temp_data (
            id INTEGER PRIMARY KEY,
            invoice_id TEXT UNIQUE,
            wallet_id TEXT,
            payment_type TEXT,
            local_payment_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    
def add_subscription(user_id: int, product_type: str, product_id: int, product_name: str, 
                    price: float, start_date: str, end_date: str, status: str):
    try:
        cursor.execute("""
            INSERT INTO subscriptions (
                user_id, product_type, product_id, product_name, 
                price, start_date, end_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, product_type, product_id, product_name, price, start_date, end_date, status))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при додаванні підписки: {e}")
        return False
    
    
def get_product_type(product_id: int):
    cursor.execute("SELECT product_type FROM products WHERE id = ?", (product_id,))
    return cursor.fetchone()[0]



def get_active_subscriptions():
    try:
        cursor.execute("""
            SELECT user_id, product_name, end_date
            FROM subscriptions 
            WHERE status = 'active'
        """)
        
        subscriptions = []
        for row in cursor.fetchall():
            subscriptions.append({
                'user_id': row[0],
                'product_name': row[1],
                'end_date': row[2]
            })
        return subscriptions
        
    except sqlite3.Error as e:
        print(f"Помилка при отриманні підписок: {e}")
        return []

def get_user_info(user_id: int) -> dict:
    try:
        cursor.execute("""
            SELECT join_date FROM users 
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                'join_date': result[0]
            }
        return None
        
    except sqlite3.Error as e:
        print(f"Помилка при отриманні інформації користувача: {e}")
        return None

def get_user_by_email(email: str):
    cursor.execute("SELECT user_id, user_name, email, source FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        return None
    return {"user_id": row[0], "user_name": row[1], "email": row[2], "source": row[3]}


def get_user_row(user_id: int):
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cursor.description]
        data = dict(zip(cols, row))
        return {
            "user_id": data.get("user_id"),
            "user_name": data.get("user_name"),
            "ref_id": data.get("ref_id"),
            "join_date": data.get("join_date"),
            "discounts": data.get("discounts"),
            "email": data.get("email"),
            "source": data.get("source") or "telegram",
            "partner_balance": data.get("partner_balance") or 0,
        }
    except sqlite3.Error as e:
        print(f"Помилка get_user_row: {e}")
        return None


def create_site_user(email: str, username: str | None = None) -> int:
    """Створює користувача сайту з від'ємним user_id (не Telegram)."""
    existing = get_user_by_email(email)
    if existing:
        return int(existing["user_id"])
    cursor.execute("SELECT MIN(user_id) FROM users")
    min_id = cursor.fetchone()[0]
    new_id = -1 if min_id is None or min_id > 0 else int(min_id) - 1
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO users (user_id, user_name, ref_id, join_date, email, source)
        VALUES (?, ?, ?, ?, ?, 'site')
        """,
        (new_id, username or email, None, current_date, email),
    )
    conn.commit()
    return new_id


def set_user_email(user_id: int, email: str) -> bool:
    try:
        cursor.execute("UPDATE users SET email = ? WHERE user_id = ?", (email, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка set_user_email: {e}")
        return False


def _reassign_user_id(from_id: int, to_id: int):
    tables = [
        ("subscriptions", "user_id"),
        ("payments", "user_id"),
        ("recurring_subscriptions", "user_id"),
        ("subscription_payments", "user_id"),
        ("contest", "user_id"),
        ("contest", "invite_id"),
        ("partner_earnings", "partner_id"),
        ("partner_earnings", "buyer_id"),
        ("partner_withdrawal_requests", "user_id"),
        ("users", "ref_id"),
    ]
    cursor.execute("DELETE FROM user_tokens WHERE user_id = ?", (from_id,))
    for table, col in tables:
        try:
            cursor.execute(f"UPDATE {table} SET {col} = ? WHERE {col} = ?", (to_id, from_id))
        except sqlite3.Error as e:
            print(f"merge skip {table}.{col}: {e}")


def merge_site_user_to_telegram(site_user_id: int, telegram_id: int, username: str | None = None) -> int:
    """Прив'язує акаунт сайту до Telegram і переносить підписки/платежі."""
    if site_user_id == telegram_id:
        if username:
            cursor.execute("UPDATE users SET user_name = ? WHERE user_id = ?", (username, telegram_id))
            conn.commit()
        return telegram_id

    tg = check_user(telegram_id)
    site = get_user_row(site_user_id)

    if not tg:
        if site:
            _reassign_user_id(site_user_id, telegram_id)
            cursor.execute(
                """
                UPDATE users
                SET user_id = ?, user_name = COALESCE(?, user_name), source = 'telegram'
                WHERE user_id = ?
                """,
                (telegram_id, username, site_user_id),
            )
            conn.commit()
        else:
            add_user(telegram_id, username, None)
        return telegram_id

    if site and site_user_id != telegram_id:
        if site.get("email"):
            set_user_email(telegram_id, site["email"])
        _reassign_user_id(site_user_id, telegram_id)
        cursor.execute("DELETE FROM users WHERE user_id = ?", (site_user_id,))
        if username:
            cursor.execute("UPDATE users SET user_name = ? WHERE user_id = ?", (username, telegram_id))
        conn.commit()
    elif username:
        cursor.execute("UPDATE users SET user_name = ? WHERE user_id = ?", (username, telegram_id))
        conn.commit()
    return telegram_id


def get_user_subscriptions(user_id: int) -> list:
    try:
        cursor.execute("""
            SELECT id, product_name, product_id, price, start_date, end_date, status
            FROM subscriptions 
            WHERE user_id = ?
            ORDER BY end_date DESC
        """, (user_id,))
        
        subscriptions = []
        for row in cursor.fetchall():
            subscriptions.append({
                'id': row[0],
                'product_name': row[1],
                'product_id': row[2],
                'price': row[3],
                'start_date': row[4],
                'end_date': row[5],
                'status': row[6]
            })
        return subscriptions
        
    except sqlite3.Error as e:
        print(f"Помилка при отриманні підписок користувача: {e}")
        return []


def add_discount(user_id: int, discount: int):
    cursor.execute("SELECT discounts FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        cursor.execute("""
            UPDATE users
            SET discounts = discounts + ?
            WHERE user_id = ?
        """, (discount, user_id))
    else:
        cursor.execute("""
            INSERT INTO users (user_id, discounts)
            VALUES (?, ?)
        """, (user_id, discount))
    
    conn.commit()


def get_user_name(user_id: int) -> str:
    cursor.execute("""
        SELECT user_name FROM users WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    return (row[0] or str(user_id)) if row else str(user_id)


def save_user_token(user_id: int, wallet_id: str, card_token: str, masked_card: str, card_type: str) -> bool:
    """Зберігає токен картки користувача"""
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO user_tokens 
            (user_id, wallet_id, card_token, masked_card, card_type, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (user_id, wallet_id, card_token, masked_card, card_type))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при збереженні токена: {e}")
        return False


def get_user_token(user_id: int) -> tuple:
    """Отримує токен картки користувача"""
    try:
        cursor.execute("""
            SELECT wallet_id, card_token, masked_card, card_type 
            FROM user_tokens 
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Помилка при отриманні токена: {e}")
        return None


def create_recurring_subscription(user_id: int, product_id: int, product_name: str, 
                                months: int, price: float, wallet_id: str) -> bool:
    """Створює повторювану підписку"""
    try:
        from datetime import datetime, timedelta
        
        next_payment_date = (datetime.now() + timedelta(days=30 * months)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO recurring_subscriptions 
            (user_id, product_id, product_name, months, price, wallet_id, next_payment_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, product_id, product_name, months, price, wallet_id, next_payment_date))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при створенні підписки: {e}")
        return False


def get_active_recurring_subscriptions() -> list:
    """Отримує всі активні підписки для обробки"""
    try:
        # Київський час з автоматичним урахуванням літнього/зимового часу
        kyiv_tz = pytz.timezone('Europe/Kiev')
        current_time = datetime.now(kyiv_tz)
        date_string = current_time.strftime('%Y-%m-%d %H:%M:00')  # Обрізаємо секунди
        
        cursor.execute("""
            SELECT id, user_id, product_id, product_name, months, price, wallet_id, next_payment_date
            FROM recurring_subscriptions 
            WHERE status = 'active' 
            AND datetime(substr(next_payment_date, 1, 16) || ':00') <= ?
        """, (date_string,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Помилка при отриманні підписок: {e}")
        return []


def update_subscription_next_payment(subscription_id: int, months: int) -> bool:
    """Оновлює дату наступного платежу підписки"""
    try:
        from datetime import datetime, timedelta
        
        next_payment_date = (datetime.now() + timedelta(days=30 * months)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            UPDATE recurring_subscriptions 
            SET next_payment_date = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (next_payment_date, subscription_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при оновленні дати платежу: {e}")
        return False


def increment_payment_failures(subscription_id: int) -> int:
    """Збільшує лічильник невдалих платежів. Повертає нове значення лічильника."""
    try:
        cursor.execute("""
            UPDATE recurring_subscriptions 
            SET payment_failures = payment_failures + 1, updated_at = datetime('now')
            WHERE id = ?
        """, (subscription_id,))
        conn.commit()
        cursor.execute(
            "SELECT payment_failures FROM recurring_subscriptions WHERE id = ?",
            (subscription_id,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error as e:
        print(f"Помилка при оновленні лічильника помилок: {e}")
        return 0


def postpone_subscription_retry(subscription_id: int, days: int = 1) -> bool:
    """Відкладає наступну спробу автосписання на N днів (щоб не спамити картку)."""
    try:
        from datetime import datetime, timedelta

        next_payment_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            UPDATE recurring_subscriptions
            SET next_payment_date = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (next_payment_date, subscription_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при відкладенні спроби платежу: {e}")
        return False


def reset_payment_failures(subscription_id: int) -> bool:
    """Скидає лічильник невдалих платежів після успішної оплати."""
    try:
        cursor.execute("""
            UPDATE recurring_subscriptions
            SET payment_failures = 0, updated_at = datetime('now')
            WHERE id = ?
        """, (subscription_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при скиданні лічильника помилок: {e}")
        return False


def deactivate_subscription(subscription_id: int) -> bool:
    """Деактивує підписку"""
    try:
        cursor.execute("""
            UPDATE recurring_subscriptions 
            SET status = 'inactive', updated_at = datetime('now')
            WHERE id = ?
        """, (subscription_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при деактивації підписки: {e}")
        return False


def save_subscription_payment(subscription_id: int, user_id: int, amount: float, 
                            status: str, invoice_id: str = None, payment_id: str = None, 
                            error_message: str = None) -> bool:
    """Зберігає інформацію про платіж підписки"""
    try:
        cursor.execute("""
            INSERT INTO subscription_payments 
            (subscription_id, user_id, amount, payment_date, status, invoice_id, payment_id, error_message)
            VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?)
        """, (subscription_id, user_id, amount, status, invoice_id, payment_id, error_message))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при збереженні платежу підписки: {e}")
        return False


def get_recurring_subscription(subscription_id: int, user_id: int | None = None):
    try:
        if user_id is None:
            cursor.execute(
                """
                SELECT id, user_id, product_id, product_name, months, price, wallet_id,
                       next_payment_date, status, payment_failures
                FROM recurring_subscriptions WHERE id = ?
                """,
                (subscription_id,),
            )
        else:
            cursor.execute(
                """
                SELECT id, user_id, product_id, product_name, months, price, wallet_id,
                       next_payment_date, status, payment_failures
                FROM recurring_subscriptions WHERE id = ? AND user_id = ?
                """,
                (subscription_id, user_id),
            )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "user_id": row[1],
            "product_id": row[2],
            "product_name": row[3],
            "months": row[4],
            "price": row[5],
            "wallet_id": row[6],
            "next_payment_date": row[7],
            "status": row[8],
            "payment_failures": row[9],
        }
    except sqlite3.Error as e:
        print(f"Помилка get_recurring_subscription: {e}")
        return None


def get_user_payments(user_id: int, limit: int = 50) -> list:
    try:
        cursor.execute(
            """
            SELECT payment_id, invoice_id, product_id, months, amount, status, payment_type, source, created_at
            FROM payments WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        return [
            {
                "payment_id": r[0],
                "invoice_id": r[1],
                "product_id": r[2],
                "months": r[3],
                "amount": r[4],
                "status": r[5],
                "payment_type": r[6],
                "source": r[7],
                "created_at": r[8],
            }
            for r in rows
        ]
    except sqlite3.Error as e:
        print(f"Помилка get_user_payments: {e}")
        return []


def list_recent_payments(limit: int = 100) -> list:
    try:
        cursor.execute(
            """
            SELECT payment_id, invoice_id, user_id, product_id, months, amount, status, payment_type, source, created_at
            FROM payments
            ORDER BY created_at DESC LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            {
                "payment_id": r[0],
                "invoice_id": r[1],
                "user_id": r[2],
                "product_id": r[3],
                "months": r[4],
                "amount": r[5],
                "status": r[6],
                "payment_type": r[7],
                "source": r[8],
                "created_at": r[9],
            }
            for r in rows
        ]
    except sqlite3.Error as e:
        print(f"Помилка list_recent_payments: {e}")
        return []


def list_users(limit: int = 100, offset: int = 0) -> list:
    try:
        cursor.execute(
            """
            SELECT user_id, user_name, email, source, join_date, partner_balance
            FROM users
            ORDER BY join_date DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        rows = cursor.fetchall()
        return [
            {
                "user_id": r[0],
                "user_name": r[1],
                "email": r[2],
                "source": r[3],
                "join_date": r[4],
                "partner_balance": r[5],
            }
            for r in rows
        ]
    except sqlite3.Error as e:
        print(f"Помилка list_users: {e}")
        return []


def get_user_recurring_subscriptions(user_id: int) -> list:
    """Отримує всі підписки користувача"""
    try:
        cursor.execute("""
            SELECT id, product_name, months, price, next_payment_date, status, payment_failures
            FROM recurring_subscriptions 
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Помилка при отриманні підписок користувача: {e}")
        return []

def migrate_payments_temp_data_table():
    """Додає поле local_payment_id до таблиці payments_temp_data"""
    try:
        cursor.execute("PRAGMA table_info(payments_temp_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'local_payment_id' not in columns:
            cursor.execute("ALTER TABLE payments_temp_data ADD COLUMN local_payment_id TEXT")
            conn.commit()
            print("Поле local_payment_id успішно додано до таблиці payments_temp_data")
        else:
            print("Поле local_payment_id вже існує в таблиці payments_temp_data")
    except sqlite3.Error as e:
        print(f"Помилка при міграції таблиці payments_temp_data: {e}")


def migrate_payments_table():
    """Додає поле payment_type до таблиці payments"""
    try:
        cursor.execute("PRAGMA table_info(payments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'payment_type' not in columns:
            cursor.execute("ALTER TABLE payments ADD COLUMN payment_type TEXT DEFAULT 'one_time'")
            conn.commit()
            print("Поле payment_type успішно додано до таблиці payments")
        else:
            print("Поле payment_type вже існує в таблиці payments")
    except sqlite3.Error as e:
        print(f"Помилка при міграції таблиці payments: {e}")


# --- Партнерська програма ---

def migrate_users_partner_balance():
    """Додає поле partner_balance до таблиці users"""
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if "partner_balance" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN partner_balance REAL DEFAULT 0")
            conn.commit()
    except sqlite3.Error as e:
        print(f"Помилка при міграції users.partner_balance: {e}")


def create_partner_settings_table():
    """Налаштування партнерської програми (відсоток нарахування)"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partner_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO partner_settings (key, value) VALUES ('referral_percent', '20')"
    )
    conn.commit()


def create_partner_earnings_table():
    """Історія нарахувань партнерам з покупок рефералів"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partner_earnings (
            id INTEGER PRIMARY KEY,
            partner_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            purchase_amount REAL NOT NULL,
            credit_amount REAL NOT NULL,
            percent REAL NOT NULL,
            product_name TEXT,
            payment_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def create_partner_withdrawal_requests_table():
    """Запити на вивід коштів партнерів"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partner_withdrawal_requests (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME,
            admin_note TEXT,
            payout_details TEXT
        )
    """)
    conn.commit()


def migrate_partner_withdrawal_payout_details():
    """Додає поле payout_details до partner_withdrawal_requests."""
    try:
        cursor.execute("PRAGMA table_info(partner_withdrawal_requests)")
        columns = [c[1] for c in cursor.fetchall()]
        if "payout_details" not in columns:
            cursor.execute(
                "ALTER TABLE partner_withdrawal_requests ADD COLUMN payout_details TEXT"
            )
            conn.commit()
    except sqlite3.Error as e:
        print(f"Помилка migrate_partner_withdrawal_payout_details: {e}")


def get_ref_id_by_user(buyer_id: int):
    """Повертає ref_id (партнера) користувача, якщо є."""
    cursor.execute("SELECT ref_id FROM users WHERE user_id = ?", (buyer_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else None


def get_partner_balance(user_id: int) -> float:
    cursor.execute("SELECT partner_balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return float(row[0]) if row and row[0] is not None else 0.0


def add_partner_credit(
    partner_id: int,
    buyer_id: int,
    purchase_amount: float,
    product_name: str,
    payment_type: str = "one_time",
) -> bool:
    """Нараховує партнеру % від покупки реферала."""
    try:
        percent = get_partner_referral_percent()
        credit_amount = round(purchase_amount * (percent / 100), 1)
        if credit_amount <= 0:
            return True
        cursor.execute(
            """
            UPDATE users SET partner_balance = COALESCE(partner_balance, 0) + ?
            WHERE user_id = ?
            """,
            (credit_amount, partner_id),
        )
        cursor.execute(
            """
            INSERT INTO partner_earnings
            (partner_id, buyer_id, purchase_amount, credit_amount, percent, product_name, payment_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (partner_id, buyer_id, purchase_amount, credit_amount, percent, product_name, payment_type),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка add_partner_credit: {e}")
        return False


def get_partner_earnings_history(partner_id: int, limit: int = 50) -> list:
    """Історія нарахувань для партнера (buyer_id, purchase_amount, credit_amount, product_name, created_at)."""
    cursor.execute(
        """
        SELECT buyer_id, purchase_amount, credit_amount, product_name, payment_type, created_at
        FROM partner_earnings WHERE partner_id = ? ORDER BY created_at DESC LIMIT ?
        """,
        (partner_id, limit),
    )
    return cursor.fetchall()


def get_partner_referral_percent() -> float:
    cursor.execute(
        "SELECT value FROM partner_settings WHERE key = 'referral_percent'"
    )
    row = cursor.fetchone()
    if row:
        try:
            return float(row[0])
        except (ValueError, TypeError):
            pass
    return 20.0


def set_partner_referral_percent(percent: float) -> bool:
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO partner_settings (key, value) VALUES ('referral_percent', ?)",
            (str(percent),),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка set_partner_referral_percent: {e}")
        return False


def create_withdrawal_request(user_id: int, amount: float, payout_details: str = None) -> int | None:
    """Створює запит на вивід. Повертає id запиту або None."""
    try:
        cursor.execute(
            """
            INSERT INTO partner_withdrawal_requests (user_id, amount, status, payout_details)
            VALUES (?, ?, 'pending', ?)
            """,
            (user_id, amount, payout_details or ""),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Помилка create_withdrawal_request: {e}")
        return None


def get_partner_stats_for_admin() -> list:
    """Список партнерів для адмінки: (user_id, user_name, balance, referral_count, total_earned)."""
    cursor.execute("""
        SELECT u.user_id, u.user_name, COALESCE(u.partner_balance, 0),
               (SELECT COUNT(*) FROM users u2 WHERE u2.ref_id = u.user_id),
               (SELECT COALESCE(SUM(credit_amount), 0) FROM partner_earnings WHERE partner_id = u.user_id)
        FROM users u
        WHERE u.user_id IN (SELECT ref_id FROM users WHERE ref_id IS NOT NULL)
        ORDER BY COALESCE(u.partner_balance, 0) DESC
    """)
    return cursor.fetchall()


def get_partner_participants_count() -> int:
    """Кількість учасників партнерської програми (мають рефералів або баланс > 0 або є в partner_earnings)."""
    cursor.execute("""
        SELECT COUNT(DISTINCT u.user_id) FROM users u
        WHERE (SELECT COUNT(*) FROM users u2 WHERE u2.ref_id = u.user_id) > 0
           OR COALESCE(u.partner_balance, 0) > 0
           OR u.user_id IN (SELECT partner_id FROM partner_earnings)
    """)
    row = cursor.fetchone()
    return row[0] if row else 0


def get_all_partner_participants(limit: int, offset: int) -> list:
    """Список усіх учасників: (user_id, user_name, balance, referral_count, total_earned)."""
    cursor.execute("""
        SELECT u.user_id, u.user_name, COALESCE(u.partner_balance, 0),
               (SELECT COUNT(*) FROM users u2 WHERE u2.ref_id = u.user_id),
               (SELECT COALESCE(SUM(credit_amount), 0) FROM partner_earnings WHERE partner_id = u.user_id)
        FROM users u
        WHERE (SELECT COUNT(*) FROM users u2 WHERE u2.ref_id = u.user_id) > 0
           OR COALESCE(u.partner_balance, 0) > 0
           OR u.user_id IN (SELECT partner_id FROM partner_earnings)
        ORDER BY (SELECT COALESCE(SUM(credit_amount), 0) FROM partner_earnings WHERE partner_id = u.user_id) DESC,
                 COALESCE(u.partner_balance, 0) DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    return cursor.fetchall()


def get_referrals_of_partner(partner_user_id: int) -> list:
    """Реферали партнера: (user_id, user_name, join_date)."""
    cursor.execute(
        "SELECT user_id, user_name, join_date FROM users WHERE ref_id = ? ORDER BY join_date DESC",
        (partner_user_id,),
    )
    return cursor.fetchall()


def get_partner_total_earned(user_id: int) -> float:
    """Сума нарахованих партнеру коштів."""
    cursor.execute(
        "SELECT COALESCE(SUM(credit_amount), 0) FROM partner_earnings WHERE partner_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    return float(row[0]) if row else 0.0


def get_withdrawal_request_by_id(request_id: int):
    """Повертає (user_id, amount, status, payout_details) для запиту або None."""
    cursor.execute(
        "SELECT user_id, amount, status, COALESCE(payout_details, '') FROM partner_withdrawal_requests WHERE id = ?",
        (request_id,),
    )
    return cursor.fetchone()


def get_withdrawal_requests(status: str = None) -> list:
    """Список запитів на вивід (id, user_id, amount, status, created_at)."""
    if status:
        cursor.execute(
            """
            SELECT id, user_id, amount, status, created_at
            FROM partner_withdrawal_requests WHERE status = ? ORDER BY created_at DESC
            """,
            (status,),
        )
    else:
        cursor.execute(
            """
            SELECT id, user_id, amount, status, created_at
            FROM partner_withdrawal_requests ORDER BY created_at DESC
            """
        )
    return cursor.fetchall()


def complete_withdrawal_request(request_id: int, admin_note: str = None) -> bool:
    """Позначає вивід як виконаний і списує баланс."""
    try:
        cursor.execute(
            "SELECT user_id, amount, status FROM partner_withdrawal_requests WHERE id = ?",
            (request_id,),
        )
        row = cursor.fetchone()
        if not row or row[2] != "pending":
            return False
        user_id, amount = row[0], row[1]
        balance = get_partner_balance(user_id)
        if balance < amount:
            return False
        cursor.execute(
            "UPDATE users SET partner_balance = partner_balance - ? WHERE user_id = ?",
            (amount, user_id),
        )
        cursor.execute(
            """
            UPDATE partner_withdrawal_requests
            SET status = 'completed', processed_at = datetime('now'), admin_note = ?
            WHERE id = ?
            """,
            (admin_note or "", request_id),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка complete_withdrawal_request: {e}")
        return False


def reject_withdrawal_request(request_id: int, admin_note: str = None) -> bool:
    try:
        cursor.execute(
            """
            UPDATE partner_withdrawal_requests
            SET status = 'rejected', processed_at = datetime('now'), admin_note = ?
            WHERE id = ? AND status = 'pending'
            """,
            (admin_note or "", request_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Помилка reject_withdrawal_request: {e}")
        return False


def deduct_partner_balance(user_id: int, amount: float) -> bool:
    """Списує кошти з балансу партнера (оплата підписки з балансу)."""
    try:
        balance = get_partner_balance(user_id)
        if balance < amount:
            return False
        cursor.execute(
            "UPDATE users SET partner_balance = partner_balance - ? WHERE user_id = ?",
            (amount, user_id),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка deduct_partner_balance: {e}")
        return False


# Створюємо таблиці та виконуємо міграції
def create_tables():
    create_table()
    create_products_table()
    create_catalog_images_table()
    migrate_products_table()  # Додаємо поле payment_type до існуючої таблиці
    create_contest_table()
    create_payments_table()
    migrate_payments_table()  # Додаємо поле payment_type до таблиці payments
    create_subscriptions_table()
    create_user_tokens_table()
    create_recurring_subscriptions_table()
    create_subscription_payments_table()
    create_payments_temp_data_table()
    migrate_payments_temp_data_table()  # Додаємо поле local_payment_id
    migrate_users_partner_balance()
    create_partner_settings_table()
    create_partner_earnings_table()
    create_partner_withdrawal_requests_table()
    migrate_partner_withdrawal_payout_details()
    migrate_users_marketing_link()
    migrate_users_site_fields()
    migrate_payments_source()
    create_web_logins_table()
    enable_wal()
    from database.links_db import create_table_links
    create_table_links()
