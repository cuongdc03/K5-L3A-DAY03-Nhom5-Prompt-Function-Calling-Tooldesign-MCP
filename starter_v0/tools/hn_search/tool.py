from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

VALID_TAGS = {"story", "comment", "ask_hn", "show_hn"}


def search_hackernews(
    query: str = "",
    tags: str = "story",
    max_results: int = 5,
) -> dict[str, Any]:
    try:
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            raise ValueError("query must not be empty")

        try:
            limit = max(1, min(int(max_results or 5), 20))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid max_results: {max_results!r}") from exc

        normalized_tags = (tags or "story").strip().lower()
        if normalized_tags not in VALID_TAGS:
            normalized_tags = "story"

        response = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": cleaned_query,
                "tags": normalized_tags,
                "hitsPerPage": limit,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits") or []
        items: list[dict[str, Any]] = []
        for hit in hits[:limit]:
            object_id = hit.get("objectID") or ""
            hn_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
            title = (hit.get("title") or hit.get("story_title") or "").strip()
            comment_text = (hit.get("comment_text") or hit.get("story_text") or "").strip()
            items.append({
                "title": title or comment_text[:120] or f"HN item {object_id}",
                "url": hit.get("url") or hn_url,
                "hn_url": hn_url,
                "source": "news.ycombinator.com",
                "summary": comment_text[:400] if comment_text else title,
                "author": hit.get("author"),
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at"),
            })
        return {
            "tool": "hn_search",
            "query": cleaned_query,
            "tags": normalized_tags,
            "total_hits": int(data.get("nbHits", len(items))),
            "items": items,
        }
    except Exception as exc:
        return err("hn_search", exc)
