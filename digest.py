"""Create a draft OTT digest with Gemini."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


def create_digest(results: list[dict[str, str]]) -> str:
    """Use Gemini and Google Search grounding to turn release leads into a draft."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY before generating a digest.")

    prompt = """Create a concise OTT release digest from these Google News leads.

Use Google Search grounding to verify claims before including them. Include only notable
films and scripted or animated series. Organize the answer into FILMS and SERIES. Group
Indian titles once under their verified original language (Telugu, Tamil, Hindi, or Malayalam)
and list supported dubs separately. Group international English-language titles under English.
For each title include only title, broad genre, and streaming platform. Do not mention sources,
countries, research process, ratings, or services that have no release.

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
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read())

    parts = data["candidates"][0]["content"]["parts"]
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned no digest text.")
    return text
