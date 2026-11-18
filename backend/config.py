import os
import tempfile
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

def get_default_db_path() -> str:
    # If running on Vercel or AWS Lambda, the root filesystem is read-only
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return os.path.join(tempfile.gettempdir(), "users.db")
    return "users.db"

def get_base_url() -> str:
    val = os.getenv("BASE_URL", "")
    if not val or "cloudflare" in val or "localhost" in val:
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            return "https://email-zoo-h.vercel.app"
    return val or "https://email-zoo-h.vercel.app"

def get_redirect_uri() -> str:
    val = os.getenv("GOOGLE_REDIRECT_URI", "")
    if not val or "cloudflare" in val or "localhost" in val:
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            return "https://email-zoo-h.vercel.app/api/auth/callback"
    return val or "https://email-zoo-h.vercel.app/api/auth/callback"

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Telegram Gmail Assistant"
    BASE_URL: str = get_base_url()
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "supersecret123")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = get_redirect_uri()
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Database (SQLite by default, Supabase if provided)
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", get_default_db_path())
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
