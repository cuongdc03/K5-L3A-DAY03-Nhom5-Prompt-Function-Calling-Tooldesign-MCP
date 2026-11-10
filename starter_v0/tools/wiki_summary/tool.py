from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

VALID_LANGS = {"en", "vi", "fr", "de", "ja", "zh"}


def get_wikipedia_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    try:
        cleaned_title = (title or "").strip()
        if not cleaned_title:
            raise ValueError("title must not be empty")

        normalized_lang = (lang or "en").strip().lower()
        if normalized_lang not in VALID_LANGS:
            normalized_lang = "en"

        encoded_title = quote(cleaned_title.replace(" ", "_"), safe="")
        url = f"https://{normalized_lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        response = requests.get(
            url,
            headers={"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        page_title = data.get("title") or cleaned_title
        extract = (data.get("extract") or "").strip()[:4000]
        page_url = (
            ((data.get("content_urls") or {}).get("desktop") or {}).get("page")
            or f"https://{normalized_lang}.wikipedia.org/wiki/{encoded_title}"
        )
        return {
            "tool": "wiki_summary",
            "title": page_title,
            "lang": normalized_lang,
            "extract": extract,
            "items": [
                {
                    "title": page_title,
                    "url": page_url,
                    "source": f"{normalized_lang}.wikipedia.org",
                    "summary": extract,
                }
            ],
        }
    except Exception as exc:
        return err("wiki_summary", exc)
