from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

USER_AGENT = "Day03ResearchAgent/1.0 (educational lab)"
ALLOWED_LANGS = {"en", "vi"}


def wiki_summary(query: str = "", lang: str = "en", limit: int = 3) -> dict[str, Any]:
    """Search Wikipedia and return intro summaries of the best matching articles."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        lang = (lang or "en").strip().lower()
        if lang not in ALLOWED_LANGS:
            raise ValueError(f"lang must be one of {sorted(ALLOWED_LANGS)}")
        limit = max(1, min(int(limit or 3), 5))

        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": limit,
                "prop": "extracts|info",
                "exintro": 1,
                "explaintext": 1,
                "exchars": 800,
                "inprop": "url",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or {}
        ordered = sorted(pages.values(), key=lambda page: page.get("index", 0))
        items = [{
            "title": page.get("title"),
            "url": page.get("fullurl"),
            "source": f"{lang}.wikipedia.org",
            "summary": (page.get("extract") or "").strip(),
        } for page in ordered]
        return {"tool": "wiki_summary", "query": query, "lang": lang, "items": items}
    except Exception as exc:
        return err("wiki_summary", exc)
