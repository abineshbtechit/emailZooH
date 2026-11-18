import os
from pathlib import Path
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from backend.config import settings
from backend.database import db
from backend.gmail_service import (
    get_google_auth_url,
    exchange_code_for_tokens,
    fetch_unread_primary_emails
)
from backend.ai_service import summarize_emails_with_gemini
from backend.telegram_service import send_telegram_message, get_connect_keyboard

app = FastAPI(title=settings.APP_NAME)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/")
def home():
    return {"status": "running", "app": settings.APP_NAME, "version": "1.0.0"}

@app.get("/api/set-webhook")
async def set_telegram_webhook(request: Request):
    """Helper endpoint to register the Telegram webhook on Vercel."""
    import httpx
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"error": "TELEGRAM_BOT_TOKEN is not set"}
    base_url = settings.BASE_URL or str(request.base_url).rstrip("/")
    webhook_url = f"{base_url}/api/webhook/telegram"
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()

@app.get("/privacy", response_class=HTMLResponse)
def serve_privacy_page():
    html_file = FRONTEND_DIR / "privacy.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse("""
    <!DOCTYPE html><html><head><title>Privacy Policy</title></head>
    <body style="font-family:sans-serif;max-width:600px;margin:40px auto;line-height:1.6">
    <h1>Privacy Policy - emailZooH</h1>
    <p>emailZooH requests read-only access to Gmail (gmail.readonly) solely to fetch unread primary emails on-demand. We do not store or share your email contents.</p>
    </body></html>
    """)

@app.get("/connect", response_class=HTMLResponse)
def serve_connect_page():
    """Serves the Telegram Mini App HTML page."""
    html_file = FRONTEND_DIR / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse("""
    <!DOCTYPE html><html><head><title>Connect Gmail</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script></head>
    <body style="font-family:sans-serif;text-align:center;padding:40px">
    <h2>Connect Gmail</h2><p>Please authorize Gmail to receive AI briefings.</p>
    <a id="btn" style="display:inline-block;padding:12px 24px;background:#2563eb;color:#fff;text-decoration:none;border-radius:8px">Sign in with Google</a>
    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) tg.expand();
      const tid = tg?.initDataUnsafe?.user?.id || new URLSearchParams(window.location.search).get("telegram_id") || "test";
      document.getElementById("btn").href = `/api/auth/google?telegram_id=${tid}`;
    </script>
    </body></html>
    """)

@app.get("/api/auth/google")
def google_auth_start(telegram_id: str = Query(..., description="User's Telegram ID")):
    """Redirects user to Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        return HTMLResponse("<h3>Error: GOOGLE_CLIENT_ID is not configured in .env</h3>", status_code=500)
    auth_url = get_google_auth_url(telegram_id)
    return RedirectResponse(auth_url)

@app.get("/api/auth/callback")
async def google_auth_callback(code: str = Query(...), state: str = Query(...)):
    """
    Handles Google OAuth redirect:
    1. Exchanges code for tokens.
    2. Saves refresh token in database for this telegram_id.
    3. Sends instant confirmation message in Telegram chat.
    4. Automatically closes the Telegram Mini App.
    """
    telegram_id = state
    try:
        tokens, google_email = exchange_code_for_tokens(code)
        refresh_token = tokens.get("refresh_token") or tokens.get("access_token")

        # Save to database
        db.save_user(telegram_id=telegram_id, refresh_token=refresh_token, google_email=google_email)

        # Notify user inside Telegram chat
        confirmation_text = (
            f"🎉 *Gmail Connected Successfully!*\n\n"
            f"Linked account: `{google_email or 'Your Gmail'}`\n\n"
            f"Send *\"i want email\"* anytime to get your unread Primary inbox briefing!"
        )
        send_telegram_message(telegram_id, confirmation_text)

        # Return closing view for Telegram Mini App
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <script src="https://telegram.org/js/telegram-web-app.js"></script>
          <style>
            body {{ font-family: -apple-system, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh; text-align: center; }}
            h2 {{ color: #16a34a; margin-bottom: 8px; }}
            p {{ color: #64748b; }}
          </style>
        </head>
        <body>
          <h2>✅ Connected!</h2>
          <p>Linked: {google_email or 'Gmail'}</p>
          <p>You can return to Telegram now.</p>
          <script>
            if (window.Telegram?.WebApp) {{
              window.Telegram.WebApp.close();
            }}
          </script>
        </body>
        </html>
        """
        return HTMLResponse(content=success_html)

    except Exception as e:
        return HTMLResponse(f"<h3>Authentication Failed: {str(e)}</h3>", status_code=400)

@app.post("/api/webhook/telegram")
async def telegram_webhook(request: Request):
    """Production Webhook endpoint for Telegram updates."""
    try:
        update = await request.json()
        await process_telegram_update(update)
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}

async def process_telegram_update(update: dict):
    """Core message processing logic for both Webhook and Polling modes."""
    message = update.get("message", {})
    text = message.get("text", "").strip()
    chat_id = str(message.get("chat", {}).get("id"))
    first_name = message.get("from", {}).get("first_name", "there")

    if not chat_id or not text:
        return

    text_lower = text.lower()
    connect_url = f"{settings.BASE_URL}/connect?telegram_id={chat_id}"

    # 1. /start or /help
    if text_lower in ["/start", "/help"]:
        user = db.get_user(chat_id)
        if user:
            msg = (
                f"👋 Hello {first_name}!\n\n"
                f"Your Gmail (`{user.get('google_email', 'connected')}`) is already linked.\n\n"
                f"Send *\"i want email\"* anytime for your unread Primary briefing."
            )
            send_telegram_message(chat_id, msg)
        else:
            msg = (
                f"👋 Welcome {first_name}!\n\n"
                f"I am your **AI Gmail Assistant**. I deliver clean, noise-free summaries of your unread **Primary** emails.\n\n"
                f"🔗 **[Click Here to Connect Your Gmail]({connect_url})**\n\n"
                f"Or open this link:\n`{connect_url}`"
            )
            keyboard = get_connect_keyboard(settings.BASE_URL)
            send_telegram_message(chat_id, msg, reply_markup=keyboard)
        return

    # 2. "i want email"
    if "i want email" in text_lower or "unread" in text_lower or text_lower == "email":
        user = db.get_user(chat_id)
        if not user:
            msg = (
                f"⚠️ *Gmail Not Connected*\n\n"
                f"Please connect your account first:\n\n"
                f"🔗 **[Click Here to Connect Your Gmail]({connect_url})**"
            )
            keyboard = get_connect_keyboard(settings.BASE_URL)
            send_telegram_message(chat_id, msg, reply_markup=keyboard)
            return

        send_telegram_message(chat_id, "⏳ *Scanning your unread Primary emails...*")

        try:
            refresh_token = user["google_refresh_token"]
            emails = fetch_unread_primary_emails(refresh_token, max_results=20)
            summary = summarize_emails_with_gemini(emails)
            send_telegram_message(chat_id, summary)

        except Exception as e:
            err_msg = (
                f"❌ *Could not fetch emails*\n\n"
                f"Authorization may have expired. Reconnect here:\n\n"
                f"🔗 **[Click Here to Reconnect]({connect_url})**"
            )
            keyboard = get_connect_keyboard(settings.BASE_URL)
            send_telegram_message(chat_id, err_msg, reply_markup=keyboard)
        return

    # Default friendly hint
    send_telegram_message(chat_id, "💡 Send *\"i want email\"* to get your unread Primary inbox summary.")
