import httpx
from typing import Optional, Dict, Any
from backend.config import settings

def send_telegram_message(
    chat_id: str,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    parse_mode: str = "Markdown"
) -> bool:
    """Send text message via Telegram Bot API with automatic error recovery."""
    if not settings.TELEGRAM_BOT_TOKEN:
        print(f"[Mock Telegram] To: {chat_id} | Text: {text}")
        return True

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                return True
            
            print(f"[Telegram API Notice] {resp.status_code}: {resp.text}")
            
            # Fallback 1: Drop reply_markup if Telegram rejected the button
            if reply_markup:
                payload.pop("reply_markup", None)
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return True

            # Fallback 2: Drop parse_mode if markdown had unescaped symbols
            payload.pop("parse_mode", None)
            resp = client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def get_connect_keyboard(base_url: str) -> Optional[Dict[str, Any]]:
    """Generates an Inline Keyboard only when an HTTPS URL is configured."""
    if base_url.startswith("https://"):
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "🔗 Connect My Gmail",
                        "web_app": {"url": f"{base_url}/connect"}
                    }
                ]
            ]
        }
    return None
