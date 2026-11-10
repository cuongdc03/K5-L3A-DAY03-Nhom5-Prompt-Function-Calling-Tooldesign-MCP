from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit


def _normalized_url(value: str) -> str:
    """Normalize harmless URL differences while preserving query parameters."""
    parts = urlsplit(value.strip())
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    if parts.port and not ((scheme == "https" and parts.port == 443) or (scheme == "http" and parts.port == 80)):
        hostname = f"{hostname}:{parts.port}"
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, hostname, path, parts.query, ""))


def deduplicate(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Remove repeated research items by URL, preserving first-seen order.

    URLs are compared case-insensitively for scheme/host, without fragments,
    and with trailing slashes ignored. Items without a URL are compared by
    normalized title. Items with neither a URL nor title are kept.
    """
    if items is None:
        items = []
    if not isinstance(items, list):
        return {"error": "ValueError", "message": "items must be a list"}
    if any(not isinstance(item, dict) for item in items):
        return {"error": "ValueError", "message": "every item must be an object"}

    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        url = item.get("url")
        title = item.get("title")
        if isinstance(url, str) and url.strip():
            key = ("url", _normalized_url(url))
        elif isinstance(title, str) and title.strip():
            key = ("title", re.sub(r"\s+", " ", title).strip().casefold())
        else:
            unique.append(item)
            continue
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return {
        "tool": "deduplicate",
        "items": unique,
        "input_count": len(items),
        "item_count": len(unique),
        "duplicate_count": len(items) - len(unique),
    }
