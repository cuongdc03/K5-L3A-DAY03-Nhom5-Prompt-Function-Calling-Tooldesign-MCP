from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests

from tools._shared import domain, err

CHECK_TIMEOUT = 10
MAX_URLS = 10
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
SOFT_404_PATTERNS = re.compile(
    r"\b(404\s*(not\s*found|error|page)?|page\s*not\s*found|khong\s*tim\s*thay\s*trang|không\s*tìm\s*thấy\s*trang)\b",
    re.IGNORECASE,
)


def _normalize_url_for_compare(url: str) -> str:
    try:
        parsed = urlparse(url.strip())
        host = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.rstrip("/") or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{host}{path}{query}"
    except Exception:
        return url.strip().lower()


def _extract_title(html: str) -> str:
    if not html:
        return ""
    match = re.search(r"<title[^>]*>(.*?)</title>", html[:16384], flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()[:200]


def _parse_url_inputs(urls: list[str] | str | None) -> list[str]:
    if urls is None:
        return []
    if isinstance(urls, str):
        raw_items = [part.strip() for part in re.split(r"[\s,]+", urls) if part.strip()]
    elif isinstance(urls, list):
        raw_items = [str(item).strip() for item in urls if str(item).strip()]
    else:
        raise ValueError("urls must be a list of URL strings or a single URL string")

    deduped: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped[:MAX_URLS]


def _check_single_url(target_url: str) -> dict[str, Any]:
    response = requests.get(
        target_url,
        headers={"User-Agent": USER_AGENT},
        timeout=CHECK_TIMEOUT,
        allow_redirects=True,
    )
    status_code = int(getattr(response, "status_code", 0) or 0)
    raw_final = getattr(response, "url", None)
    payload = getattr(response, "_payload", None)
    if not raw_final and isinstance(payload, dict):
        raw_final = payload.get("final_url") or payload.get("url")
    final_url = str(raw_final or target_url).strip()

    history = getattr(response, "history", None) or []
    redirected = (
        _normalize_url_for_compare(target_url) != _normalize_url_for_compare(final_url)
        or bool(history)
    )

    orig_parsed = urlparse(target_url)
    final_parsed = urlparse(final_url)
    orig_path = orig_parsed.path.rstrip("/")
    final_path = final_parsed.path.rstrip("/")
    redirected_to_root = bool(orig_path and len(orig_path) > 1 and final_path == "")
    redirected_to_error_path = final_path.lower() in {"/404", "/not-found", "/error", "/404.html"}
    cross_domain_redirect = (
        orig_parsed.netloc.lower().removeprefix("www.")
        != final_parsed.netloc.lower().removeprefix("www.")
    )

    body_text = getattr(response, "text", "") or ""
    title = _extract_title(body_text)
    if not title and isinstance(payload, dict):
        title = str(payload.get("title") or "").strip()

    is_soft_404 = bool(title and SOFT_404_PATTERNS.search(title))
    is_cloudflare_challenge = status_code in {403, 429} and (
        "cloudflare" in body_text.lower() or "just a moment" in body_text.lower()
    )

    if status_code in {404, 410}:
        is_valid = False
        status = "not_found_404"
        reason = f"HTTP {status_code} (Dead/Not Found link)"
    elif is_cloudflare_challenge and not redirected_to_error_path:
        is_valid = True
        status = "ok_bot_protected"
        reason = f"HTTP {status_code} (Protected by anti-bot challenge, domain reachable)"
    elif status_code >= 400 or status_code < 200:
        is_valid = False
        status = f"http_error_{status_code}"
        reason = f"HTTP {status_code}"
    elif is_soft_404:
        is_valid = False
        status = "soft_404"
        reason = f"Page returned 200 but title indicates 404/Not Found: {title!r}"
    elif redirected_to_error_path or redirected_to_root:
        is_valid = False
        status = "redirected_to_invalid_page"
        reason = f"Redirected from deep link {target_url} to homepage/error page {final_url}"
    elif redirected:
        is_valid = True
        status = "redirected_cross_domain" if cross_domain_redirect else "redirected"
        reason = f"Redirected from {target_url} to {final_url}"
    else:
        is_valid = True
        status = "ok"
        reason = "HTTP 200 OK"

    if hasattr(response, "close"):
        response.close()

    return {
        "url": target_url,
        "final_url": final_url,
        "source": domain(final_url) or domain(target_url),
        "status_code": status_code,
        "is_valid": is_valid,
        "redirected": redirected,
        "status": status,
        "title": title,
        "reason": reason,
    }


def validate_urls(urls: list[str] | str | None = None) -> dict[str, Any]:
    try:
        url_list = _parse_url_inputs(urls)
        if not url_list:
            raise ValueError("Missing or empty urls to validate")

        valid_scheme_urls = [u for u in url_list if u.startswith(("http://", "https://"))]
        if not valid_scheme_urls:
            raise ValueError(f"Invalid URL format (must start with http:// or https://): {url_list[0]}")

        results: list[dict[str, Any]] = []
        valid_urls: list[str] = []
        invalid_urls: list[str] = []
        last_exc: Exception | None = None
        network_Attempted = 0
        network_failed = 0

        for item_url in url_list:
            if not item_url.startswith(("http://", "https://")):
                results.append({
                    "url": item_url,
                    "final_url": item_url,
                    "source": "",
                    "status_code": 0,
                    "is_valid": False,
                    "redirected": False,
                    "status": "invalid_url_format",
                    "title": "",
                    "reason": "URL must start with http:// or https://",
                })
                invalid_urls.append(item_url)
                continue

            network_Attempted += 1
            try:
                info = _check_single_url(item_url)
                results.append(info)
                if info["is_valid"]:
                    valid_urls.append(info["final_url"])
                else:
                    invalid_urls.append(item_url)
            except Exception as exc:
                network_failed += 1
                last_exc = exc
                results.append({
                    "url": item_url,
                    "final_url": item_url,
                    "source": domain(item_url),
                    "status_code": 0,
                    "is_valid": False,
                    "redirected": False,
                    "status": "connection_error",
                    "title": "",
                    "reason": f"{type(exc).__name__}: {exc}",
                })
                invalid_urls.append(item_url)

        if network_Attempted > 0 and network_failed == network_Attempted and last_exc is not None:
            raise last_exc

        return {
            "tool": "validate_urls",
            "results": results,
            "valid_urls": valid_urls,
            "invalid_urls": invalid_urls,
        }
    except Exception as exc:
        return err("validate_urls", exc)
