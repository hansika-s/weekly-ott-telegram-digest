"""Google News RSS search helper."""

from __future__ import annotations

from datetime import date, timedelta
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def search_google_news(query: str, limit: int = 10) -> list[dict[str, str]]:
    """Return recent Google News results for a query."""
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}
    )
    request = urllib.request.Request(url, headers={"User-Agent": "weekly-ott-digest/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())

    return [
        {
            "title": item.findtext("title", default="").strip(),
            "url": item.findtext("link", default="").strip(),
        }
        for item in root.findall("./channel/item")[:limit]
    ]


def weekly_queries(end_date: date) -> list[str]:
    """Build language-first Google News queries for the current digest window."""
    start_date = end_date - timedelta(days=6)
    day_after_end = end_date + timedelta(days=1)
    period = f"after:{start_date.isoformat()} before:{day_after_end.isoformat()}"
    indian_services = "(Netflix OR \"Prime Video\" OR JioHotstar OR Aha OR ZEE5 OR \"Sun NXT\" OR SonyLIV)"
    english_services = "(Netflix OR \"Prime Video\" OR \"Disney+\" OR \"Apple TV+\")"
    return [
        f"Telugu OTT release {indian_services} {period}",
        f"Tamil OTT release {indian_services} {period}",
        f"Hindi OTT release {indian_services} {period}",
        f"Malayalam OTT release {indian_services} {period}",
        f"English streaming release {english_services} {period}",
    ]


def find_weekly_releases(end_date: date) -> list[dict[str, str]]:
    """Collect and de-duplicate coverage across all language-first queries."""
    seen: set[tuple[str, str]] = set()
    results: list[dict[str, str]] = []
    for query in weekly_queries(end_date):
        for item in search_google_news(query):
            key = (item["title"].casefold(), item["url"])
            if key not in seen:
                seen.add(key)
                results.append(item)
    return results
