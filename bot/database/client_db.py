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
    
    
def add_user(user_id, user_name, ref_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    if existing_user is None:
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute('''
                INSERT INTO users (user_id, user_name, ref_id, join_date)
                VALUES (?, ?, ?, ?)
                ''', (user_id, user_name, ref_id, current_date))
            conn.commit()
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

def save_payment_info(payment_id: str, invoice_id: str, user_id: int, product_id: int, months: int, amount: float, status: str, payment_type: str = 'one_time') -> bool:
    try:
        cursor.execute("""
            INSERT INTO payments (
                payment_id, invoice_id, user_id, product_id, months, amount, status, payment_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (payment_id, invoice_id, user_id, product_id, months, amount, status, payment_type))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при збереженні платежу: {e}")
        return False

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

def get_user_subscriptions(user_id: int) -> list:
    try:
        cursor.execute("""
            SELECT product_name, price, start_date, end_date, status
            FROM subscriptions 
            WHERE user_id = ?
            ORDER BY end_date DESC
        """, (user_id,))
        
        subscriptions = []
        for row in cursor.fetchall():
            subscriptions.append({
                'product_name': row[0],
                'price': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'status': row[4]
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


def increment_payment_failures(subscription_id: int) -> bool:
    """Збільшує лічильник невдалих платежів"""
    try:
        cursor.execute("""
            UPDATE recurring_subscriptions 
            SET payment_failures = payment_failures + 1, updated_at = datetime('now')
            WHERE id = ?
        """, (subscription_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при оновленні лічильника помилок: {e}")
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
