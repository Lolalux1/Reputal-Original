"""
Zernio integration.

Docs: https://zernio.com
You'll need a Zernio account + API key — set ZERNIO_API_KEY in your environment.
"""
import os
import requests

ZERNIO_API_KEY = os.environ.get("ZERNIO_API_KEY", "")
ZERNIO_BASE_URL = "https://api.zernio.com/v1"  # confirm exact base URL in current Zernio docs before going live


def _headers():
    return {
        "Authorization": f"Bearer {ZERNIO_API_KEY}",
        "Content-Type": "application/json",
    }


def get_connect_url(redirect_uri: str) -> str:
    return (
        f"{ZERNIO_BASE_URL}/connect/googlebusiness"
        f"?api_key={ZERNIO_API_KEY}&redirect_uri={redirect_uri}"
    )


def fetch_reviews(zernio_account_id: str):
    if not ZERNIO_API_KEY:
        raise RuntimeError("ZERNIO_API_KEY is not set — add it to your environment first.")

    resp = requests.get(
        f"{ZERNIO_BASE_URL}/reviews",
        headers=_headers(),
        params={"accountId": zernio_account_id, "platform": "googlebusiness"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    reviews = []
    for item in data.get("reviews", []):
        reviews.append(
            {
                "id": item.get("id"),
                "author_name": item.get("authorName", "Anonymous"),
                "rating": item.get("rating"),
                "text": item.get("text", ""),
            }
        )
    return reviews


def post_reply(zernio_account_id: str, review_id: str, message: str):
    if not ZERNIO_API_KEY:
        raise RuntimeError("ZERNIO_API_KEY is not set — add it to your environment first.")

    resp = requests.post(
        f"{ZERNIO_BASE_URL}/reviews/reply",
        headers=_headers(),
        json={
            "accountId": zernio_account_id,
            "reviewId": review_id,
            "message": message,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
