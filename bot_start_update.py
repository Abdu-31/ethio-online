# ── Add this to bot.py ────────────────────────────────────────────────────────
# Replace your existing /start handler with this version.
# It adds a "Open Mini App" button below the language selector.

from telegram import WebAppInfo

MINIAPP_URL = os.getenv("MINIAPP_URL", "https://abdu-31.github.io/passport-miniapp")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()

    # Mini App button
    miniapp_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🛂 Open Passport Service App",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ],[
        InlineKeyboardButton("🇬🇧 English",    callback_data="lang_en"),
        InlineKeyboardButton("🇪🇹 አማርኛ",      callback_data="lang_am"),
        InlineKeyboardButton("Afaan Oromoo",   callback_data="lang_om"),
    ]])

    await update.message.reply_text(
        "🛂 *Ethiopia Passport Service*\n\n"
        "Tap the button below to open our app, or choose your language to order via chat:",
        parse_mode="Markdown",
        reply_markup=miniapp_kb
    )
    return LANG

# ── Also add MINIAPP_URL to your .env ─────────────────────────────────────────
# MINIAPP_URL=https://abdu-31.github.io/passport-miniapp
