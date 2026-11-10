"""Student Tool Unit Test Challenge & New Tool Tests.

Tested offline: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    res = TOOL_FUNCTIONS["clarify"](question="Chọn phương án?", response_type="choice", options=["A", "B"])
    assert res["options"] == ["A", "B"]
    assert res["awaiting_user"] is True
    assert res["response_type"] == "choice"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Item 1", "section": "A", "url": "https://example.com/1"},
        {"title": "Item 2", "section": "B", "url": "https://example.com/2"},
        {"title": "Item 3", "section": "A", "url": "https://example.com/3"},
    ]
    res = TOOL_FUNCTIONS["format"](items=items, template="sections")
    md = res["markdown"]
    assert md.count("## A") == 1
    assert md.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "Tweet 1", "summary": "First point"},
        {"title": "Tweet 2", "summary": "Second point"},
    ]
    res = TOOL_FUNCTIONS["format"](items=items, template="thread")
    assert "1/ First point" in res["markdown"]
    assert "2/ Second point" in res["markdown"]


def test_format_empty_items_does_not_crash() -> None:
    res1 = TOOL_FUNCTIONS["format"](items=None)
    assert res1["item_count"] == 0
    res2 = TOOL_FUNCTIONS["format"](items=[])
    assert res2["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:FAKE_TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-10099999")
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin công nghệ", confirmed=True)
    assert len(calls) == 1
    assert "123456:FAKE_TOKEN" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-10099999"
    assert calls[0]["json"]["text"] == "Bản tin công nghệ"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    TOOL_FUNCTIONS["lookup"](query="AI agents", timeframe=None)
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-fc-key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "# Heading\nSample text",
            "metadata": {"title": "Title Page", "sourceURL": "https://example.com/article"}
        }
    }))
    res = TOOL_FUNCTIONS["fetch"](url="https://example.com/article")
    assert res["items"][0]["title"] == "Title Page"
    assert res["items"][0]["url"] == "https://example.com/article"
    assert res["items"][0]["source"] == "example.com"
    assert "Sample text" in res["items"][0]["summary"]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-fc-key")
    long_md = "A" * 5500
    fake_http(FakeResponse({
        "data": {
            "markdown": long_md,
            "metadata": {"title": "Long Page", "sourceURL": "https://example.com/long"}
        }
    }))
    res = TOOL_FUNCTIONS["fetch"](url="https://example.com/long")
    assert len(res["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid-key")
    raw_tweets = [
        {"text": "No ID tweet"},
        {"id": "1", "text": "Tweet 1", "screen_name": "sama"},
        {"id": "2", "text": "Tweet 2", "screen_name": "sama"},
        {"id": "3", "text": "Tweet 3", "screen_name": "sama"},
        {"id": "4", "text": "Tweet 4", "screen_name": "sama"},
    ]
    fake_http(FakeResponse({"timeline": raw_tweets}))
    res = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=3)
    assert len(res["items"]) == 3
    for item in res["items"]:
        assert item["url"].startswith("https://x.com/sama/status/")


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid-key")
    calls = fake_http(FakeResponse({"tweets": []}))
    TOOL_FUNCTIONS["social_search"](query="DeepSeek", search_type="Top", limit=7)
    assert calls[0]["params"]["search_type"] == "Top"
    assert calls[0]["params"]["query"] == "DeepSeek"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    res = TOOL_FUNCTIONS["policy"](query="")
    assert res["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    res = TOOL_FUNCTIONS["policy"](query="privacy data", policy_area="data_privacy")
    assert len(res["results"]) > 0
    assert all(r["policy_area"] == "data_privacy" for r in res["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    res = TOOL_FUNCTIONS["policy"](query="injection probe", policy_area="source_citation")
    found_untrusted = any(len(r.get("untrusted_text", [])) > 0 for r in res["results"])
    assert found_untrusted


# ---------------- NEW TOOLS (Wikipedia, Calculator, Crypto) ----------------

# 1. Wikipedia tests
def test_wikipedia_happy_path(fake_http) -> None:
    fake_http(FakeResponse({
        "title": "Artificial Intelligence",
        "extract": "AI is the intelligence of machines.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Artificial_Intelligence"}}
    }))
    res = TOOL_FUNCTIONS["wikipedia"](title="Artificial Intelligence", language="en")
    assert res["title"] == "Artificial Intelligence"
    assert res["items"][0]["summary"] == "AI is the intelligence of machines."
    assert res["items"][0]["url"] == "https://en.wikipedia.org/wiki/Artificial_Intelligence"


def test_wikipedia_empty_title_returns_error_dict() -> None:
    res = TOOL_FUNCTIONS["wikipedia"](title="")
    assert "error" in res or res.get("items") == []


def test_wikipedia_not_found_returns_empty_items(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    res = TOOL_FUNCTIONS["wikipedia"](title="NonExistentTopic12345XYZ")
    assert res["items"] == []


# 2. Calculator tests
def test_calculator_evaluates_basic_expression() -> None:
    res = TOOL_FUNCTIONS["calculator"](expression="(15 + 5) * 4 / 2")
    assert res["result"] == 40.0


def test_calculator_math_functions() -> None:
    res = TOOL_FUNCTIONS["calculator"](expression="sqrt(144) + pow(2, 3)")
    assert res["result"] == 20.0


def test_calculator_empty_or_invalid_returns_error() -> None:
    res1 = TOOL_FUNCTIONS["calculator"](expression="")
    assert res1["error"] == "Empty expression"
    res2 = TOOL_FUNCTIONS["calculator"](expression="invalid + syntax @#$")
    assert "error" in res2


# 3. Crypto Price tests
def test_crypto_price_happy_path(fake_http) -> None:
    fake_http(FakeResponse({"bitcoin": {"usd": 98500}}))
    res = TOOL_FUNCTIONS["crypto_price"](coin_id="bitcoin", currency="usd")
    assert res["price"] == 98500
    assert res["formatted"] == "98500 USD"


def test_crypto_price_not_found(fake_http) -> None:
    fake_http(FakeResponse({}))
    res = TOOL_FUNCTIONS["crypto_price"](coin_id="unknown_coin", currency="usd")
    assert res["price"] is None
    assert "Price not found" in res["message"]


def test_crypto_price_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    res = TOOL_FUNCTIONS["crypto_price"](coin_id="bitcoin")
    assert res["error"] == "HTTPError"
