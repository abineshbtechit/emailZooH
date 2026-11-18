import uvicorn
import asyncio
import threading
from backend.config import settings
from backend.bot_polling import run_polling

def start_polling_thread():
    if settings.TELEGRAM_BOT_TOKEN:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_polling())

if __name__ == "__main__":
    print(f"🚀 Starting {settings.APP_NAME}...")
    print(f"🌐 Mini App URL: {settings.BASE_URL}/connect")
    
    # Run polling in background thread
    if settings.TELEGRAM_BOT_TOKEN:
        t = threading.Thread(target=start_polling_thread, daemon=True)
        t.start()
        print("🤖 Telegram Bot Polling active for @ZooHHooZbot!")

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)
