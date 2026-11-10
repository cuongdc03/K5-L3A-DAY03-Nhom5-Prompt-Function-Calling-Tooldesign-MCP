from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err

VALID_SORTS = {"stars", "forks", "updated", "best-match"}


def search_github_repos(
    query: str = "",
    language: str = "",
    sort: str = "stars",
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

        normalized_sort = (sort or "stars").strip().lower()
        if normalized_sort not in VALID_SORTS:
            normalized_sort = "stars"

        q_str = cleaned_query
        cleaned_lang = (language or "").strip()
        if cleaned_lang and f"language:{cleaned_lang.lower()}" not in cleaned_query.lower():
            q_str = f"{cleaned_query} language:{cleaned_lang}"

        params: dict[str, Any] = {
            "q": q_str,
            "per_page": limit,
            "order": "desc",
        }
        if normalized_sort != "best-match":
            params["sort"] = normalized_sort

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "AI20k-Day03-Research-Agent/1.0",
        }
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
        data = response.json()
        raw_items = data.get("items") or []
        items = [
            {
                "title": repo.get("full_name") or repo.get("name") or "",
                "url": repo.get("html_url") or "",
                "source": "github.com",
                "summary": (repo.get("description") or "").strip(),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language"),
                "updated_at": repo.get("updated_at"),
            }
            for repo in raw_items[:limit]
            if repo.get("html_url") or repo.get("full_name")
        ]
        return {
            "tool": "github_search",
            "query": cleaned_query,
            "language": cleaned_lang or None,
            "sort": normalized_sort,
            "total_count": int(data.get("total_count", len(items))),
            "items": items,
        }
    except Exception as exc:
        return err("github_search", exc)
