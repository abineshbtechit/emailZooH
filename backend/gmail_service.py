import httpx
import base64
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
from typing import List, Dict, Any, Tuple
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.config import settings

def get_google_auth_url(telegram_id: str) -> str:
    """Generate clean Google OAuth consent URL carrying telegram_id in state."""
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "state": str(telegram_id),
        "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email"
    }
    return f"{base}?{urlencode(params)}"

def exchange_code_for_tokens(code: str) -> Tuple[Dict[str, Any], str]:
    """Exchanges authorization code for access and refresh tokens, and gets email."""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    with httpx.Client() as client:
        resp = client.post(token_url, data=payload)
        resp.raise_for_status()
        token_data = resp.json()

        # Get User's Google Email
        user_info_resp = client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        email = user_info_resp.json().get("email", "") if user_info_resp.status_code == 200 else ""
        
        return token_data, email

def is_received_today(date_str: str) -> bool:
    """Checks if the email date matches today's date."""
    if not date_str:
        return True
    try:
        dt = parsedate_to_datetime(date_str)
        # Compare in the email's timezone or local time
        now = datetime.now(dt.tzinfo)
        return dt.date() == now.date()
    except Exception:
        return True

def is_strict_primary_email(headers_dict: Dict[str, str], from_str: str, subject_str: str) -> bool:
    """
    RFC-compliant Primary filter: Drops newsletters, bulk marketing campaigns,
    automated alerts, and system notifications.
    """
    # 1. Bulk & Newsletter Headers
    if "list-unsubscribe" in headers_dict or "list-id" in headers_dict or "feedback-id" in headers_dict:
        return False
    
    prec = headers_dict.get("precedence", "").lower()
    if any(b in prec for b in ["bulk", "list", "junk"]):
        return False
        
    auto_sub = headers_dict.get("auto-submitted", "").lower()
    if any(a in auto_sub for a in ["auto-generated", "auto-replied"]):
        return False
        
    if "x-auto-response-suppress" in headers_dict:
        return False

    # 2. Automated Senders
    from_lower = from_str.lower()
    automated_senders = [
        "no-reply", "noreply", "donotreply", "notifications@", "notification@",
        "alerts@", "alert@", "news@", "newsletter@", "marketing@", "support@",
        "info@", "updates@", "digest@", "automated@", "mailer-daemon@",
        "talent.paypal.com", "substack.com", "naukri.com", "send.zapier.com"
    ]
    if any(s in from_lower for s in automated_senders):
        return False

    # 3. Automated Subjects
    subj_lower = subject_str.lower()
    automated_subj = [
        "newsletter", "weekly digest", "daily digest", "unsubscribe",
        "notification", "job alert", "cluster will be automatically paused"
    ]
    if any(kw in subj_lower for kw in automated_subj):
        return False

    return True

def fetch_unread_primary_emails(refresh_token: str, max_results: int = 30) -> List[Dict[str, str]]:
    """
    Uses the user's refresh token to fetch unread Primary emails that arrived TODAY ONLY.
    """
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"]
    )
    
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # Search unread messages from the last 2 days to account for timezones
    res = service.users().messages().list(
        userId="me",
        q="is:unread newer_than:2d",
        maxResults=max_results
    ).execute()
    
    messages = res.get("messages", [])
    if not messages:
        return []

    primary_emails = []

    for item in messages:
        try:
            msg = service.users().messages().get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe", "List-Id", "Feedback-Id", "Precedence", "Auto-Submitted", "X-Auto-Response-Suppress"]
            ).execute()
            
            headers = msg.get("payload", {}).get("headers", [])
            h_dict = {h["name"].lower(): h["value"] for h in headers}

            from_val = h_dict.get("from", "Unknown")
            subject_val = h_dict.get("subject", "(No Subject)")
            date_val = h_dict.get("date", "")
            snippet = msg.get("snippet", "")

            # STRICT TODAY FILTER: Discard any email not received today
            if not is_received_today(date_val):
                continue

            # STRICT PRIMARY FILTER: Discard newsletters & bots
            if is_strict_primary_email(h_dict, from_val, subject_val):
                primary_emails.append({
                    "from": from_val,
                    "subject": subject_val,
                    "date": date_val,
                    "snippet": snippet[:400]
                })
        except Exception:
            continue

    return primary_emails
