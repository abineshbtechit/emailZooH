# 📬 Telegram AI Gmail Assistant (Multi-Tenant Mini App)

A complete, live-ready application that lets **any user** connect their Gmail inside Telegram via a **Telegram Mini App** and receive clean, noise-free, AI-powered unread **Primary** email briefings on demand.

---

## 🌟 Highlights

- **Native Telegram Mini App**: Runs directly inside Telegram on mobile and desktop — users never download or install another app.
- **1-Click Google OAuth**: Users tap *"Connect My Gmail"* and sign in with Google directly inside the Telegram webview.
- **Strict RFC Primary Inbox Filter**: Inspects email headers and drops 100% of newsletters, automated spam, promotional campaigns (`List-Unsubscribe`, `Feedback-ID`, `Precedence: bulk`), isolating only genuine human/primary messages.
- **Gemini Flash AI Summarization**: Blazing fast, intelligent synthesis into clean Telegram cards:
  - 🔴 **Action Required** (Deadlines, decisions, replies needed)
  - 🟢 **General Messages** (One-sentence summaries)
- **Multi-Tenant Ready**: Each user's tokens are isolated and mapped to their unique Telegram Chat ID.
- **Zero-Setup Local Dev**: Works immediately with built-in SQLite database and Telegram long-polling (no ngrok required to start testing).

---

## 🏗️ Project Architecture

```
gmail-updates/
├── frontend/
│   └── index.html               # Telegram Mini App UI (Mobile-responsive, Telegram WebApp SDK)
├── backend/
│   ├── app.py                   # FastAPI server (OAuth flow, webhooks, Mini App hosting)
│   ├── config.py                # Environment & settings configuration
│   ├── database.py              # SQLite (local) + Supabase (production) engine
│   ├── gmail_service.py         # Google OAuth & strict Primary unread email filter
│   ├── ai_service.py            # Gemini AI summarizer (clean Telegram Markdown format)
│   ├── telegram_service.py      # Telegram Bot API client (buttons, messages)
│   └── bot_polling.py           # Local polling engine (run without public webhook)
├── .env.example                 # Environment variables template
├── requirements.txt             # Python dependencies
├── run_server.py                # Unified one-command runner
├── CREDENTIALS_GUIDE.md         # Step-by-step instructions for getting all keys
└── README.md                    # Project documentation
```

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in the 3 essential keys (see [CREDENTIALS_GUIDE.md](file:///d:/projects/ZOOH%20-%20nextLen/gmail-updates/CREDENTIALS_GUIDE.md)):
- `TELEGRAM_BOT_TOKEN`
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`
- `GEMINI_API_KEY`

### 3. Run the App
```bash
python run_server.py
```
- FastAPI server runs on `http://localhost:8000`.
- Telegram bot starts listening automatically.
