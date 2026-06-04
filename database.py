import sqlite3
from datetime import datetime

DB_PATH = "passport_bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id   INTEGER NOT NULL,
            username      TEXT,
            name          TEXT NOT NULL,
            phone         TEXT NOT NULL,
            city          TEXT NOT NULL,
            passport_type TEXT NOT NULL,
            urgency       TEXT NOT NULL,
            photos        TEXT,
            lang          TEXT DEFAULT 'en',
            status        TEXT DEFAULT 'pending',
            created_at    TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_order(telegram_id, username, name, phone, city,
               passport_type, urgency, photos, lang) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        """INSERT INTO orders
           (telegram_id, username, name, phone, city,
            passport_type, urgency, photos, lang, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,'pending',?)""",
        (telegram_id, username, name, phone, city,
         passport_type, urgency, photos, lang,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_order_by_id(order_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM orders WHERE id=?", (order_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_orders(limit=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_order_status(order_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE orders SET status=? WHERE id=?", (status, order_id)
    )
    conn.commit()
    conn.close()
