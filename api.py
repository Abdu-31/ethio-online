"""
api.py — FastAPI backend for Passport Bot Mini App
Run alongside bot.py on Render using:
  uvicorn api:app --host 0.0.0.0 --port 8000
"""
import os
import json
import hmac
import hashlib
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from database import init_db, save_order, get_all_orders, get_order_by_id, update_order_status
import sqlite3

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID  = int(os.getenv("ADMIN_ID", "0"))

app = FastAPI(title="Passport Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Telegram WebApp auth validation ───────────────────────────────────────────
def validate_telegram_init_data(init_data: str) -> dict:
    """Validate Telegram WebApp initData and return parsed user data."""
    try:
        parsed = {}
        for item in init_data.split("&"):
            if "=" in item:
                k, v = item.split("=", 1)
                parsed[k] = v

        received_hash = parsed.pop("hash", "")
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        secret_key = hmac.new(
            b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
        ).digest()
        expected_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            raise ValueError("Invalid hash")

        # Check not too old (1 hour)
        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > 3600:
            raise ValueError("Data too old")

        user_data = json.loads(parsed.get("user", "{}"))
        return user_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")

def get_current_user(x_init_data: str = Header(...)):
    return validate_telegram_init_data(x_init_data)

def get_admin_user(x_init_data: str = Header(...)):
    user = validate_telegram_init_data(x_init_data)
    if user.get("id") != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Admin only")
    return user

# ── Models ─────────────────────────────────────────────────────────────────────
class StatusUpdate(BaseModel):
    status: str

class OrderCreate(BaseModel):
    name: str
    phone: str
    city: str
    passport_type: str
    urgency: str
    lang: str = "en"
    photos: list[str] = []

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/orders")
def create_order(order: OrderCreate, user: dict = Depends(get_current_user)):
    order_id = save_order(
        telegram_id=user["id"],
        username=user.get("username", ""),
        name=order.name,
        phone=order.phone,
        city=order.city,
        passport_type=order.passport_type,
        urgency=order.urgency,
        photos=",".join(order.photos),
        lang=order.lang
    )
    return {"order_id": order_id, "status": "pending"}

@app.get("/orders/my")
def my_orders(user: dict = Depends(get_current_user)):
    conn = sqlite3.connect("passport_bot.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, name, passport_type, urgency, status, created_at FROM orders WHERE telegram_id=? ORDER BY id DESC",
        (user["id"],)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/admin/orders")
def admin_list_orders(
    status: Optional[str] = None,
    user: dict = Depends(get_admin_user)
):
    conn = sqlite3.connect("passport_bot.db")
    conn.row_factory = sqlite3.Row
    if status:
        rows = conn.execute(
            "SELECT * FROM orders WHERE status=? ORDER BY id DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/admin/orders/{order_id}")
def admin_get_order(order_id: int, user: dict = Depends(get_admin_user)):
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.patch("/admin/orders/{order_id}/status")
def admin_update_status(
    order_id: int,
    body: StatusUpdate,
    user: dict = Depends(get_admin_user)
):
    valid = ["pending", "processing", "booked", "completed", "cancelled"]
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid}")
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    update_order_status(order_id, body.status)
    return {"order_id": order_id, "status": body.status}

@app.get("/admin/stats")
def admin_stats(user: dict = Depends(get_admin_user)):
    conn = sqlite3.connect("passport_bot.db")
    conn.row_factory = sqlite3.Row
    total    = conn.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
    pending  = conn.execute("SELECT COUNT(*) as c FROM orders WHERE status='pending'").fetchone()["c"]
    booked   = conn.execute("SELECT COUNT(*) as c FROM orders WHERE status='booked'").fetchone()["c"]
    done     = conn.execute("SELECT COUNT(*) as c FROM orders WHERE status='completed'").fetchone()["c"]
    conn.close()
    return {
        "total": total,
        "pending": pending,
        "booked": booked,
        "completed": done,
    }

@app.on_event("startup")
def startup():
    init_db()
