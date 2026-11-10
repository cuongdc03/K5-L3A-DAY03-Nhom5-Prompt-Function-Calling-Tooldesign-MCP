from __future__ import annotations

import urllib.parse
from typing import Any
import requests

from tools._shared import TIMEOUT, err


def search_wikipedia(title: str = "", language: str = "en") -> dict[str, Any]:
    try:
        clean_title = (title or "").strip()
        if not clean_title:
            return {"tool": "wikipedia", "items": [], "error": "Empty title"}
        lang = language if language in ["en", "vi", "fr", "de", "ja"] else "en"
        encoded = urllib.parse.quote(clean_title.replace(" ", "_"))
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        headers = {"User-Agent": "AI20k-ResearchAgent/1.0 (educational lab)"}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 404:
            return {"tool": "wikipedia", "title": clean_title, "items": []}
        resp.raise_for_status()
        data = resp.json()
        page_title = data.get("title", clean_title)
        extract = data.get("extract", "")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", url)
        return {
            "tool": "wikipedia",
            "title": page_title,
            "items": [{
                "title": page_title,
                "url": page_url,
                "source": f"wikipedia_{lang}",
                "summary": extract,
            }],
        }
    except Exception as exc:
        return err("wikipedia", exc)
