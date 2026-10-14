"""Search for OTT release coverage."""

from __future__ import annotations

import argparse

from search import search_google_news


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Google News for OTT releases.")
    parser.add_argument(
        "query",
        nargs="?",
        default="OTT releases Telugu Tamil Hindi Malayalam Netflix Prime Video",
        help="Google News search query",
    )
    args = parser.parse_args()

    for result in search_google_news(args.query):
        print(result["title"])
        print(result["url"])
        print()


if __name__ == "__main__":
    main()
