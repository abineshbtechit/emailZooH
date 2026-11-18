import time
import httpx
import asyncio
from backend.config import settings
from backend.app import process_telegram_update

async def run_polling():
    """
    Runs Telegram Long Polling locally.
    Enables instant testing on localhost without needing ngrok or a public domain!
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN is not set in .env. Cannot start polling.")
        return

    print("🤖 Telegram Bot Polling started! Press Ctrl+C to stop.")
    last_update_id = 0
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"

    # Delete any webhook to allow getUpdates
    async with httpx.AsyncClient() as client:
        await client.post(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteWebhook")

    async with httpx.AsyncClient(timeout=40.0) as client:
        while True:
            try:
                params = {"offset": last_update_id + 1, "timeout": 30}
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        last_update_id = update["update_id"]
                        await process_telegram_update(update)
            except Exception as e:
                print(f"[Polling Notice] {e}")
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_polling())
