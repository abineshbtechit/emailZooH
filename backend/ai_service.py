import httpx
from typing import List, Dict
from backend.config import settings

def summarize_emails_with_gemini(emails: List[Dict[str, str]]) -> str:
    """
    Summarizes unread primary emails into a clean, mobile-optimized Telegram Markdown format.
    """
    if not emails:
        return "📬 *PRIMARY INBOX DIGEST*\n\n🎉 *Inbox Zero!*\nYou have no unread primary emails right now."

    # Format email items
    email_blocks = []
    for idx, e in enumerate(emails):
        email_blocks.append(
            f"[#{idx + 1}]\nFrom: {e['from']}\nSubject: {e['subject']}\nDate: {e['date']}\nPreview: {e['snippet']}"
        )
    formatted_input = "\n\n---\n\n".join(email_blocks)

    system_prompt = f"""You are an executive assistant preparing an unread Primary email briefing for Telegram mobile view.

STRICT INSTRUCTIONS:
1. Format output using clean Telegram Markdown (*bold*, bullet points •).
2. Group into 2 simple sections:
   🔴 *Action Required*
   • [Sender] — *[What they need, context, or deadline]*
   (If none require action, write: • None right now.)

   🟢 *General Messages*
   • [Sender] — [1-sentence concise takeaway]
3. Keep it brief, high-signal, under 2500 characters. No markdown tables, no raw headers, no noisy fluff.

Input emails ({len(emails)} unread Primary):
{formatted_input}
"""

    # If Gemini API key is provided, generate summary
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": system_prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000}
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if text:
                            return text.strip()
        except Exception as e:
            print(f"Gemini API error, falling back to local formatter: {e}")

    # Fallback clean formatter if AI key is missing or offline
    lines = [f"📬 *PRIMARY INBOX BRIEFING* ({len(emails)} unread)\n"]
    lines.append("🟢 *Unread Messages*")
    for e in emails[:10]:
        lines.append(f"• *{e['from'][:30]}* — {e['subject']}")
    return "\n".join(lines)
