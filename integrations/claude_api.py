"""
Claude API integration — drafts review replies.

This is a SEPARATE account/billing from claude.ai — sign up at
https://platform.claude.com, create an API key, and set CLAUDE_API_KEY
in your environment.
"""
import os
import requests

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"


def draft_reply(review_text: str, rating: int, restaurant_name: str, tone: str) -> str:
    if not CLAUDE_API_KEY:
        raise RuntimeError("CLAUDE_API_KEY is not set — add it to your environment first.")

    prompt = f"""You are writing a public reply to a customer review for a restaurant called "{restaurant_name}".

Restaurant's desired tone: {tone}

Review (rating: {rating}/5 stars):
\"\"\"{review_text}\"\"\"

Write a short, genuine reply (2-4 sentences) as the restaurant owner would.
- If the review is positive, thank them warmly and specifically.
- If the review is negative or mixed, acknowledge the issue sincerely, avoid being
  defensive, and invite them to reach out directly to make it right.
- Never sound generic or copy-paste. Never over-promise discounts or refunds.
- Do not include a subject line or signature — just the reply text itself.
"""

    resp = requests.post(
        CLAUDE_API_URL,
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    for block in data.get("content", []):
        if block.get("type") == "text":
            return block["text"].strip()

    raise RuntimeError("No text content returned from Claude API.")
