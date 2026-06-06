import sqlite3
from datetime import datetime

DB_PATH = "passport_bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id     INTEGER NOT NULL,
            username        TEXT,
            name            TEXT NOT NULL,
            phone           TEXT NOT NULL,
            city            TEXT NOT NULL,
            passport_type   TEXT NOT NULL,
            urgency         TEXT NOT NULL,
            photos          TEXT,
            lang            TEXT DEFAULT 'en',
            status          TEXT DEFAULT 'pending',
            payment_status  TEXT DEFAULT 'unpaid',
            appointment_date TEXT,
            appointment_time TEXT,
            appointment_location TEXT,
            rating          INTEGER,
            reminder_sent   INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL
        )
    """)
    # Migration: add new columns to existing DB if they don't exist
    existing = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
    new_cols = {
        "payment_status":       "TEXT DEFAULT 'unpaid'",
        "appointment_date":     "TEXT",
        "appointment_time":     "TEXT",
        "appointment_location": "TEXT",
        "rating":               "INTEGER",
        "reminder_sent":        "INTEGER DEFAULT 0",
    }
    for col, definition in new_cols.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE orders ADD COLUMN {col} {definition}")
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
    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_orders(limit=20, status=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if status:
        rows = conn.execute(
            "SELECT * FROM orders WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_orders_by_telegram_id(telegram_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM orders WHERE telegram_id=? ORDER BY id DESC LIMIT 5", (telegram_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_order_status(order_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

def update_order_payment(order_id: int, payment_status: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE orders SET payment_status=? WHERE id=?", (payment_status, order_id))
    conn.commit()
    conn.close()

def update_appointment_details(order_id: int, date: str, time: str, location: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE orders SET appointment_date=?, appointment_time=?, appointment_location=? WHERE id=?",
        (date, time, location, order_id)
    )
    conn.commit()
    conn.close()

def save_rating(order_id: int, rating: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE orders SET rating=? WHERE id=?", (rating, order_id))
    conn.commit()
    conn.close()

def get_orders_needing_reminder():
    """Orders that are 'booked', have appointment_date tomorrow, reminder not yet sent."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    from datetime import date, timedelta
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    rows = conn.execute(
        """SELECT * FROM orders
           WHERE status='booked'
           AND appointment_date=?
           AND reminder_sent=0""",
        (tomorrow,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_reminder_sent(order_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE orders SET reminder_sent=1 WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

def search_orders_by_phone(phone: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM orders WHERE phone LIKE ? ORDER BY id DESC LIMIT 5",
        (f"%{phone}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_customer_ids():
    """Get all unique telegram_ids for broadcast."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT DISTINCT telegram_id FROM orders"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]
