"""News OSINT: article search via NewsAPI (user-supplied key only)."""

from __future__ import annotations

from typing import Any

import requests

from xosint.config import get_secret

DEFAULT_TIMEOUT = 10
NEWSAPI_URL = "https://newsapi.org/v2/everything"
MAX_LIMIT = 100


class NewsAPIError(RuntimeError):
    """Raised when NewsAPI returns an error payload."""


def search_news(
    query: str,
    limit: int = 10,
    *,
    api_key: str | None = None,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Search NewsAPI /v2/everything, newest first.

    Raises ValueError for a bad query or limit, RuntimeError if no key is
    configured, NewsAPIError for API-reported errors, and
    requests.RequestException for network failures.
    """
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    key = api_key or get_secret("newsapi_key")
    if not key:
        raise RuntimeError(
            "NewsAPI key not configured. "
            "Set XOSINT_NEWSAPI_KEY or add newsapi_key under [secrets] in config.toml."
        )

    client = session or requests.Session()
    resp = client.get(
        NEWSAPI_URL,
        params={"q": query, "pageSize": limit, "sortBy": "publishedAt"},
        headers={"X-Api-Key": key},
        timeout=timeout,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        message = None
        try:
            message = resp.json().get("message")
        except ValueError:
            pass
        if message:
            raise NewsAPIError(message) from exc
        raise

    data = resp.json()
    if data.get("status") != "ok":
        raise NewsAPIError(data.get("message", "unknown NewsAPI error"))

    articles = [
        {
            "title": a.get("title"),
            "source": (a.get("source") or {}).get("name"),
            "published_at": a.get("publishedAt"),
            "url": a.get("url"),
            "description": a.get("description"),
        }
        for a in data.get("articles", [])
    ]
    return {
        "query": query,
        "total_results": data.get("totalResults", len(articles)),
        "articles": articles,
    }
