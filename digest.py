"""Create a draft OTT digest with Gemini."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
import time
import urllib.error
import urllib.parse
import urllib.request


def create_digest(results: list[dict[str, str]], end_date: date) -> str:
    """Use Gemini and Google Search grounding to turn release leads into a draft."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY before generating a digest.")

    start_date = end_date - timedelta(days=6)
    prompt = f"""Create a concise OTT release digest for {start_date:%d %b %Y}–{end_date:%d %b %Y}.

The supplied Google News entries are leads, not evidence. Use Google Search grounding to verify
each title's release date, platform, format, original language and dubs. Include only notable
films and scripted or animated series that premiered in this date range. A title must be available
on one of these services: Netflix, Prime Video, JioHotstar, Aha, ZEE5, Sun NXT, SonyLIV, Disney+,
or Apple TV+. Omit anything uncertain, theatrical-only, documentary/reality/news content, or not
released in the date window.

Use this exact compact structure, omitting empty sections and languages:
FILMS
Telugu
- Title — Genre — Platform
  Dubs: language list (only when confirmed)

SERIES
English
- Title — Genre — Platform

Group Indian titles exactly once under their verified original language: Telugu, Tamil, Hindi, or
Malayalam. Never repeat them under dubbed languages. Put English-language international titles
under English. Include only title, broad genre and platform; Indian entries may additionally have
the Dubs line. Do not include a country, rating, source, availability note, research comment,
service list, introduction or conclusion.

Google News leads:
""" + json.dumps(results, ensure_ascii=False)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.1},
    }
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read())
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 2:
                raise RuntimeError(
                    f"Gemini request failed with HTTP {error.code}. Check the API key's model access and quota."
                ) from error
            time.sleep(10 * (attempt + 1))

    parts = data["candidates"][0]["content"]["parts"]
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned no digest text.")
    return text


def send_telegram(text: str) -> None:
    """Send a completed digest to the configured Telegram chat."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError(
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID before sending to Telegram."
        )

    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read())

    if not result.get("ok"):
        raise RuntimeError("Telegram did not accept the digest.")
