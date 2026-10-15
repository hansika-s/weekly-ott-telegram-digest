"""Search for OTT release coverage."""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from digest import create_digest, send_telegram
from search import find_weekly_releases, search_google_news


def most_recent_friday(today: date) -> date:
    """Return Friday on or before today for a complete weekly digest window."""
    return today - timedelta(days=(today.weekday() - 4) % 7)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Google News for OTT releases.")
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Google News search query",
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        default=most_recent_friday(date.today()),
        help="Last day to include, in YYYY-MM-DD format (defaults to the most recent Friday).",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the Google News leads instead of generating a Gemini draft.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the completed digest to Telegram.",
    )
    args = parser.parse_args()
    results = search_google_news(args.query) if args.query else find_weekly_releases(args.end_date)

    if args.raw:
        for result in results:
            print(result["title"])
            print(result["url"])
            print()
        return

    if not results:
        return

    digest = create_digest(results, args.end_date)
    print(digest)
    if args.send:
        send_telegram(digest)


if __name__ == "__main__":
    main()
