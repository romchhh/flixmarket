import sqlite3

from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    return count

def get_all_user_ids():
    cursor.execute('SELECT user_id FROM users')
    user_ids = [row[0] for row in cursor.fetchall()]
    return user_ids

def get_all_categories():
    try:
        cursor.execute("SELECT DISTINCT catalog_id, product_type FROM products")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Помилка при отриманні категорій: {e}")
        return []

def get_max_category_id():
    try:
        cursor.execute("SELECT MAX(catalog_id) FROM products")
        result = cursor.fetchone()[0]
        return result if result is not None else 0
    except sqlite3.Error as e:
        print(f"Помилка при отриманні максимального ID категорії: {e}")
        return 0

def add_new_product(category_id: int, product_type: str, name: str, description: str, price: str, photo_path: str, payment_type: str = 'subscription'):
    try:
        cursor.execute("""
            INSERT INTO products (catalog_id, product_type, product_name, product_description, product_price, product_photo, payment_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (category_id, product_type, name, description, price, photo_path, payment_type))
        cursor.connection.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при додаванні товару: {e}")
        return False
    
    
def get_category_type(category_id: int):
    try:
        cursor.execute("SELECT product_type FROM products WHERE catalog_id = ?", (category_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Помилка при отриманні типу категорії: {e}")


def set_category_image(catalog_id: int, image_path: str) -> bool:
    """Зберегти або оновити зображення категорії для маркетплейсу."""
    try:
        cursor.execute("""
            INSERT INTO catalog_images (catalog_id, image_path) VALUES (?, ?)
            ON CONFLICT(catalog_id) DO UPDATE SET image_path = excluded.image_path
        """, (catalog_id, image_path))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при збереженні зображення категорії: {e}")
        return False


def get_category_image(catalog_id: int) -> str | None:
    """Повертає шлях до зображення категорії або None."""
    try:
        cursor.execute("SELECT image_path FROM catalog_images WHERE catalog_id = ?", (catalog_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Помилка при отриманні зображення категорії: {e}")
        return None

def delete_product_from_db(product_id: int) -> bool:
    try:
        cursor.execute("""
            DELETE FROM products 
            WHERE id = ?
        """, (product_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при видаленні товару: {e}")
        return False

def update_product_name(product_id: int, new_name: str) -> bool:
    try:
        cursor.execute("""
            UPDATE products 
            SET product_name = ? 
            WHERE id = ?
        """, (new_name, product_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при оновленні назви: {e}")
        return False

def update_product_description(product_id: int, new_description: str) -> bool:
    try:
        cursor.execute("""
            UPDATE products 
            SET product_description = ? 
            WHERE id = ?
        """, (new_description, product_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при оновленні опису: {e}")
        return False

def update_product_price(product_id: int, new_price: str) -> bool:
    try:
        cursor.execute("""
            UPDATE products 
            SET product_price = ? 
            WHERE id = ?
        """, (new_price, product_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при оновленні ціни: {e}")
        return False

def update_product_payment_type(product_id: int, payment_type: str) -> bool:
    try:
        cursor.execute("""
            UPDATE products 
            SET payment_type = ? 
            WHERE id = ?
        """, (payment_type, product_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Помилка при оновленні типу оплати: {e}")
        return False

def get_product_payment_type(product_id: int) -> str:
    try:
        cursor.execute("SELECT payment_type FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        return result[0] if result else 'subscription'
    except sqlite3.Error as e:
        print(f"Помилка при отриманні типу оплати: {e}")
        return 'subscription'


def get_admin_subscriptions_stats():
    """Отримує статистику підписок для адміна"""
    try:
        stats = {}
        
        # Користувачі
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE DATE(join_date) = DATE('now', 'localtime')
        """)
        stats['new_users_today'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE DATE(join_date) >= DATE('now', 'localtime', '-7 days')
        """)
        stats['new_users_week'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE DATE(join_date) >= DATE('now', 'localtime', 'start of month')
        """)
        stats['new_users_month'] = cursor.fetchone()[0]
        
        # Товари
        cursor.execute("SELECT COUNT(*) FROM products")
        stats['total_products'] = cursor.fetchone()[0]
        
        # Загальна кількість підписок
        cursor.execute("SELECT COUNT(*) FROM subscriptions")
        stats['total_simple_subscriptions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recurring_subscriptions")
        stats['total_recurring_subscriptions'] = cursor.fetchone()[0]
        
        # Активні підписки
        cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
        stats['active_simple_subscriptions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recurring_subscriptions WHERE status = 'active'")
        stats['active_recurring_subscriptions'] = cursor.fetchone()[0]
        
        # Статистика платежів за сьогодні
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM payments 
            WHERE status = 'success' AND DATE(created_at) = DATE('now', 'localtime')
        """)
        today_payments = cursor.fetchone()
        stats['today_payments_count'] = today_payments[0]
        stats['today_revenue'] = today_payments[1]
        
        # Статистика автоматичних платежів за сьогодні
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM subscription_payments 
            WHERE status = 'success' AND DATE(payment_date) = DATE('now', 'localtime')
        """)
        today_auto_payments = cursor.fetchone()
        stats['today_auto_payments_count'] = today_auto_payments[0]
        stats['today_auto_revenue'] = today_auto_payments[1]
        
        # Статистика за місяць
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM payments 
            WHERE status = 'success' AND DATE(created_at) >= DATE('now', 'localtime', 'start of month')
        """)
        month_payments = cursor.fetchone()
        stats['month_payments_count'] = month_payments[0]
        stats['month_revenue'] = month_payments[1]
        
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM subscription_payments 
            WHERE status = 'success' AND DATE(payment_date) >= DATE('now', 'localtime', 'start of month')
        """)
        month_auto_payments = cursor.fetchone()
        stats['month_auto_payments_count'] = month_auto_payments[0]
        stats['month_auto_revenue'] = month_auto_payments[1]
        
        # Невдалі платежі сьогодні
        cursor.execute("""
            SELECT COUNT(*) 
            FROM subscription_payments 
            WHERE status = 'failed' AND DATE(payment_date) = DATE('now', 'localtime')
        """)
        stats['today_failed_payments'] = cursor.fetchone()[0]
        
        # Загальний дохід (всього часу)
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE status = 'success'
        """)
        stats['total_revenue'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM subscription_payments 
            WHERE status = 'success'
        """)
        stats['total_auto_revenue'] = cursor.fetchone()[0]
        
        return stats
        
    except sqlite3.Error as e:
        print(f"Помилка при отриманні статистики: {e}")
        return {}


def get_all_subscriptions_for_admin():
    """Отримує всі підписки для адміна"""
    try:
        subscriptions = []
        
        # Звичайні підписки
        cursor.execute("""
            SELECT s.id, s.user_id, s.product_name, s.price, s.start_date, s.end_date, s.status, u.user_name
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.user_id
            ORDER BY s.start_date DESC
        """)
        
        for row in cursor.fetchall():
            subscriptions.append({
                'type': 'simple',
                'id': row[0],
                'user_id': row[1],
                'product_name': row[2],
                'price': row[3],
                'start_date': row[4],
                'end_date': row[5],
                'status': row[6],
                'username': row[7] or 'Невідомо',
                'next_payment_date': None,
                'payment_failures': 0
            })
        
        # Повторювані підписки
        cursor.execute("""
            SELECT rs.id, rs.user_id, rs.product_name, rs.price, rs.months, rs.next_payment_date, rs.status, rs.payment_failures, u.user_name
            FROM recurring_subscriptions rs
            LEFT JOIN users u ON rs.user_id = u.user_id
            ORDER BY rs.created_at DESC
        """)
        
        for row in cursor.fetchall():
            subscriptions.append({
                'type': 'recurring',
                'id': row[0],
                'user_id': row[1],
                'product_name': row[2],
                'price': row[3],
                'months': row[4],
                'next_payment_date': row[5],
                'status': row[6],
                'payment_failures': row[7],
                'username': row[8] or 'Невідомо',
                'start_date': None,
                'end_date': None
            })
        
        return subscriptions
        
    except sqlite3.Error as e:
        print(f"Помилка при отриманні підписок: {e}")
        return []


def search_subscriptions_for_admin(query: str):
    """Шукає підписки за user_id, username, product_name або id підписки"""
    if not query or not query.strip():
        return []
    try:
        q = f"%{query.strip()}%"
        seen = set()
        subscriptions = []
        
        def add_simple(row):
            key = ('simple', row[0])
            if key in seen:
                return
            seen.add(key)
            subscriptions.append({
                'type': 'simple',
                'id': row[0],
                'user_id': row[1],
                'product_name': row[2],
                'price': row[3],
                'start_date': row[4],
                'end_date': row[5],
                'status': row[6],
                'username': row[7] or 'Невідомо',
                'next_payment_date': None,
                'payment_failures': 0
            })
        
        def add_recurring(row):
            key = ('recurring', row[0])
            if key in seen:
                return
            seen.add(key)
            subscriptions.append({
                'type': 'recurring',
                'id': row[0],
                'user_id': row[1],
                'product_name': row[2],
                'price': row[3],
                'months': row[4],
                'next_payment_date': row[5],
                'status': row[6],
                'payment_failures': row[7],
                'username': row[8] or 'Невідомо',
                'start_date': None,
                'end_date': None
            })
        
        if query.strip().isdigit():
            user_id = int(query.strip())
            cursor.execute("""
                SELECT s.id, s.user_id, s.product_name, s.price, s.start_date, s.end_date, s.status, u.user_name
                FROM subscriptions s
                LEFT JOIN users u ON s.user_id = u.user_id
                WHERE s.user_id = ?
                ORDER BY s.start_date DESC
            """, (user_id,))
            for row in cursor.fetchall():
                add_simple(row)
            cursor.execute("""
                SELECT rs.id, rs.user_id, rs.product_name, rs.price, rs.months, rs.next_payment_date, rs.status, rs.payment_failures, u.user_name
                FROM recurring_subscriptions rs
                LEFT JOIN users u ON rs.user_id = u.user_id
                WHERE rs.user_id = ?
                ORDER BY rs.created_at DESC
            """, (user_id,))
            for row in cursor.fetchall():
                add_recurring(row)
        
        cursor.execute("""
            SELECT s.id, s.user_id, s.product_name, s.price, s.start_date, s.end_date, s.status, u.user_name
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE u.user_name LIKE ? OR s.product_name LIKE ?
            ORDER BY s.start_date DESC
        """, (q, q))
        for row in cursor.fetchall():
            add_simple(row)
        
        cursor.execute("""
            SELECT rs.id, rs.user_id, rs.product_name, rs.price, rs.months, rs.next_payment_date, rs.status, rs.payment_failures, u.user_name
            FROM recurring_subscriptions rs
            LEFT JOIN users u ON rs.user_id = u.user_id
            WHERE u.user_name LIKE ? OR rs.product_name LIKE ?
            ORDER BY rs.created_at DESC
        """, (q, q))
        for row in cursor.fetchall():
            add_recurring(row)
        
        if query.strip().isdigit():
            sub_id = int(query.strip())
            cursor.execute("SELECT id FROM subscriptions WHERE id = ?", (sub_id,))
            if cursor.fetchone():
                cursor.execute("""
                    SELECT s.id, s.user_id, s.product_name, s.price, s.start_date, s.end_date, s.status, u.user_name
                    FROM subscriptions s
                    LEFT JOIN users u ON s.user_id = u.user_id
                    WHERE s.id = ?
                """, (sub_id,))
                row = cursor.fetchone()
                if row:
                    add_simple(row)
            cursor.execute("SELECT id FROM recurring_subscriptions WHERE id = ?", (sub_id,))
            if cursor.fetchone():
                cursor.execute("""
                    SELECT rs.id, rs.user_id, rs.product_name, rs.price, rs.months, rs.next_payment_date, rs.status, rs.payment_failures, u.user_name
                    FROM recurring_subscriptions rs
                    LEFT JOIN users u ON rs.user_id = u.user_id
                    WHERE rs.id = ?
                """, (sub_id,))
                row = cursor.fetchone()
                if row:
                    add_recurring(row)
        
        return subscriptions
        
    except sqlite3.Error as e:
        print(f"Помилка при пошуку підписок: {e}")
        return []


def get_subscription_details(subscription_id: int, subscription_type: str):
    """Отримує детальну інформацію про підписку"""
    try:
        if subscription_type == 'simple':
            cursor.execute("""
                SELECT s.id, s.user_id, s.product_name, s.price, s.start_date, s.end_date, s.status, u.user_name
                FROM subscriptions s
                LEFT JOIN users u ON s.user_id = u.user_id
                WHERE s.id = ?
            """, (subscription_id,))
        else:  # recurring
            cursor.execute("""
                SELECT rs.id, rs.user_id, rs.product_name, rs.price, rs.months, rs.next_payment_date, rs.status, rs.payment_failures, u.user_name
                FROM recurring_subscriptions rs
                LEFT JOIN users u ON rs.user_id = u.user_id
                WHERE rs.id = ?
            """, (subscription_id,))
        
        return cursor.fetchone()
        
    except sqlite3.Error as e:
        print(f"Помилка при отриманні деталей підписки: {e}")
        return None


def update_subscription_status(subscription_id: int, subscription_type: str, new_status: str):
    """Змінює статус підписки"""
    try:
        if subscription_type == 'simple':
            cursor.execute("""
                UPDATE subscriptions 
                SET status = ? 
                WHERE id = ?
            """, (new_status, subscription_id))
        else:  # recurring
            cursor.execute("""
                UPDATE recurring_subscriptions 
                SET status = ?, updated_at = datetime('now') 
                WHERE id = ?
            """, (new_status, subscription_id))
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Помилка при оновленні статусу підписки: {e}")
        return False


def delete_subscription(subscription_id: int, subscription_type: str):
    """Видаляє підписку"""
    try:
        if subscription_type == 'simple':
            cursor.execute("DELETE FROM subscriptions WHERE id = ?", (subscription_id,))
        else:  # recurring
            cursor.execute("DELETE FROM recurring_subscriptions WHERE id = ?", (subscription_id,))
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Помилка при видаленні підписки: {e}")
        return False
