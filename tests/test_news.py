"""Offline tests for the news module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from xosint.modules import news


def _session(payload, status=200):
    resp = MagicMock()
    resp.json.return_value = payload
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status}")
    session = MagicMock()
    session.get.return_value = resp
    return session


OK_PAYLOAD = {
    "status": "ok",
    "totalResults": 1,
    "articles": [
        {
            "source": {"name": "Example"},
            "title": "Headline",
            "url": "https://example.com/a",
            "publishedAt": "2026-11-25T10:00:00Z",
            "description": "Desc",
        }
    ],
}


def test_search_news_parses_articles():
    session = _session(OK_PAYLOAD)
    result = news.search_news("seattle", 5, api_key="k", session=session)
    assert result["total_results"] == 1
    assert result["articles"][0]["source"] == "Example"
    assert result["articles"][0]["title"] == "Headline"


def test_search_news_uses_params_header_and_timeout():
    session = _session(OK_PAYLOAD)
    news.search_news("a b", 3, api_key="secret", session=session)
    _, kwargs = session.get.call_args
    assert kwargs["params"]["q"] == "a b"
    assert kwargs["params"]["pageSize"] == 3
    assert kwargs["headers"] == {"X-Api-Key": "secret"}
    assert kwargs["timeout"] == news.DEFAULT_TIMEOUT
    assert "secret" not in session.get.call_args.args[0]


def test_missing_key_raises(monkeypatch):
    monkeypatch.setattr(news, "get_secret", lambda name: None)
    with pytest.raises(RuntimeError, match="XOSINT_NEWSAPI_KEY"):
        news.search_news("x", session=_session(OK_PAYLOAD))


@pytest.mark.parametrize("query,limit", [("  ", 5), ("x", 0), ("x", 101)])
def test_bad_arguments(query, limit):
    with pytest.raises(ValueError):
        news.search_news(query, limit, api_key="k", session=_session(OK_PAYLOAD))


def test_api_error_payload():
    session = _session({"status": "error", "message": "rate limited"})
    with pytest.raises(news.NewsAPIError, match="rate limited"):
        news.search_news("x", api_key="k", session=session)


def test_http_error_uses_api_message():
    session = _session({"status": "error", "message": "apiKey invalid"}, status=401)
    with pytest.raises(news.NewsAPIError, match="apiKey invalid"):
        news.search_news("x", api_key="k", session=session)
