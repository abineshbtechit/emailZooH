import sqlite3
import os
from typing import Optional, Dict, Any
from backend.config import settings

class Database:
    def __init__(self):
        self.use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
        if not self.use_supabase:
            self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(settings.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id TEXT PRIMARY KEY,
                google_email TEXT,
                google_refresh_token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_user(self, telegram_id: str, refresh_token: str, google_email: Optional[str] = None):
        telegram_id = str(telegram_id)
        if self.use_supabase:
            import httpx
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            }
            payload = {
                "telegram_id": telegram_id,
                "google_refresh_token": refresh_token,
                "google_email": google_email or ""
            }
            with httpx.Client() as client:
                resp = client.post(f"{settings.SUPABASE_URL}/rest/v1/users", json=payload, headers=headers)
                resp.raise_for_status()
        else:
            conn = sqlite3.connect(settings.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (telegram_id, google_refresh_token, google_email, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    google_refresh_token = excluded.google_refresh_token,
                    google_email = excluded.google_email,
                    updated_at = CURRENT_TIMESTAMP
            """, (telegram_id, refresh_token, google_email or ""))
            conn.commit()
            conn.close()

    def get_user(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        telegram_id = str(telegram_id)
        if self.use_supabase:
            import httpx
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}"
            }
            with httpx.Client() as client:
                resp = client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/users?telegram_id=eq.{telegram_id}&select=*",
                    headers=headers
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data[0] if data else None
                return None
        else:
            conn = sqlite3.connect(settings.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

db = Database()
