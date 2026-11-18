import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app import app as fastapi_app

class VercelPathMiddleware:
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            header_dict = {k.decode("utf-8", "ignore"): v.decode("utf-8", "ignore") for k, v in scope.get("headers", [])}
            
            # If requesting /_debug, return headers and scope info
            if "debug" in header_dict.get("x-matched-path", "") or b"debug" in scope.get("query_string", b""):
                response_body = json.dumps({
                    "scope_path": scope.get("path"),
                    "raw_path": scope.get("raw_path", b"").decode("utf-8", "ignore"),
                    "query_string": scope.get("query_string", b"").decode("utf-8", "ignore"),
                    "headers": header_dict
                }).encode("utf-8")
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]]
                })
                await send({
                    "type": "http.response.body",
                    "body": response_body
                })
                return

            matched_path = header_dict.get("x-matched-path", "")
            if matched_path and matched_path != "/api/index.py":
                scope["path"] = matched_path
            elif scope.get("path") == "/api/index.py":
                scope["path"] = "/"

        await self.inner_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)


