"""xosint news: article search via NewsAPI."""

from __future__ import annotations

import argparse
import sys

from xosint.output import add_json_flag, emit_json

NAME = "news"


def run(args: argparse.Namespace) -> int:
    import requests

    from xosint.modules.news import search_news

    try:
        result = search_news(args.query, args.limit)
    except ValueError as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, requests.RequestException) as exc:
        print(f"News error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        emit_json(result)
        return 0

    articles = result["articles"]
    print(f"{len(articles)} of {result['total_results']} results for {result['query']!r}")
    for i, art in enumerate(articles, 1):
        print(f"\n{i}. {art['title']}")
        print(f"   {art['source']} | {art['published_at']}")
        print(f"   {art['url']}")
    return 0


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        NAME,
        help="Search recent news articles via NewsAPI (needs XOSINT_NEWSAPI_KEY).",
    )
    parser.add_argument("query", help="Search query (quote multi-word queries).")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of articles to return, 1-100 (default: 10).",
    )
    add_json_flag(parser)
    parser.set_defaults(handler=run)
