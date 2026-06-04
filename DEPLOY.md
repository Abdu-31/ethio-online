# 🛂 Passport Mini App — Full Deployment Guide

## Architecture
```
Telegram Bot (Render)  ←→  FastAPI Backend (Render)  ←→  SQLite DB
                                    ↑
                         React Mini App (GitHub Pages)
                                    ↑
                              Telegram User
```

---

## Part 1 — Deploy Backend API on Render

### Step 1: Add these files to your GitHub repo
Copy from this folder into your bot repo root:
- `api.py`
- `requirements.txt` (replace the old one)
- `bot_start_update.py` (use the `start()` function inside to replace yours in `bot.py`)

### Step 2: Create TWO services on Render from the same repo

**Service 1 — Bot (already exists or create new)**
- Type: Web Service
- Start Command: `python bot.py`
- Environment vars: BOT_TOKEN, CHANNEL_ID, ADMIN_ID, MINIAPP_URL

**Service 2 — API**
- Type: Web Service  
- Start Command: `uvicorn api:app --host 0.0.0.0 --port 8000`
- Environment vars: BOT_TOKEN, ADMIN_ID

After deploying Service 2, copy its URL — it will look like:
`https://passport-api-xxxx.onrender.com`

---

## Part 2 — Deploy Mini App on GitHub Pages

### Step 1: Create a new GitHub repo
Name it `passport-miniapp` under your account (abdu-31).

### Step 2: Add environment file
Create `.env` in the miniapp folder:
```
REACT_APP_API_URL=https://passport-api-xxxx.onrender.com
REACT_APP_ADMIN_ID=your_numeric_telegram_id
```

### Step 3: Update package.json homepage
In `package.json`, change:
```json
"homepage": "https://abdu-31.github.io/passport-miniapp"
```

### Step 4: Install and deploy
```bash
cd passport_miniapp
npm install
npm run deploy
```
This builds React and pushes to GitHub Pages automatically.

Your Mini App URL will be:
`https://abdu-31.github.io/passport-miniapp`

---

## Part 3 — Connect Bot to Mini App

### Step 1: Register Mini App with BotFather
1. Open @BotFather
2. Send `/newapp`
3. Choose your bot
4. Set URL: `https://abdu-31.github.io/passport-miniapp`
5. Upload an icon (512x512 PNG)

### Step 2: Add MINIAPP_URL to Render env vars
```
MINIAPP_URL=https://abdu-31.github.io/passport-miniapp
```

### Step 3: Update bot.py
Replace the `start()` function with the one in `bot_start_update.py`

---

## What users see
1. User sends `/start` to bot
2. Bot shows "Open Passport Service App" button
3. User taps → Mini App opens inside Telegram
4. User fills form in their language → submits
5. You get notified in admin chat
6. You update status → user sees it on "My Orders" tab

---

## Mini App screens
| Tab | Who sees it | What it does |
|-----|------------|--------------|
| New Order | Everyone | Trilingual order form with photo upload |
| My Orders | Everyone | Order history with live status timeline |
| Admin | Admin only | Stats dashboard, all orders, status updates |
