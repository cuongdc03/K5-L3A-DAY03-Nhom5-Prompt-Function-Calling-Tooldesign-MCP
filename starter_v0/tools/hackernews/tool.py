from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"


def search_hackernews(
    query: str = "",
    sort_by: str = "relevance",
    max_results: int = 5,
) -> dict[str, Any]:
    try:
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            raise ValueError("Missing or empty query for Hacker News search")

        limit = max(1, min(int(max_results or 5), 20))
        normalized_sort = sort_by if sort_by in {"relevance", "date"} else "relevance"
        endpoint = HN_SEARCH_BY_DATE_URL if normalized_sort == "date" else HN_SEARCH_URL

        response = requests.get(
            endpoint,
            params={
                "query": cleaned_query,
                "tags": "story",
                "hitsPerPage": limit,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        items: list[dict[str, Any]] = []
        for hit in (data.get("hits") or [])[:limit]:
            object_id = str(hit.get("objectID") or "").strip()
            title = (hit.get("title") or hit.get("story_title") or "").strip()
            if not title and not object_id:
                continue
            hn_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
            raw_url = (hit.get("url") or "").strip()
            item_url = raw_url or hn_url
            points = hit.get("points") or 0
            comments = hit.get("num_comments") or 0
            author = hit.get("author") or "unknown"
            summary = f"{points} points | {comments} comments | by {author} (HN: {hn_url})"
            items.append({
                "title": title or f"HN Story #{object_id}",
                "url": item_url,
                "hn_url": hn_url,
                "source": domain(raw_url) or "news.ycombinator.com",
                "summary": summary,
                "points": points,
                "num_comments": comments,
                "author": author,
                "date": hit.get("created_at"),
            })

        return {
            "tool": "search_hackernews",
            "query": cleaned_query,
            "sort_by": normalized_sort,
            "items": items,
        }
    except Exception as exc:
        return err("search_hackernews", exc)
