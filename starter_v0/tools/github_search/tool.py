from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err

ALLOWED_SORTS = {"stars", "updated", "best_match"}


def github_search(query: str = "", sort: str = "stars", language: str = "", limit: int = 5) -> dict[str, Any]:
    """Search public GitHub repositories. GITHUB_TOKEN is optional (raises the rate limit)."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        sort = (sort or "stars").strip().lower()
        if sort not in ALLOWED_SORTS:
            raise ValueError(f"sort must be one of {sorted(ALLOWED_SORTS)}")
        limit = max(1, min(int(limit or 5), 20))

        q = query
        language = (language or "").strip()
        if language:
            q = f"{q} language:{language}"
        params: dict[str, Any] = {"q": q, "per_page": limit}
        if sort != "best_match":
            params.update({"sort": sort, "order": "desc"})
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Day03ResearchAgent"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(
            "https://api.github.com/search/repositories",
            params=params,
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = [{
            "title": repo.get("full_name"),
            "url": repo.get("html_url"),
            "summary": repo.get("description") or "",
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language"),
            "updated_at": repo.get("pushed_at") or repo.get("updated_at"),
        } for repo in response.json().get("items", [])[:limit]]
        return {"tool": "github_search", "query": query, "sort": sort, "language": language or None, "items": items}
    except Exception as exc:
        return err("github_search", exc)
