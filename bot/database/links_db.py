import sqlite3

from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

LINK_START_PREFIX = "linktowatch_"


def build_link_start_payload(link_id: int) -> str:
    return f"{LINK_START_PREFIX}{link_id}"


def create_table_links():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY,
            link_name TEXT,
            link_url TEXT,
            link_count INTEGER DEFAULT 0,
            registrations_count INTEGER DEFAULT 0,
            purchases_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    migrate_links_table()


def migrate_links_table():
    cursor.execute("PRAGMA table_info(links)")
    columns = {column[1] for column in cursor.fetchall()}
    if "registrations_count" not in columns:
        cursor.execute(
            "ALTER TABLE links ADD COLUMN registrations_count INTEGER DEFAULT 0"
        )
    if "purchases_count" not in columns:
        cursor.execute(
            "ALTER TABLE links ADD COLUMN purchases_count INTEGER DEFAULT 0"
        )
    conn.commit()


def add_link(link_name: str, link_url: str = None):
    cursor.execute(
        "INSERT INTO links (link_name, link_url, link_count, registrations_count, purchases_count) "
        "VALUES (?, ?, 0, 0, 0)",
        (link_name, link_url),
    )
    conn.commit()
    return cursor.lastrowid


def get_all_links():
    cursor.execute("SELECT * FROM links")
    return cursor.fetchall()


def link_exists(link_id: int) -> bool:
    cursor.execute("SELECT 1 FROM links WHERE id = ?", (link_id,))
    return cursor.fetchone() is not None


def increment_link_count(link_id: int):
    cursor.execute(
        "UPDATE links SET link_count = link_count + 1 WHERE id = ?",
        (link_id,),
    )
    conn.commit()


def increment_link_registrations(link_id: int):
    cursor.execute(
        "UPDATE links SET registrations_count = registrations_count + 1 WHERE id = ?",
        (link_id,),
    )
    conn.commit()


def increment_link_purchases(link_id: int):
    cursor.execute(
        "UPDATE links SET purchases_count = purchases_count + 1 WHERE id = ?",
        (link_id,),
    )
    conn.commit()


def track_link_purchase(user_id: int):
    from database.client_db import get_marketing_link_id_by_user

    link_id = get_marketing_link_id_by_user(user_id)
    if link_id and link_exists(link_id):
        increment_link_purchases(link_id)


def get_link_stats():
    cursor.execute("SELECT link_name, link_count FROM links")
    return cursor.fetchall()


def get_link_detailed_stats():
    cursor.execute(
        "SELECT id, link_name, link_count, registrations_count, purchases_count FROM links"
    )
    return cursor.fetchall()


def get_link_stats_row(link_id: int):
    cursor.execute(
        "SELECT id, link_name, link_count, registrations_count, purchases_count "
        "FROM links WHERE id = ?",
        (link_id,),
    )
    return cursor.fetchone()


def get_link_by_id(link_id: int):
    cursor.execute("SELECT link_name, link_url FROM links WHERE id = ?", (link_id,))
    return cursor.fetchone()


def update_link_name(link_id: int, new_name: str):
    cursor.execute("UPDATE links SET link_name = ? WHERE id = ?", (new_name, link_id))
    conn.commit()


def delete_link(link_id: int):
    cursor.execute("DELETE FROM links WHERE id = ?", (link_id,))
    conn.commit()


def get_users_by_language():
    cursor.execute("SELECT language, COUNT(*) FROM users GROUP BY language")
    return cursor.fetchall()
