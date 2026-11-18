import sqlite3
import os
import tempfile
from typing import Optional, Dict, Any
from backend.config import settings

class Database:
    def __init__(self):
        self.use_supabase = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
        self.db_path = settings.DATABASE_PATH
        if not self.use_supabase:
            if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
                self.db_path = os.path.join(tempfile.gettempdir(), "users.db")
            self._init_sqlite()

    def _init_sqlite(self):
        try:
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
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
        except Exception as e:
            print(f"Warning: Could not initialize SQLite at {self.db_path}: {e}")

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
            try:
                conn = sqlite3.connect(self.db_path)
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
            except Exception as e:
                print(f"Error saving user in SQLite: {e}")

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
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
                row = cursor.fetchone()
                conn.close()
                return dict(row) if row else None
            except Exception as e:
                print(f"Error retrieving user from SQLite: {e}")
                return None

db = Database()
