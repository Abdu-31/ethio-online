import os
import asyncio
import sqlite3
import logging
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from marketing import get_daily_post
from database import init_db, save_order, get_all_orders, update_order_status, get_order_by_id

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN    = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_ID   = os.getenv("CHANNEL_ID", "@your_channel_username")
ADMIN_ID     = int(os.getenv("ADMIN_ID", "0"))  # Your Telegram user ID

# ── Conversation states ────────────────────────────────────────────────────────
LANG, NAME, PHONE, CITY, PASSPORT_TYPE, URGENCY, PHOTOS, CONFIRM = range(8)
ADMIN_STATUS_ORDER_ID, ADMIN_STATUS_MESSAGE = range(8, 10)

# ── Language strings ───────────────────────────────────────────────────────────
STRINGS = {
    "en": {
        "welcome": (
            "🛂 *Welcome to Ethiopia Passport Service Bot!*\n\n"
            "We help you book passport appointments fast and hassle-free.\n\n"
            "Choose your language / Afaan keessan filadhaa / ቋንቋዎን ይምረጡ:"
        ),
        "ask_name": "📝 Please enter your *full name* (as on ID):",
        "ask_phone": "📞 Enter your *phone number* (e.g. 0911234567):",
        "ask_city": "📍 Which *city* are you in?\n(e.g. Addis Ababa, Jimma, Dire Dawa, Adama...)",
        "ask_passport_type": "🛂 Select *passport type*:",
        "new_passport": "🆕 New Passport",
        "renewal": "🔄 Renewal",
        "ask_urgency": "⚡ How urgent is your appointment?",
        "urgent": "🔴 Urgent (1–3 days)",
        "regular": "🟢 Regular (1–2 weeks)",
        "ask_photos": (
            "📎 Please send your *document photos* now.\n\n"
            "Send all photos one by one, then tap *Done* when finished."
        ),
        "done_btn": "✅ Done — Submit Order",
        "confirm_title": "📋 *Order Summary — Please confirm:*\n\n",
        "confirm_btn": "✅ Confirm & Submit",
        "edit_btn": "✏️ Start Over",
        "order_submitted": (
            "✅ *Order submitted successfully!*\n\n"
            "Our team will contact you within a few hours.\n"
            "Your order ID: *#{order_id}*\n\n"
            "To check status anytime: /status"
        ),
        "no_orders": "You have no orders yet. Use /start to place one.",
        "status_header": "📋 *Your Orders:*\n\n",
        "cancelled": "Order cancelled. Use /start to begin again.",
    },
    "am": {
        "welcome": (
            "🛂 *እንኳን ደህና መጡ — የፓስፖርት አገልግሎት ቦት!*\n\n"
            "ፓስፖርት ቀጠሮ እንድናስይዝልዎ እናግዝዎታለን።\n\n"
            "ቋንቋዎን ይምረጡ:"
        ),
        "ask_name": "📝 *ሙሉ ስምዎን* ያስገቡ (በመታወቂያ ላይ እንዳለ):",
        "ask_phone": "📞 *ስልክ ቁጥርዎን* ያስገቡ (ለምሳሌ 0911234567):",
        "ask_city": "📍 *በምን ከተማ* ነዎት?\n(ለምሳሌ አዲስ አበባ፣ ጅማ፣ ድሬዳዋ፣ አዳማ...)",
        "ask_passport_type": "🛂 *የፓስፖርት አይነት* ይምረጡ:",
        "new_passport": "🆕 አዲስ ፓስፖርት",
        "renewal": "🔄 ታደሰ",
        "ask_urgency": "⚡ ቀጠሮው ምን ያህል አስቸኳይ ነው?",
        "urgent": "🔴 አስቸኳይ (1–3 ቀናት)",
        "regular": "🟢 መደበኛ (1–2 ሳምንት)",
        "ask_photos": (
            "📎 *የሰነድ ፎቶዎቻቸውን* አሁን ይላኩ።\n\n"
            "ፎቶዎቹን አንድ በአንድ ይላኩ፣ ከጨረሱ በኋላ *ጨርሻለሁ* ይጫኑ።"
        ),
        "done_btn": "✅ ጨርሻለሁ — ትዕዛዝ ላክ",
        "confirm_title": "📋 *የትዕዛዝ ማጠቃለያ — ያረጋግጡ:*\n\n",
        "confirm_btn": "✅ አረጋግጥ እና ላክ",
        "edit_btn": "✏️ እንደገና ጀምር",
        "order_submitted": (
            "✅ *ትዕዛዝዎ ተልኳል!*\n\n"
            "ቡድናችን በጥቂት ሰዓታት ውስጥ ያገኝዎታል።\n"
            "የትዕዛዝ መለያ: *#{order_id}*\n\n"
            "ሁኔታ ለማወቅ: /status"
        ),
        "no_orders": "ምንም ትዕዛዝ የለዎትም። ለመጀመር /start ይጠቀሙ።",
        "status_header": "📋 *ትዕዛዞቾዎ:*\n\n",
        "cancelled": "ትዕዛዝ ተሰርዟል። እንደገና ለመጀመር /start ይጠቀሙ።",
    },
    "om": {
        "welcome": (
            "🛂 *Baga nagaan dhuftan — Tajaajila Paaspoortii!*\n\n"
            "Beellama paaspoortii qabsiifachuu isin gargaarra.\n\n"
            "Afaan filadhaa:"
        ),
        "ask_name": "📝 *Maqaa guutuu* keessan galchaa (ID irratti akka jirutti):",
        "ask_phone": "📞 *Lakkoofsa bilbilaa* keessan galchaa (fkn. 0911234567):",
        "ask_city": "📍 *Magaalaa* kamitti argamtu?\n(fkn. Finfinnee, Jimmaa, Dire Dawa, Adaamaa...)",
        "ask_passport_type": "🛂 *Gosa paaspoortii* filadhaa:",
        "new_passport": "🆕 Paaspoortii Haaraa",
        "renewal": "🔄 Haaromsa",
        "ask_urgency": "⚡ Beellanni kun yeroo meeqa barbaadaa?",
        "urgent": "🔴 Ariifachiisaa (guyyaa 1–3)",
        "regular": "🟢 Idilee (torbee 1–2)",
        "ask_photos": (
            "📎 *Suuraa sanadeewwan* keessan amma ergi.\n\n"
            "Suuraalee tokkoon tokkoon ergi, xumurte booda *Xumurame* tuqi."
        ),
        "done_btn": "✅ Xumurame — Ajaja Ergi",
        "confirm_title": "📋 *Cuunfaa Ajajaa — Mirkaneessi:*\n\n",
        "confirm_btn": "✅ Mirkaneessi fi Ergi",
        "edit_btn": "✏️ Deebi'ii Jalqabi",
        "order_submitted": (
            "✅ *Ajajni kee milkaa'inaan ergame!*\n\n"
            "Gareen keenya sa'aatii muraasa keessatti si quunnamti.\n"
            "ID Ajajaa: *#{order_id}*\n\n"
            "Haala ilaaluuf: /status"
        ),
        "no_orders": "Ajajni hin jiru. /start fayyadami.",
        "status_header": "📋 *Ajajawwan kee:*\n\n",
        "cancelled": "Ajajni haquame. Deebi'uuf /start fayyadami.",
    }
}

STATUS_EMOJI = {
    "pending":    "⏳ Pending",
    "processing": "🔄 Processing",
    "booked":     "✅ Appointment Booked",
    "completed":  "🎉 Completed",
    "cancelled":  "❌ Cancelled",
}

def s(lang, key):
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, ""))

def lang_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇪🇹 አማርኛ",   callback_data="lang_am"),
        InlineKeyboardButton("Afaan Oromoo", callback_data="lang_om"),
    ]])

def passport_type_keyboard(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(s(lang, "new_passport"), callback_data="type_new"),
        InlineKeyboardButton(s(lang, "renewal"),      callback_data="type_renewal"),
    ]])

def urgency_keyboard(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(s(lang, "urgent"),  callback_data="urgency_urgent"),
        InlineKeyboardButton(s(lang, "regular"), callback_data="urgency_regular"),
    ]])

# ── /start ─────────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        STRINGS["en"]["welcome"],
        parse_mode="Markdown",
        reply_markup=lang_keyboard()
    )
    return LANG

async def lang_chosen(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    ctx.user_data["lang"] = lang
    await query.edit_message_text(
        s(lang, "ask_name"), parse_mode="Markdown"
    )
    return NAME

# ── Collect fields ─────────────────────────────────────────────────────────────
async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "en")
    ctx.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(s(lang, "ask_phone"), parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "en")
    ctx.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(s(lang, "ask_city"), parse_mode="Markdown")
    return CITY

async def get_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "en")
    ctx.user_data["city"] = update.message.text.strip()
    await update.message.reply_text(
        s(lang, "ask_passport_type"),
        parse_mode="Markdown",
        reply_markup=passport_type_keyboard(lang)
    )
    return PASSPORT_TYPE

async def get_passport_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang", "en")
    ctx.user_data["passport_type"] = "New Passport" if query.data == "type_new" else "Renewal"
    await query.edit_message_text(
        s(lang, "ask_urgency"),
        parse_mode="Markdown",
        reply_markup=urgency_keyboard(lang)
    )
    return URGENCY

async def get_urgency(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang", "en")
    ctx.user_data["urgency"] = "Urgent (1–3 days)" if query.data == "urgency_urgent" else "Regular (1–2 weeks)"
    ctx.user_data["photos"] = []

    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(s(lang, "done_btn"))]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await query.message.reply_text(
        s(lang, "ask_photos"), parse_mode="Markdown", reply_markup=kb
    )
    return PHOTOS

async def collect_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "en")
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        ctx.user_data.setdefault("photos", []).append(file_id)
        await update.message.reply_text(
            f"✅ Photo {len(ctx.user_data['photos'])} received. Send more or tap Done."
        )
    elif update.message.document:
        ctx.user_data.setdefault("photos", []).append(update.message.document.file_id)
        await update.message.reply_text(
            f"✅ Document {len(ctx.user_data['photos'])} received. Send more or tap Done."
        )
    return PHOTOS

async def photos_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "en")
    d = ctx.user_data
    summary = (
        f"{s(lang, 'confirm_title')}"
        f"👤 *Name:* {d.get('name')}\n"
        f"📞 *Phone:* {d.get('phone')}\n"
        f"📍 *City:* {d.get('city')}\n"
        f"🛂 *Type:* {d.get('passport_type')}\n"
        f"⚡ *Urgency:* {d.get('urgency')}\n"
        f"📎 *Photos:* {len(d.get('photos', []))} file(s)\n"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(s(lang, "confirm_btn"), callback_data="confirm_yes"),
        InlineKeyboardButton(s(lang, "edit_btn"),    callback_data="confirm_no"),
    ]])
    await update.message.reply_text(
        summary, parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text("👆 Review above and confirm:", reply_markup=kb)
    return CONFIRM

async def confirm_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang", "en")

    if query.data == "confirm_no":
        await query.edit_message_text(s(lang, "cancelled"))
        return ConversationHandler.END

    d = ctx.user_data
    user = update.effective_user
    order_id = save_order(
        telegram_id=user.id,
        username=user.username or "",
        name=d.get("name", ""),
        phone=d.get("phone", ""),
        city=d.get("city", ""),
        passport_type=d.get("passport_type", ""),
        urgency=d.get("urgency", ""),
        photos=",".join(d.get("photos", [])),
        lang=lang
    )

    # Notify admin
    await notify_admin(ctx, order_id, user, d)

    msg = s(lang, "order_submitted").replace("{order_id}", str(order_id))
    await query.edit_message_text(msg, parse_mode="Markdown")
    return ConversationHandler.END

async def notify_admin(ctx, order_id, user, d):
    if not ADMIN_ID:
        return
    text = (
        f"🔔 *New Order #{order_id}*\n\n"
        f"👤 {d.get('name')} | @{user.username or 'N/A'}\n"
        f"📞 {d.get('phone')}\n"
        f"📍 {d.get('city')}\n"
        f"🛂 {d.get('passport_type')} — {d.get('urgency')}\n"
        f"📎 {len(d.get('photos', []))} photo(s)\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Update status: /setstatus {order_id}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Processing", callback_data=f"admin_processing_{order_id}"),
        InlineKeyboardButton("✅ Booked",      callback_data=f"admin_booked_{order_id}"),
    ],[
        InlineKeyboardButton("🎉 Completed",  callback_data=f"admin_completed_{order_id}"),
        InlineKeyboardButton("❌ Cancel",      callback_data=f"admin_cancelled_{order_id}"),
    ]])
    await ctx.bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=kb)

    # Send photos to admin
    for photo_id in d.get("photos", []):
        try:
            await ctx.bot.send_photo(ADMIN_ID, photo_id)
        except Exception:
            try:
                await ctx.bot.send_document(ADMIN_ID, photo_id)
            except Exception:
                pass

# ── Admin status update ────────────────────────────────────────────────────────
async def admin_status_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await query.answer("Not authorized.", show_alert=True)
        return
    await query.answer()

    parts = query.data.split("_")  # admin_<status>_<order_id>
    new_status = parts[1]
    order_id   = int(parts[2])

    order = get_order_by_id(order_id)
    if not order:
        await query.edit_message_text("Order not found.")
        return

    update_order_status(order_id, new_status)

    # Notify customer
    customer_id = order["telegram_id"]
    lang        = order["lang"]
    status_label = STATUS_EMOJI.get(new_status, new_status)

    customer_msg = {
        "en": f"📬 *Update on your order #{order_id}*\n\nStatus: *{status_label}*\n\nQuestions? Reply here.",
        "am": f"📬 *የትዕዛዝዎ #{order_id} ዝማኔ*\n\nሁኔታ: *{status_label}*\n\nጥያቄ ካለዎት እዚህ ይጻፉ።",
        "om": f"📬 *Haaromsa Ajajaa #{order_id}*\n\nHaala: *{status_label}*\n\nGaafii qabdaa? Asitti deebisi.",
    }.get(lang, f"📬 Order #{order_id} status: *{status_label}*")

    try:
        await ctx.bot.send_message(customer_id, customer_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Could not notify customer: {e}")

    await query.edit_message_text(
        f"✅ Order #{order_id} marked as *{status_label}*\nCustomer notified.",
        parse_mode="Markdown"
    )

# ── /status command ────────────────────────────────────────────────────────────
async def my_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("passport_bot.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, passport_type, urgency, status, created_at FROM orders WHERE telegram_id=? ORDER BY id DESC LIMIT 5",
        (user_id,)
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("You have no orders yet. Use /start to place one.")
        return

    text = "📋 *Your Orders:*\n\n"
    for r in rows:
        status_label = STATUS_EMOJI.get(r["status"], r["status"])
        text += (
            f"*Order #{r['id']}*\n"
            f"  Type: {r['passport_type']}\n"
            f"  {r['urgency']}\n"
            f"  Status: {status_label}\n"
            f"  Date: {r['created_at'][:10]}\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# ── Admin /orders command ──────────────────────────────────────────────────────
async def admin_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    orders = get_all_orders(limit=10)
    if not orders:
        await update.message.reply_text("No orders yet.")
        return
    text = "📋 *Last 10 Orders:*\n\n"
    for o in orders:
        status_label = STATUS_EMOJI.get(o["status"], o["status"])
        text += (
            f"*#{o['id']}* — {o['name']} | {o['phone']}\n"
            f"  {o['passport_type']} | {o['urgency']}\n"
            f"  {o['city']} | {status_label}\n"
            f"  {o['created_at'][:16]}\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# ── Daily marketing post ───────────────────────────────────────────────────────
async def post_daily_marketing(app: Application):
    post = get_daily_post()
    try:
        await app.bot.send_message(
            CHANNEL_ID, post,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info("Daily marketing post sent.")
    except Exception as e:
        logger.error(f"Failed to send marketing post: {e}")

async def manual_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await post_daily_marketing(ctx.application)
    await update.message.reply_text("✅ Marketing post sent to channel.")

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "en")
    await update.message.reply_text(
        s(lang, "cancelled"),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG:          [CallbackQueryHandler(lang_chosen, pattern="^lang_")],
            NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CITY:          [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            PASSPORT_TYPE: [CallbackQueryHandler(get_passport_type, pattern="^type_")],
            URGENCY:       [CallbackQueryHandler(get_urgency, pattern="^urgency_")],
            PHOTOS: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, collect_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, photos_done),
            ],
            CONFIRM: [CallbackQueryHandler(confirm_order, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("status",  my_status))
    app.add_handler(CommandHandler("orders",  admin_orders))
    app.add_handler(CommandHandler("post",    manual_post))
    app.add_handler(CallbackQueryHandler(admin_status_button, pattern="^admin_"))

    # Scheduler for daily posts
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: asyncio.create_task(post_daily_marketing(app)),
        trigger="cron",
        hour=9, minute=0,   # 9:00 AM daily
        timezone="Africa/Addis_Ababa"
    )
    scheduler.start()

    logger.info("Bot started.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
