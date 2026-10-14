"""Search for OTT release coverage."""

from __future__ import annotations

import argparse

from digest import create_digest, send_telegram
from search import search_google_news


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Google News for OTT releases.")
    parser.add_argument(
        "query",
        nargs="?",
        default="OTT releases Telugu Tamil Hindi Malayalam Netflix Prime Video",
        help="Google News search query",
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
    results = search_google_news(args.query)

    if args.raw:
        for result in results:
            print(result["title"])
            print(result["url"])
            print()
        return

    digest = create_digest(results)
    print(digest)
    if args.send:
        send_telegram(digest)


if __name__ == "__main__":
    main()
