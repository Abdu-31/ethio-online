import os
import asyncio
import sqlite3
import logging
from datetime import datetime
from io import BytesIO

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from marketing import get_daily_post
from database import (
    init_db, save_order, get_all_orders, update_order_status,
    get_order_by_id, update_order_payment, update_appointment_details,
    save_rating, get_orders_needing_reminder, mark_reminder_sent,
    search_orders_by_phone, get_all_customer_ids, get_orders_by_telegram_id
)
from pdf_generator import generate_appointment_pdf

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel_username")
ADMIN_ID   = int(os.getenv("ADMIN_ID", "0"))

TELEBIRR_NUMBER = "0925470395"
MPESA_NUMBER    = "0713057628"
SERVICE_FEE     = "6,000 ETB"

# ── Conversation states ────────────────────────────────────────────────────────
LANG, NAME, PHONE, CITY, PASSPORT_TYPE, URGENCY, PHOTOS, CONFIRM = range(8)
APPT_ORDER_ID, APPT_DATE, APPT_TIME, APPT_LOCATION = range(8, 12)
BROADCAST_MSG  = 12
SEARCH_PHONE   = 13
RATING_STATE   = 14

# ── Language strings ───────────────────────────────────────────────────────────
STRINGS = {
    "en": {
        "welcome": (
            "🛂 *Welcome to Ethio Online Passport Service!*\n\n"
            "We help you book passport appointments fast and hassle-free.\n\n"
            "Choose your language:"
        ),
        "ask_name":          "📝 Please enter your *full name* (as on ID):",
        "ask_phone":         "📞 Enter your *phone number* (e.g. 0911234567):",
        "ask_city":          "📍 Which *city* are you in?\n(e.g. Addis Ababa, Jimma, Dire Dawa, Adama...)",
        "ask_passport_type": "🛂 Select *passport type*:",
        "new_passport":      "🆕 New Passport",
        "renewal":           "🔄 Renewal",
        "ask_urgency":       "⚡ How urgent is your appointment?",
        "urgent":            "🔴 Urgent (1–3 days)",
        "regular":           "🟢 Regular (1–2 weeks)",
        "ask_photos":        "📎 Please send your *document photos* now.\n\nSend all photos one by one, then tap *Done* when finished.",
        "done_btn":          "✅ Done — Submit Order",
        "confirm_title":     "📋 *Order Summary — Please confirm:*\n\n",
        "confirm_btn":       "✅ Confirm & Submit",
        "edit_btn":          "✏️ Start Over",
        "order_submitted": (
            "✅ *Order submitted successfully!*\n\n"
            "Our team will review and contact you shortly.\n"
            "Your order ID: *#{order_id}*\n\n"
            "Check status anytime: /status"
        ),
        "cancelled": "Order cancelled. Use /start to begin again.",
        "payment_msg": (
            "💳 *Payment Required — Service Fee*\n\n"
            "Your appointment has been approved! ✅\n\n"
            f"Please pay the service fee of *{SERVICE_FEE}* to one of:\n\n"
            f"📱 *TeleBirr:* `{TELEBIRR_NUMBER}`\n"
            f"📱 *M-Pesa:*   `{MPESA_NUMBER}`\n\n"
            "After payment, send your *payment screenshot* here.\n"
            "⚠️ This fee covers our booking service only and does not include government fees."
        ),
        "payment_received": (
            "✅ *Payment confirmed!*\n\n"
            "Your appointment is now fully booked.\n"
            "You will receive your appointment confirmation document shortly."
        ),
        "reminder_msg": (
            "⏰ *Appointment Reminder!*\n\n"
            "You have a passport appointment *tomorrow*.\n\n"
            "📅 Date: *{date}*\n"
            "🕐 Time: *{time}*\n"
            "📍 Location: *{location}*\n\n"
            "Please arrive 15 minutes early and bring all required documents."
        ),
        "rate_msg": (
            "⭐ *How was your experience?*\n\n"
            "Your appointment is complete! We'd love your feedback.\n"
            "Please rate our service:"
        ),
        "rate_thanks": "🙏 Thank you for your rating! Your feedback helps us improve.",
    },
    "am": {
        "welcome": (
            "🛂 *እንኳን ደህና መጡ — ኢትዮ ኦንላይን የፓስፖርት አገልግሎት!*\n\n"
            "ፓስፖርት ቀጠሮ እንድናስይዝልዎ እናግዝዎታለን።\n\n"
            "ቋንቋዎን ይምረጡ:"
        ),
        "ask_name":          "📝 *ሙሉ ስምዎን* ያስገቡ (በመታወቂያ ላይ እንዳለ):",
        "ask_phone":         "📞 *ስልክ ቁጥርዎን* ያስገቡ (ለምሳሌ 0911234567):",
        "ask_city":          "📍 *በምን ከተማ* ነዎት?\n(ለምሳሌ አዲስ አበባ፣ ጅማ፣ ድሬዳዋ፣ አዳማ...)",
        "ask_passport_type": "🛂 *የፓስፖርት አይነት* ይምረጡ:",
        "new_passport":      "🆕 አዲስ ፓስፖርት",
        "renewal":           "🔄 ታደሰ",
        "ask_urgency":       "⚡ ቀጠሮው ምን ያህል አስቸኳይ ነው?",
        "urgent":            "🔴 አስቸኳይ (1–3 ቀናት)",
        "regular":           "🟢 መደበኛ (1–2 ሳምንት)",
        "ask_photos":        "📎 *የሰነድ ፎቶዎቻቸውን* አሁን ይላኩ።\n\nፎቶዎቹን አንድ በአንድ ይላኩ፣ ከጨረሱ በኋላ *ጨርሻለሁ* ይጫኑ።",
        "done_btn":          "✅ ጨርሻለሁ — ትዕዛዝ ላክ",
        "confirm_title":     "📋 *የትዕዛዝ ማጠቃለያ — ያረጋግጡ:*\n\n",
        "confirm_btn":       "✅ አረጋግጥ እና ላክ",
        "edit_btn":          "✏️ እንደገና ጀምር",
        "order_submitted": (
            "✅ *ትዕዛዝዎ ተልኳል!*\n\n"
            "ቡድናችን ይገመግምና በቅርቡ ያገኝዎታል።\n"
            "የትዕዛዝ መለያ: *#{order_id}*\n\n"
            "ሁኔታ ለማወቅ: /status"
        ),
        "cancelled": "ትዕዛዝ ተሰርዟል። እንደገና ለመጀመር /start ይጠቀሙ።",
        "payment_msg": (
            "💳 *ክፍያ ያስፈልጋል — የአገልግሎት ክፍያ*\n\n"
            "ቀጠሮዎ ጸድቋል! ✅\n\n"
            f"እባክዎ *{SERVICE_FEE}* ወደ አንዱ ይላኩ:\n\n"
            f"📱 *ቴሌብር:* `{TELEBIRR_NUMBER}`\n"
            f"📱 *ኤም-ፔሳ:* `{MPESA_NUMBER}`\n\n"
            "ከከፈሉ በኋላ *የክፍያ ስክሪንሾት* እዚህ ይላኩ።\n"
            "⚠️ ይህ ክፍያ የቦት አገልግሎት ክፍያ ብቻ ሲሆን የመንግስት ክፍያን አያካትትም።"
        ),
        "payment_received": (
            "✅ *ክፍያ ተረጋግጧል!*\n\n"
            "ቀጠሮዎ ሙሉ በሙሉ ተያዘ።\n"
            "የቀጠሮ ማረጋገጫ ሰነድ በቅርቡ ይደርስዎታል።"
        ),
        "reminder_msg": (
            "⏰ *የቀጠሮ አስታዋሽ!*\n\n"
            "ነገ የፓስፖርት ቀጠሮ አለዎት።\n\n"
            "📅 ቀን: *{date}*\n"
            "🕐 ሰዓት: *{time}*\n"
            "📍 ቦታ: *{location}*\n\n"
            "እባክዎ 15 ደቂቃ ቀደም ብለው ይቅረቡ።"
        ),
        "rate_msg": (
            "⭐ *ልምድዎ እንደምን ነበር?*\n\n"
            "ቀጠሮዎ ተጠናቋል! አስተያየትዎን ንገሩን።\n"
            "አገልግሎታችንን ይገምግሙ:"
        ),
        "rate_thanks": "🙏 ለግምገማዎ እናመሰግናለን! አስተያየትዎ እናሻሽልበታለን።",
    },
    "om": {
        "welcome": (
            "🛂 *Baga nagaan dhuftan — Tajaajila Paaspoortii Ethio Online!*\n\n"
            "Beellama paaspoortii qabsiifachuu isin gargaarra.\n\n"
            "Afaan filadhaa:"
        ),
        "ask_name":          "📝 *Maqaa guutuu* keessan galchaa (ID irratti akka jirutti):",
        "ask_phone":         "📞 *Lakkoofsa bilbilaa* keessan galchaa (fkn. 0911234567):",
        "ask_city":          "📍 *Magaalaa* kamitti argamtu?\n(fkn. Finfinnee, Jimmaa, Dire Dawa, Adaamaa...)",
        "ask_passport_type": "🛂 *Gosa paaspoortii* filadhaa:",
        "new_passport":      "🆕 Paaspoortii Haaraa",
        "renewal":           "🔄 Haaromsa",
        "ask_urgency":       "⚡ Beellanni kun yeroo meeqa barbaadaa?",
        "urgent":            "🔴 Ariifachiisaa (guyyaa 1–3)",
        "regular":           "🟢 Idilee (torbee 1–2)",
        "ask_photos":        "📎 *Suuraa sanadeewwan* keessan amma ergi.\n\nSuuraalee tokkoon tokkoon ergi, xumurte booda *Xumurame* tuqi.",
        "done_btn":          "✅ Xumurame — Ajaja Ergi",
        "confirm_title":     "📋 *Cuunfaa Ajajaa — Mirkaneessi:*\n\n",
        "confirm_btn":       "✅ Mirkaneessi fi Ergi",
        "edit_btn":          "✏️ Deebi'ii Jalqabi",
        "order_submitted": (
            "✅ *Ajajni kee milkaa'inaan ergame!*\n\n"
            "Gareen keenya ilalee dafee si quunnamti.\n"
            "ID Ajajaa: *#{order_id}*\n\n"
            "Haala ilaaluuf: /status"
        ),
        "cancelled": "Ajajni haquame. Deebi'uuf /start fayyadami.",
        "payment_msg": (
            "💳 *Kaffaltii Barbaachisaa — Gatii Tajaajilaa*\n\n"
            "Beellanni kee ni mirkanaaye! ✅\n\n"
            f"Maaloo gatii tajaajilaa *{SERVICE_FEE}* kana ergii:\n\n"
            f"📱 *TeleBirr:* `{TELEBIRR_NUMBER}`\n"
            f"📱 *M-Pesa:*   `{MPESA_NUMBER}`\n\n"
            "Ergin booda *screenshot kaffaltiikee* asitti ergi.\n"
            "⚠️ Kun gatii tajaajila keenyaaf qofa; gatii mootummaa hin hammatu."
        ),
        "payment_received": (
            "✅ *Kaffaltin mirkanaaye!*\n\n"
            "Beellaman kee guutummaatti qabsiifame.\n"
            "Sanadni mirkaneessa beellamaa dafee siif ergama."
        ),
        "reminder_msg": (
            "⏰ *Yaadachiisa Beellamaa!*\n\n"
            "Boru beellama paaspoortii qabda.\n\n"
            "📅 Guyyaa: *{date}*\n"
            "🕐 Yeroo: *{time}*\n"
            "📍 Bakka: *{location}*\n\n"
            "Daqiiqaa 15 duraan dhufuu yaali."
        ),
        "rate_msg": (
            "⭐ *Muuxannoon kee akkam ture?*\n\n"
            "Beellaman kee xumurameera! Yaada kee nuuf kenni.\n"
            "Tajaajila keenya madaali:"
        ),
        "rate_thanks": "🙏 Madaalii keetif galatoomi! Yaada kee fayyadamna.",
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
        InlineKeyboardButton("🇬🇧 English",   callback_data="lang_en"),
        InlineKeyboardButton("🇪🇹 አማርኛ",     callback_data="lang_am"),
        InlineKeyboardButton("Afaan Oromoo",  callback_data="lang_om"),
    ]])

def passport_type_keyboard(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(s(lang,"new_passport"), callback_data="type_new"),
        InlineKeyboardButton(s(lang,"renewal"),      callback_data="type_renewal"),
    ]])

def urgency_keyboard(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(s(lang,"urgent"),  callback_data="urgency_urgent"),
        InlineKeyboardButton(s(lang,"regular"), callback_data="urgency_regular"),
    ]])

def rating_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⭐ 1", callback_data="rate_1"),
        InlineKeyboardButton("⭐ 2", callback_data="rate_2"),
        InlineKeyboardButton("⭐ 3", callback_data="rate_3"),
        InlineKeyboardButton("⭐ 4", callback_data="rate_4"),
        InlineKeyboardButton("⭐ 5", callback_data="rate_5"),
    ]])

# ── /start ─────────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        STRINGS["en"]["welcome"], parse_mode="Markdown",
        reply_markup=lang_keyboard()
    )
    return LANG

async def lang_chosen(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    ctx.user_data["lang"] = lang
    await query.edit_message_text(s(lang,"ask_name"), parse_mode="Markdown")
    return NAME

# ── Order flow ─────────────────────────────────────────────────────────────────
async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang","en")
    ctx.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(s(lang,"ask_phone"), parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang","en")
    ctx.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(s(lang,"ask_city"), parse_mode="Markdown")
    return CITY

async def get_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang","en")
    ctx.user_data["city"] = update.message.text.strip()
    await update.message.reply_text(
        s(lang,"ask_passport_type"), parse_mode="Markdown",
        reply_markup=passport_type_keyboard(lang)
    )
    return PASSPORT_TYPE

async def get_passport_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang","en")
    ctx.user_data["passport_type"] = "New Passport" if query.data=="type_new" else "Renewal"
    await query.edit_message_text(
        s(lang,"ask_urgency"), parse_mode="Markdown",
        reply_markup=urgency_keyboard(lang)
    )
    return URGENCY

async def get_urgency(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang","en")
    ctx.user_data["urgency"] = "Urgent (1–3 days)" if query.data=="urgency_urgent" else "Regular (1–2 weeks)"
    ctx.user_data["photos"] = []
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(s(lang,"done_btn"))]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await query.message.reply_text(
        s(lang,"ask_photos"), parse_mode="Markdown", reply_markup=kb
    )
    return PHOTOS

async def collect_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        ctx.user_data.setdefault("photos",[]).append(update.message.photo[-1].file_id)
    elif update.message.document:
        ctx.user_data.setdefault("photos",[]).append(update.message.document.file_id)
    await update.message.reply_text(f"✅ {len(ctx.user_data['photos'])} photo(s) received. Send more or tap Done.")
    return PHOTOS

async def photos_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang","en")
    d = ctx.user_data
    summary = (
        f"{s(lang,'confirm_title')}"
        f"👤 *Name:* {d.get('name')}\n"
        f"📞 *Phone:* {d.get('phone')}\n"
        f"📍 *City:* {d.get('city')}\n"
        f"🛂 *Type:* {d.get('passport_type')}\n"
        f"⚡ *Urgency:* {d.get('urgency')}\n"
        f"📎 *Photos:* {len(d.get('photos',[]))} file(s)\n"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(s(lang,"confirm_btn"), callback_data="confirm_yes"),
        InlineKeyboardButton(s(lang,"edit_btn"),    callback_data="confirm_no"),
    ]])
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("👆 Review above and confirm:", reply_markup=kb)
    return CONFIRM

async def confirm_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang","en")
    if query.data == "confirm_no":
        await query.edit_message_text(s(lang,"cancelled"))
        return ConversationHandler.END
    d    = ctx.user_data
    user = update.effective_user
    order_id = save_order(
        telegram_id=user.id, username=user.username or "",
        name=d.get("name",""), phone=d.get("phone",""),
        city=d.get("city",""), passport_type=d.get("passport_type",""),
        urgency=d.get("urgency",""), photos=",".join(d.get("photos",[])),
        lang=lang
    )
    await notify_admin_new_order(ctx, order_id, user, d)
    msg = s(lang,"order_submitted").replace("{order_id}", str(order_id))
    await query.edit_message_text(msg, parse_mode="Markdown")
    return ConversationHandler.END

# ── Admin notification — new order ─────────────────────────────────────────────
async def notify_admin_new_order(ctx, order_id, user, d):
    if not ADMIN_ID:
        return
    text = (
        f"🔔 *New Order #{order_id}*\n\n"
        f"👤 {d.get('name')} | @{user.username or 'N/A'}\n"
        f"📞 {d.get('phone')}\n"
        f"📍 {d.get('city')}\n"
        f"🛂 {d.get('passport_type')} — {d.get('urgency')}\n"
        f"📎 {len(d.get('photos',[]))} photo(s)\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Processing", callback_data=f"admin_processing_{order_id}"),
        InlineKeyboardButton("✅ Approve & Request Payment", callback_data=f"admin_booked_{order_id}"),
    ],[
        InlineKeyboardButton("🎉 Complete",   callback_data=f"admin_completed_{order_id}"),
        InlineKeyboardButton("❌ Cancel",      callback_data=f"admin_cancelled_{order_id}"),
    ],[
        InlineKeyboardButton("📅 Set Appointment", callback_data=f"admin_setappt_{order_id}"),
        InlineKeyboardButton("📄 Send PDF",         callback_data=f"admin_sendpdf_{order_id}"),
    ]])
    await ctx.bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=kb)
    for photo_id in d.get("photos",[]):
        try:
            await ctx.bot.send_photo(ADMIN_ID, photo_id)
        except Exception:
            try:
                await ctx.bot.send_document(ADMIN_ID, photo_id)
            except Exception:
                pass

# ── Admin status button handler ────────────────────────────────────────────────
async def admin_status_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await query.answer("Not authorized.", show_alert=True)
        return
    await query.answer()

    data     = query.data  # e.g. admin_booked_12 or admin_setappt_12
    parts    = data.split("_")
    action   = parts[1]
    order_id = int(parts[2])
    order    = get_order_by_id(order_id)
    if not order:
        await query.edit_message_text("Order not found.")
        return

    customer_id = order["telegram_id"]
    lang        = order["lang"]

    # ── Set appointment flow ──────────────────────────────────────────────
    if action == "setappt":
        ctx.user_data["appt_order_id"] = order_id
        await query.message.reply_text(
            f"📅 Setting appointment for Order #{order_id}\n\n"
            "Enter *appointment date* (e.g. 2024-08-20):",
            parse_mode="Markdown"
        )
        return  # handled by set_appt_date conversation

    # ── Send PDF ──────────────────────────────────────────────────────────
    if action == "sendpdf":
        await send_appointment_pdf(ctx.bot, order, customer_id, lang)
        await query.answer("PDF sent to customer!", show_alert=True)
        return

    # ── Status updates ────────────────────────────────────────────────────
    status_map = {
        "processing": "processing",
        "booked":     "booked",
        "completed":  "completed",
        "cancelled":  "cancelled",
    }
    new_status = status_map.get(action)
    if not new_status:
        return

    update_order_status(order_id, new_status)
    status_label = STATUS_EMOJI.get(new_status, new_status)

    # Customer notification per status
    if new_status == "booked":
        # Send payment request
        await ctx.bot.send_message(
            customer_id,
            s(lang, "payment_msg"),
            parse_mode="Markdown"
        )
    elif new_status == "completed":
        # Send rating request
        await ctx.bot.send_message(
            customer_id,
            s(lang, "rate_msg"),
            parse_mode="Markdown",
            reply_markup=rating_keyboard()
        )
    elif new_status == "cancelled":
        cancel_msg = {
            "en": f"❌ *Order #{order_id} Cancelled*\n\nWe're sorry, your order has been cancelled. Please contact us for more information.",
            "am": f"❌ *ትዕዛዝ #{order_id} ተሰርዟል*\n\nይቅርታ፣ ትዕዛዝዎ ተሰርዟል። ለተጨማሪ መረጃ ያግኙን።",
            "om": f"❌ *Ajajni #{order_id} haquame*\n\nGabaabicha, ajajni kee haquame. Odeeffannoo dabalataa argachuuf nu quunnamaa.",
        }.get(lang, f"❌ Order #{order_id} cancelled.")
        await ctx.bot.send_message(customer_id, cancel_msg, parse_mode="Markdown")
    else:
        generic_msg = {
            "en": f"📬 *Order #{order_id} Update*\n\nStatus: *{status_label}*",
            "am": f"📬 *ትዕዛዝ #{order_id} ዝማኔ*\n\nሁኔታ: *{status_label}*",
            "om": f"📬 *Haaromsa Ajajaa #{order_id}*\n\nHaala: *{status_label}*",
        }.get(lang, f"📬 Order #{order_id}: *{status_label}*")
        await ctx.bot.send_message(customer_id, generic_msg, parse_mode="Markdown")

    await query.edit_message_text(
        f"✅ Order #{order_id} → *{status_label}*\nCustomer notified.",
        parse_mode="Markdown"
    )

# ── Payment screenshot handler ─────────────────────────────────────────────────
async def handle_payment_screenshot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Customer sends payment screenshot — forward to admin for verification."""
    user = update.effective_user
    # Check if user has a booked order awaiting payment
    orders = get_orders_by_telegram_id(user.id)
    booked_unpaid = [o for o in orders if o["status"]=="booked" and o["payment_status"]=="unpaid"]
    if not booked_unpaid:
        return  # not a payment screenshot, ignore

    order = booked_unpaid[0]
    order_id = order["id"]
    lang     = order["lang"]

    # Forward screenshot to admin
    caption = (
        f"💳 *Payment Screenshot*\n"
        f"Order #{order_id} — {order['name']}\n"
        f"📞 {order['phone']}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirm Payment", callback_data=f"pay_confirm_{order_id}"),
        InlineKeyboardButton("❌ Reject",           callback_data=f"pay_reject_{order_id}"),
    ]])

    if update.message.photo:
        await ctx.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id,
                                 caption=caption, parse_mode="Markdown", reply_markup=kb)
    elif update.message.document:
        await ctx.bot.send_document(ADMIN_ID, update.message.document.file_id,
                                    caption=caption, parse_mode="Markdown", reply_markup=kb)

    await update.message.reply_text(
        "📤 Your payment screenshot has been sent to our team for verification. "
        "We'll confirm shortly!",
        parse_mode="Markdown"
    )

async def admin_payment_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await query.answer("Not authorized.", show_alert=True)
        return
    await query.answer()

    parts    = query.data.split("_")
    action   = parts[1]   # confirm or reject
    order_id = int(parts[2])
    order    = get_order_by_id(order_id)
    if not order:
        await query.edit_message_text("Order not found.")
        return

    customer_id = order["telegram_id"]
    lang        = order["lang"]

    if action == "confirm":
        update_order_payment(order_id, "paid")
        await ctx.bot.send_message(
            customer_id, s(lang, "payment_received"), parse_mode="Markdown"
        )
        # Auto-send PDF if appointment details exist
        if order.get("appointment_date"):
            await send_appointment_pdf(ctx.bot, order, customer_id, lang)
        await query.edit_message_text(
            f"✅ Payment confirmed for Order #{order_id}. Customer notified."
        )
    else:
        await ctx.bot.send_message(
            customer_id,
            "❌ Payment could not be verified. Please resend a clear screenshot or contact us.",
            parse_mode="Markdown"
        )
        await query.edit_message_text(f"❌ Payment rejected for Order #{order_id}.")

# ── Set appointment conversation ───────────────────────────────────────────────
async def admin_set_appt_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin command: /setappt <order_id>"""
    if update.effective_user.id != ADMIN_ID:
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /setappt <order_id>")
        return ConversationHandler.END
    ctx.user_data["appt_order_id"] = int(args[0])
    await update.message.reply_text(
        f"📅 Setting appointment for Order #{args[0]}\n\nEnter *date* (YYYY-MM-DD):",
        parse_mode="Markdown"
    )
    return APPT_DATE

async def appt_get_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["appt_date"] = update.message.text.strip()
    await update.message.reply_text("🕐 Enter *appointment time* (e.g. 09:30 AM):", parse_mode="Markdown")
    return APPT_TIME

async def appt_get_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["appt_time"] = update.message.text.strip()
    await update.message.reply_text("📍 Enter *appointment location* (e.g. Immigration Office, Addis Ababa):", parse_mode="Markdown")
    return APPT_LOCATION

async def appt_get_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    order_id = ctx.user_data.get("appt_order_id")
    date     = ctx.user_data.get("appt_date")
    time     = ctx.user_data.get("appt_time")
    location = update.message.text.strip()

    update_appointment_details(order_id, date, time, location)
    order = get_order_by_id(order_id)
    lang  = order["lang"]

    # Notify customer
    reminder = s(lang,"reminder_msg").replace("{date}", date).replace("{time}", time).replace("{location}", location)
    appt_notify = {
        "en": f"📅 *Appointment Confirmed — Order #{order_id}*\n\n📅 Date: *{date}*\n🕐 Time: *{time}*\n📍 Location: *{location}*",
        "am": f"📅 *ቀጠሮ ተረጋግጧል — ትዕዛዝ #{order_id}*\n\n📅 ቀን: *{date}*\n🕐 ሰዓት: *{time}*\n📍 ቦታ: *{location}*",
        "om": f"📅 *Beellama Mirkanaaye — Ajajaa #{order_id}*\n\n📅 Guyyaa: *{date}*\n🕐 Yeroo: *{time}*\n📍 Bakka: *{location}*",
    }.get(lang)

    await ctx.bot.send_message(order["telegram_id"], appt_notify, parse_mode="Markdown")

    # Auto-send PDF
    await send_appointment_pdf(ctx.bot, get_order_by_id(order_id), order["telegram_id"], lang)

    await update.message.reply_text(
        f"✅ Appointment set for Order #{order_id}.\nCustomer notified + PDF sent.",
    )
    return ConversationHandler.END

# ── PDF sender ─────────────────────────────────────────────────────────────────
async def send_appointment_pdf(bot, order, customer_id, lang):
    try:
        pdf_bytes = generate_appointment_pdf(order)
        pdf_file  = InputFile(BytesIO(pdf_bytes), filename=f"Appointment_#{order['id']}.pdf")
        caption   = {
            "en": "📄 Your appointment confirmation is attached. Please bring this (printed or on phone) to your appointment.",
            "am": "📄 የቀጠሮ ማረጋገጫ ሰነድ ተያይዟል። ወደ ቀጠሮ ሲሄዱ ይዘው ይምጡ።",
            "om": "📄 Sanadni mirkaneessa beellamaa siif ergame. Beellamaaf yoo dhuftu fudhachuu yaadhu.",
        }.get(lang, "📄 Appointment confirmation attached.")
        await bot.send_document(customer_id, pdf_file, caption=caption)
    except Exception as e:
        logger.error(f"Failed to send PDF: {e}")

# ── Rating handler ─────────────────────────────────────────────────────────────
async def handle_rating(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rating   = int(query.data.split("_")[1])
    user_id  = update.effective_user.id

    orders = get_orders_by_telegram_id(user_id)
    completed = [o for o in orders if o["status"]=="completed"]
    if completed:
        save_rating(completed[0]["id"], rating)
        lang = completed[0]["lang"]
    else:
        lang = "en"

    stars = "⭐" * rating
    await query.edit_message_text(
        f"{stars}\n\n{s(lang,'rate_thanks')}",
        parse_mode="Markdown"
    )
    # Notify admin of rating
    if ADMIN_ID:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"⭐ New rating: *{rating}/5* from {update.effective_user.first_name}",
            parse_mode="Markdown"
        )

# ── /status command ────────────────────────────────────────────────────────────
async def my_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    orders = get_orders_by_telegram_id(update.effective_user.id)
    if not orders:
        await update.message.reply_text("No orders yet. Use /start to place one.")
        return
    text = "📋 *Your Orders:*\n\n"
    for o in orders:
        status_label  = STATUS_EMOJI.get(o["status"], o["status"])
        payment_label = "✅ Paid" if o.get("payment_status")=="paid" else "⏳ Unpaid"
        appt = f"\n  📅 Appt: {o['appointment_date']} {o.get('appointment_time','')}" if o.get("appointment_date") else ""
        text += (
            f"*Order #{o['id']}*\n"
            f"  {o['passport_type']} | {o['urgency']}\n"
            f"  Status: {status_label}\n"
            f"  Payment: {payment_label}{appt}\n"
            f"  Date: {o['created_at'][:10]}\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# ── Admin commands ─────────────────────────────────────────────────────────────
async def admin_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    orders = get_all_orders(limit=10)
    if not orders:
        await update.message.reply_text("No orders yet.")
        return
    text = "📋 *Last 10 Orders:*\n\n"
    for o in orders:
        status_label  = STATUS_EMOJI.get(o["status"], o["status"])
        payment_label = "✅" if o.get("payment_status")=="paid" else "💳"
        text += (
            f"*#{o['id']}* {payment_label} — {o['name']} | {o['phone']}\n"
            f"  {o['passport_type']} | {o['urgency']} | {o['city']}\n"
            f"  {status_label} | {o['created_at'][:16]}\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin: /search <phone>"""
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /search <phone number>")
        return
    phone  = ctx.args[0]
    orders = search_orders_by_phone(phone)
    if not orders:
        await update.message.reply_text("No orders found for that phone number.")
        return
    text = f"🔍 *Results for {phone}:*\n\n"
    for o in orders:
        status_label = STATUS_EMOJI.get(o["status"], o["status"])
        text += (
            f"*#{o['id']}* — {o['name']}\n"
            f"  {o['passport_type']} | {o['city']}\n"
            f"  {status_label} | {o['created_at'][:10]}\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_broadcast_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin: /broadcast — sends a message to ALL customers."""
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text(
        "📢 *Broadcast to all customers*\n\n"
        "Type your message below. It will be sent to all users who have ever placed an order.\n\n"
        "Send /cancel to abort.",
        parse_mode="Markdown"
    )
    return BROADCAST_MSG

async def do_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg      = update.message.text
    user_ids = get_all_customer_ids()
    sent = failed = 0
    for uid in user_ids:
        try:
            await ctx.bot.send_message(uid, f"📢 *Message from Ethio Online Passport Service:*\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"✅ Broadcast done.\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )
    return ConversationHandler.END

# ── Reminder scheduler ─────────────────────────────────────────────────────────
async def send_reminders(app: Application):
    orders = get_orders_needing_reminder()
    for order in orders:
        lang = order["lang"]
        msg  = s(lang,"reminder_msg").format(
            date=order.get("appointment_date",""),
            time=order.get("appointment_time",""),
            location=order.get("appointment_location","")
        )
        try:
            await app.bot.send_message(order["telegram_id"], msg, parse_mode="Markdown")
            mark_reminder_sent(order["id"])
            logger.info(f"Reminder sent for order #{order['id']}")
        except Exception as e:
            logger.error(f"Reminder failed for order #{order['id']}: {e}")

# ── Daily marketing ────────────────────────────────────────────────────────────
async def post_daily_marketing(app: Application):
    post = get_daily_post()
    try:
        await app.bot.send_message(
            CHANNEL_ID, post, parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info("Daily marketing post sent.")
    except Exception as e:
        logger.error(f"Marketing post failed: {e}")

async def manual_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await post_daily_marketing(ctx.application)
    await update.message.reply_text("✅ Marketing post sent.")

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang","en")
    await update.message.reply_text(s(lang,"cancelled"), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Order conversation
    order_conv = ConversationHandler(
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

    # Appointment setting conversation (admin)
    appt_conv = ConversationHandler(
        entry_points=[CommandHandler("setappt", admin_set_appt_start)],
        states={
            APPT_DATE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, appt_get_date)],
            APPT_TIME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, appt_get_time)],
            APPT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, appt_get_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Broadcast conversation (admin)
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", admin_broadcast_start)],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(order_conv)
    app.add_handler(appt_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(CommandHandler("status",   my_status))
    app.add_handler(CommandHandler("orders",   admin_orders))
    app.add_handler(CommandHandler("search",   admin_search))
    app.add_handler(CommandHandler("post",     manual_post))
    app.add_handler(CallbackQueryHandler(admin_status_button,  pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_payment_button, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(handle_rating,        pattern="^rate_"))
    # Payment screenshot — photos/docs from non-admin users
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.ALL) & ~filters.User(ADMIN_ID),
        handle_payment_screenshot
    ))

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: asyncio.create_task(post_daily_marketing(app)),
        trigger="cron", hour=9, minute=0, timezone="Africa/Addis_Ababa"
    )
    scheduler.add_job(
        lambda: asyncio.create_task(send_reminders(app)),
        trigger="cron", hour=8, minute=0, timezone="Africa/Addis_Ababa"
    )
    scheduler.start()

    logger.info("Bot started.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
