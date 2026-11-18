# 🔑 Complete Credentials & Setup Guide

This guide walks you step-by-step through obtaining every credential needed to launch your **Telegram Mini App Gmail Assistant** for live users.

---

## 1. Telegram Bot Token (1 Minute)

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot`.
3. Choose a name (e.g. `Smart Gmail Assistant`) and a unique username ending in `bot` (e.g. `MySmartGmailAiBot`).
4. BotFather will provide an **HTTP API Token** (e.g. `7812345678:AAH...`).
5. Copy this into `.env` as `TELEGRAM_BOT_TOKEN`.

### Enabling the Telegram Mini App Menu Button:
1. In [@BotFather](https://t.me/BotFather), send `/mybots` $\rightarrow$ select your bot.
2. Click **Bot Settings** $\rightarrow$ **Menu Button** $\rightarrow$ **Configure menu button**.
3. When asked for the URL, send your app URL:
   - For local dev: `https://your-ngrok-url/connect`
   - For live deployment: `https://your-app-domain.com/connect`
4. Set button text: `📬 Connect Gmail`.

---

## 2. Google OAuth Credentials (3 Minutes)

Google OAuth allows users to click "Sign in with Google" and securely grant read-only access to their Primary inbox.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g. `Telegram Gmail Assistant`).
3. **Enable Gmail API**:
   - Go to **APIs & Services** $\rightarrow$ **Library**.
   - Search for **Gmail API** $\rightarrow$ Click **Enable**.
4. **Configure OAuth Consent Screen**:
   - Go to **APIs & Services** $\rightarrow$ **OAuth consent screen**.
   - Choose **External** $\rightarrow$ Click **Create**.
   - Fill in:
     - **App name**: `Telegram Gmail Assistant`
     - **User support email**: Your email.
     - **Developer contact information**: Your email.
   - Click **Save and Continue**.
   - In **Scopes**, click **Add or Remove Scopes** and add:
     - `.../auth/gmail.readonly` (Read resources from Gmail)
     - `.../auth/userinfo.email` (See user's email address)
   - Click **Save and Continue** $\rightarrow$ Under **Test Users**, add your own email for testing.
5. **Create OAuth Client ID**:
   - Go to **APIs & Services** $\rightarrow$ **Credentials**.
   - Click **+ Create Credentials** $\rightarrow$ **OAuth client ID**.
   - **Application type**: `Web application`.
   - **Name**: `Telegram Mini App Client`.
   - **Authorized redirect URIs**:
     - For local development: `http://localhost:8000/api/auth/callback`
     - For your public domain: `https://your-domain.com/api/auth/callback`
   - Click **Create**.
6. Google will display your **Client ID** and **Client Secret**.
7. Copy them into `.env`:
   - `GOOGLE_CLIENT_ID=...`
   - `GOOGLE_CLIENT_SECRET=...`

---

## 3. Google Gemini API Key (30 Seconds)

Gemini Flash generates the crisp, noise-free mobile Telegram briefing.

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key**.
3. Click **Create API key in new project**.
4. Copy the key into `.env` as `GEMINI_API_KEY`.

---

## 4. Database Setup (Zero Setup locally, Supabase for Production)

* **Local Development**: You don't need any database keys! The app will automatically create and use a local SQLite file (`users.db`).
* **Production Deployment (Supabase)**:
  1. Go to [Supabase](https://supabase.com/) and create a free project.
  2. Go to the **SQL Editor** and run:
     ```sql
     CREATE TABLE users (
         telegram_id TEXT PRIMARY KEY,
         google_email TEXT,
         google_refresh_token TEXT NOT NULL,
         created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
         updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
     );
     ```
  3. Go to **Project Settings** $\rightarrow$ **API**.
  4. Copy **Project URL** into `SUPABASE_URL` and **anon/public key** into `SUPABASE_KEY` in `.env`.

---

## 5. Running the Application

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`:
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 3. Start the Server & Bot:
```bash
python run_server.py
```
* The FastAPI server starts on `http://localhost:8000`.
* The Telegram bot starts listening in the background automatically.
* Users can open your bot on Telegram, click **"Connect Gmail"**, and send **"i want email"**!
