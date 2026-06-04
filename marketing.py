"""
marketing.py — Daily rotating post content in EN / AM / OM
Posts cycle through 5 themes: price, availability, turnaround, testimonial, CTA
"""
from datetime import date

# ── Contact info (edit these) ──────────────────────────────────────────────────
CHANNEL_LINK  = "https://t.me/your_channel"
BOT_LINK      = "https://t.me/your_bot_username"
PHONE_DISPLAY = "+251 91 234 5678"

# ── 5 content themes, each with EN / AM / OM ──────────────────────────────────
POSTS = [
    # ── Theme 0: Service Price ──────────────────────────────────────────────
    {
        "en": (
            "🛂 *Ethiopia Passport Appointment Service*\n\n"
            "💰 *Our Service Fees:*\n"
            "• New Passport (Regular) — 500 ETB\n"
            "• New Passport (Urgent)  — 900 ETB\n"
            "• Renewal (Regular)      — 400 ETB\n"
            "• Renewal (Urgent)       — 800 ETB\n\n"
            "✅ We book your appointment. You just show up.\n"
            "📲 Start your order now 👇\n"
            f"{BOT_LINK}"
        ),
        "am": (
            "🛂 *የፓስፖርት ቀጠሮ አገልግሎት — ኢትዮጵያ*\n\n"
            "💰 *የአገልግሎት ዋጋ:*\n"
            "• አዲስ ፓስፖርት (መደበኛ) — 500 ብር\n"
            "• አዲስ ፓስፖርት (አስቸኳይ) — 900 ብር\n"
            "• ታደሰ (መደበኛ)          — 400 ብር\n"
            "• ታደሰ (አስቸኳይ)         — 800 ብር\n\n"
            "✅ ቀጠሮዎን እናስያዝልዎታለን። እርስዎ ቦታው ላይ ብቻ ይቅረቡ።\n"
            "📲 አሁን ትዕዛዝ ይስጡ 👇\n"
            f"{BOT_LINK}"
        ),
        "om": (
            "🛂 *Tajaajila Beellama Paaspoortii — Itoophiyaa*\n\n"
            "💰 *Gatii Tajaajilaa:*\n"
            "• Paaspoortii Haaraa (Idilee) — Birr 500\n"
            "• Paaspoortii Haaraa (Ariif.)  — Birr 900\n"
            "• Haaromsa (Idilee)             — Birr 400\n"
            "• Haaromsa (Ariifachiisaa)      — Birr 800\n\n"
            "✅ Beellama ni qabsiifna. Ati bakka dhaquuf qofa deemi.\n"
            "📲 Ajaja kee amma kennii 👇\n"
            f"{BOT_LINK}"
        ),
    },

    # ── Theme 1: Appointment Availability ──────────────────────────────────
    {
        "en": (
            "📅 *Passport Appointments Available NOW!*\n\n"
            "🟢 Slots open for:\n"
            "• Addis Ababa\n"
            "• Jimma\n"
            "• Dire Dawa\n"
            "• Adama & more cities\n\n"
            "⚡ Urgent slots fill up fast — don't wait!\n"
            "📲 Book yours today 👇\n"
            f"{BOT_LINK}"
        ),
        "am": (
            "📅 *አሁን ቀጠሮ ይስሩ!*\n\n"
            "🟢 ለሚከተሉት ከተሞች ክፍት ቦታ አለ:\n"
            "• አዲስ አበባ\n"
            "• ጅማ\n"
            "• ድሬዳዋ\n"
            "• አዳማ እና ሌሎች ከተሞች\n\n"
            "⚡ አስቸኳይ ቦታዎች ፈጥኖ ይሞላሉ — አይዘግዩ!\n"
            "📲 ዛሬ ቀጠሮ ያስይዙ 👇\n"
            f"{BOT_LINK}"
        ),
        "om": (
            "📅 *Beellama Amma Argama!*\n\n"
            "🟢 Bakkeewwan banaa kan jiran:\n"
            "• Finfinnee\n"
            "• Jimmaa\n"
            "• Dire Dawa\n"
            "• Adaamaa fi magaalota biroo\n\n"
            "⚡ Bakkeewwan ariifachiisaa dafanii guutamu — hin turin!\n"
            "📲 Beellama kee har'a qabsiifadhu 👇\n"
            f"{BOT_LINK}"
        ),
    },

    # ── Theme 2: Turnaround Time ────────────────────────────────────────────
    {
        "en": (
            "⏱️ *Fast Passport Appointments — How It Works*\n\n"
            "1️⃣ Send your info via our bot\n"
            "2️⃣ We confirm & book your appointment\n"
            "3️⃣ You get your appointment date within:\n\n"
            "   🔴 *Urgent:*  1–3 business days\n"
            "   🟢 *Regular:* 1–2 weeks\n\n"
            "No queues. No stress. Just results. ✅\n"
            "📲 Start now 👇\n"
            f"{BOT_LINK}"
        ),
        "am": (
            "⏱️ *ፈጣን የፓስፖርት ቀጠሮ — እንዴት ይሰራል?*\n\n"
            "1️⃣ መረጃዎን ወደ ቦቱ ይላኩ\n"
            "2️⃣ እናረጋግጣለን እና ቀጠሮ እናስያዝልዎታለን\n"
            "3️⃣ የቀጠሮ ቀንዎ ይደርስዎታል:\n\n"
            "   🔴 *አስቸኳይ:*  1–3 የስራ ቀናት\n"
            "   🟢 *መደበኛ:* 1–2 ሳምንት\n\n"
            "ምንም ወረፋ አይደለም። ምንም ጭንቀት አይደለም። ✅\n"
            "📲 አሁን ይጀምሩ 👇\n"
            f"{BOT_LINK}"
        ),
        "om": (
            "⏱️ *Beellama Paaspoortii Ariifataa — Akkamitti Hojjata?*\n\n"
            "1️⃣ Odeeffannoo kee bot keenyatti ergi\n"
            "2️⃣ Mirkaneessina fi beellama ni qabsiifna\n"
            "3️⃣ Guyyaa beellamaa kee argatta:\n\n"
            "   🔴 *Ariifachiisaa:* Guyyaa hojii 1–3\n"
            "   🟢 *Idilee:*        Torbee 1–2\n\n"
            "Sarara hin jiru. Yaaddoo hin jiru. ✅\n"
            "📲 Amma jalqabi 👇\n"
            f"{BOT_LINK}"
        ),
    },

    # ── Theme 3: Testimonial ────────────────────────────────────────────────
    {
        "en": (
            "⭐ *What Our Customers Say*\n\n"
            "❝ I got my appointment in just 2 days. Super fast and easy! ❞\n"
            "— Fatuma A., Jimma\n\n"
            "❝ I was stressed about the process. They handled everything. ❞\n"
            "— Bekele T., Addis Ababa\n\n"
            "❝ Very professional. Will definitely use again! ❞\n"
            "— Chaltu M., Adama\n\n"
            "📲 Join 700+ happy customers 👇\n"
            f"{BOT_LINK}"
        ),
        "am": (
            "⭐ *ደንበኞቻችን ምን ይላሉ?*\n\n"
            "❝ ቀጠሮዬን በ2 ቀናት አገኘሁ። በጣም ፈጣን ነው! ❞\n"
            "— ፋጡማ አ.፣ ጅማ\n\n"
            "❝ ሁሉንም ነገር ለኔ አስተናገዱ። ምንም ጭንቀት አልነበረም። ❞\n"
            "— በቀለ ተ.፣ አዲስ አበባ\n\n"
            "❝ በጣም ሙያዊ አገልግሎት ነው። ዳግም እጠቀማቸዋለሁ! ❞\n"
            "— ጫልቱ ም.፣ አዳማ\n\n"
            "📲 ከ700+ ደስተኛ ደንበኞቻችን ይቀላቀሉ 👇\n"
            f"{BOT_LINK}"
        ),
        "om": (
            "⭐ *Maamiltoonni Keenya Maal Jedhu?*\n\n"
            "❝ Guyyaa 2 keessatti beellama argadhe. Baay'ee ariifataa! ❞\n"
            "— Faaxumaa A., Jimmaa\n\n"
            "❝ Hunda naaf hojjatan. Yaaddoo tokkollee hin qabu ture. ❞\n"
            "— Baqqalaa T., Finfinnee\n\n"
            "❝ Baay'ee ogummaa qaba. Irra deebi'ee fayyadama! ❞\n"
            "— Caaltuu M., Adaamaa\n\n"
            "📲 Maamiltota 700+ gammadoo waliin makkami 👇\n"
            f"{BOT_LINK}"
        ),
    },

    # ── Theme 4: Strong CTA ─────────────────────────────────────────────────
    {
        "en": (
            "🇪🇹 *Need a Passport Appointment?*\n\n"
            "We handle it for you — fast, reliable, and affordable.\n\n"
            "✅ New passports\n"
            "✅ Renewals\n"
            "✅ Urgent & regular slots\n"
            "✅ Any city in Ethiopia\n\n"
            "📞 Call/WhatsApp: " + PHONE_DISPLAY + "\n"
            "📲 Order via bot 👇\n"
            f"{BOT_LINK}"
        ),
        "am": (
            "🇪🇹 *የፓስፖርት ቀጠሮ ያስፈልጎታልን?*\n\n"
            "ለእርስዎ እናስተናግዳለን — ፈጣን፣ ታማኝ እና ተመጣጣኝ ዋጋ።\n\n"
            "✅ አዲስ ፓስፖርቶች\n"
            "✅ ታደሰ\n"
            "✅ አስቸኳይ እና መደበኛ ቀጠሮዎች\n"
            "✅ በኢትዮጵያ ማንኛውም ከተማ\n\n"
            "📞 ይደውሉ/ዋትስአፕ: " + PHONE_DISPLAY + "\n"
            "📲 ቦቱ ላይ ትዕዛዝ ይስጡ 👇\n"
            f"{BOT_LINK}"
        ),
        "om": (
            "🇪🇹 *Beellama Paaspoortii Barbaaddaa?*\n\n"
            "Siif hojjanna — ariifataa, amanamaa, fi gatii madaalawaa.\n\n"
            "✅ Paaspoortii haaraa\n"
            "✅ Haaromsa\n"
            "✅ Bakkeewwan ariifachiisaa fi idilee\n"
            "✅ Magaalaa kamiiyyuu Itoophiyaa keessatti\n\n"
            "📞 Bilbili/WhatsApp: " + PHONE_DISPLAY + "\n"
            "📲 Bot irratti ajaji 👇\n"
            f"{BOT_LINK}"
        ),
    },
]

def get_daily_post() -> str:
    """Rotate through 5 themes based on day of year, post all 3 languages."""
    day_index = date.today().timetuple().tm_yday
    theme = POSTS[day_index % len(POSTS)]
    return (
        f"{theme['en']}\n\n"
        "──────────────────\n\n"
        f"{theme['am']}\n\n"
        "──────────────────\n\n"
        f"{theme['om']}"
    )
