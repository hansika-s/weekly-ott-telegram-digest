"""Google News RSS search helper."""

from __future__ import annotations

from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from html.parser import HTMLParser
import re
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from gnews_decoder import decode_many


class ArticleParser(HTMLParser):
    """Keep a page description and its first useful paragraphs."""

    def __init__(self) -> None:
        super().__init__()
        self.description = ""
        self.in_paragraph = False
        self.current: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "meta" and not self.description:
            values = {key.lower(): (value or "") for key, value in attrs}
            label = values.get("name", values.get("property", "")).lower()
            if label in {"description", "og:description"}:
                self.description = unescape(values.get("content", "")).strip()
        if tag == "p":
            self.in_paragraph = True
            self.current = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self.in_paragraph:
            paragraph = " ".join("".join(self.current).split())
            if len(paragraph) > 40:
                self.paragraphs.append(paragraph)
            self.in_paragraph = False

    def handle_data(self, data: str) -> None:
        if self.in_paragraph:
            self.current.append(data)


def search_google_news(query: str, limit: int = 6) -> list[dict[str, str]]:
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
            "summary": _plain_text(item.findtext("description", default="")),
        }
        for item in root.findall("./channel/item")[:limit]
    ]


def _plain_text(html: str) -> str:
    """Turn a small HTML fragment into readable text."""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def fetch_article_text(url: str) -> str:
    """Fetch enough public publisher text to verify a release claim."""
    request = urllib.request.Request(url, headers={"User-Agent": "weekly-ott-digest/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            html = response.read(1_000_000).decode("utf-8", errors="ignore")
    except Exception:
        return ""

    parser = ArticleParser()
    parser.feed(html)
    return f"{parser.description}\n{' '.join(parser.paragraphs[:12])}".strip()[:4_000]


def has_streaming_evidence(text: str) -> bool:
    """Reject articles about future or theatrical-only streaming announcements."""
    text = text.casefold()
    has_streaming_claim = bool(
        re.search(r"\b(stream(?:ing)?|available to watch|premier(?:e|ed|ing))\b", text)
    )
    has_explicit_date = bool(
        re.search(
            r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
            r"dec(?:ember)?)\s+\d{1,2}\b",
            text,
        )
    )
    return has_streaming_claim and has_explicit_date


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
        try:
            matches = search_google_news(query)
        except Exception:
            continue
        for item in matches:
            key = (item["title"].casefold(), item["url"])
            if key not in seen:
                seen.add(key)
                results.append(item)
    try:
        resolved = decode_many([item["url"] for item in results], ceid="IN:en", timeout=20)
    except Exception:
        resolved = {}

    def enrich(item: dict[str, str]) -> None:
        publisher_url = resolved.get(item["url"])
        if publisher_url:
            item["url"] = publisher_url
            item["article"] = fetch_article_text(publisher_url)
        else:
            item["article"] = ""

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(enrich, results))
    return [item for item in results if has_streaming_evidence(item["article"])]
