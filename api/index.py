import sys
from pathlib import Path

# Add project root to sys.path so backend imports work seamlessly on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app import app as fastapi_app

class VercelPathMiddleware:
    """
    On Vercel, catch-all rewrites rewrite incoming paths to /api/index.py.
    This middleware restores the original requested path from x-matched-path header
    so FastAPI routes (/connect, /privacy, /, etc.) match cleanly.
    """
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
            if matched_path and matched_path != "/api/index.py":
                scope["path"] = matched_path
            elif scope.get("path") == "/api/index.py":
                scope["path"] = "/"
        await self.inner_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)

