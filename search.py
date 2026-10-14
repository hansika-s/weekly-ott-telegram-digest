"""Google News RSS search helper."""

from __future__ import annotations

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
