import sys
import urllib.parse
from pathlib import Path

# Add project root to sys.path so backend imports work seamlessly on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app import app as fastapi_app

class VercelPathMiddleware:
    """
    Restores the original requested path rewritten by Vercel via __path__ query param.
    """
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            qs = scope.get("query_string", b"").decode("utf-8", "ignore")
            query = urllib.parse.parse_qs(qs, keep_blank_values=True)
            if "__path__" in query:
                orig_path = query.pop("__path__")[0]
                scope["path"] = "/" + orig_path.lstrip("/")
                # Rebuild query_string without __path__
                clean_qs = urllib.parse.urlencode(query, doseq=True)
                scope["query_string"] = clean_qs.encode("utf-8")
            elif scope.get("path") == "/api/index.py":
                scope["path"] = "/"

        await self.inner_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)
