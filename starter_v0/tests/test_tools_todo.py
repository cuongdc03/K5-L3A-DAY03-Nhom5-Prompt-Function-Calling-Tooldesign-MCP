"""Tool Unit Test Challenge — completed unit tests for built-in tools and 4 new team tools
(`hackernews`, `datetime_now`, `wikipedia`, `crypto_price`).

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
hackernews_tool = TOOL_FUNCTIONS["hackernews"]
datetime_now_tool = TOOL_FUNCTIONS["datetime_now"]
wikipedia_tool = TOOL_FUNCTIONS["wikipedia"]
crypto_price_tool = TOOL_FUNCTIONS["crypto_price"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify_tool(
        question="Bạn muốn tìm nguồn nào?",
        response_type="choice",
        options=["Web", "Twitter"],
    )
    assert result["question"] == "Bạn muốn tìm nguồn nào?"
    assert result["response_type"] == "choice"
    assert result["options"] == ["Web", "Twitter"]
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Item 1", "section": "A", "url": "https://a.com/1"},
        {"title": "Item 2", "section": "B", "url": "https://b.com/2"},
        {"title": "Item 3", "section": "A", "url": "https://a.com/3"},
    ]
    result = format_tool(items=items, template="sections", headline="Bản tin")
    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "First post", "url": "https://example.com/1"},
        {"title": "Second post", "url": "https://example.com/2"},
    ]
    result = format_tool(items=items, template="thread")
    lines = [line for line in result["markdown"].split("\n\n") if line.strip()]
    assert lines[0].startswith("1/ ")
    assert lines[1].startswith("2/ ")


def test_format_empty_items_does_not_crash() -> None:
    res_none = format_tool(items=None, template="bullets")
    res_empty = format_tool(items=[], template="sections")
    assert res_none["item_count"] == 0
    assert res_empty["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999888")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "123456:ABC-DEF" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100999888"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send_tool(text="Bản tin AI", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", topic="general", timeframe=None, max_results=2)

    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert result["timeframe"] is None


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({
        "data": {
            "markdown": "Nội dung bài viết chi tiết",
            "metadata": {"title": "Bài viết AI", "sourceURL": "https://www.openai.com/research"},
        }
    }))

    result = fetch_tool(url="https://www.openai.com/research")

    assert len(calls) == 1
    assert result["items"][0] == {
        "title": "Bài viết AI",
        "url": "https://www.openai.com/research",
        "source": "openai.com",
        "summary": "Nội dung bài viết chi tiết",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({
        "data": {
            "markdown": "a" * 5500,
            "metadata": {"title": "Long Doc", "sourceURL": "https://example.com/long"},
        }
    }))

    result = fetch_tool(url="https://example.com/long")

    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    raw_timeline = [{"text": "Missing id tweet", "screen_name": "sama"}] + [
        {"tweet_id": str(100 + i), "screen_name": "sama", "text": f"Tweet {i}"}
        for i in range(6)
    ]
    fake_http(FakeResponse({"timeline": raw_timeline}))

    result = timeline_tool(screenname="sama", limit=3)

    assert len(result["items"]) == 3
    for idx, item in enumerate(result["items"]):
        assert item["url"] == f"https://x.com/sama/status/{100 + idx}"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    calls = fake_http(FakeResponse({"timeline": []}))

    social_search_tool(query="OpenAI", search_type="Top", limit=4)

    assert len(calls) == 1
    assert calls[0]["params"]["query"] == "OpenAI"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = policy_tool(query="", policy_area="all")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="API key customer data prompt", policy_area="data_privacy")
    assert len(result["results"]) >= 1
    for item in result["results"]:
        assert item["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="injection probe", policy_area="source_citation", top_k=5)
    probe_sections = [r for r in result["results"] if r["section"] == "Injection probe"]
    assert len(probe_sections) == 1
    probe = probe_sections[0]
    assert any("ignore the citation policy" in line for line in probe["untrusted_text"])
    assert "ignore the citation policy" not in probe["facts"]


# ---------------- NEW TOOL 1: hackernews ----------------

def test_hackernews_happy_path_maps_algolia_hits(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "hits": [
            {
                "objectID": "40001",
                "title": "Show HN: Local AI Research Agent",
                "url": "https://github.com/example/agent",
                "points": 250,
                "num_comments": 84,
                "author": "ducanh",
                "created_at": "2026-11-10T08:00:00Z",
            }
        ]
    }))

    result = hackernews_tool(query="AI Research Agent", sort_by="relevance", max_results=3)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"]["query"] == "AI Research Agent"
    assert calls[0]["params"]["hitsPerPage"] == 3
    assert result["items"][0]["title"] == "Show HN: Local AI Research Agent"
    assert result["items"][0]["source"] == "github.com"
    assert result["items"][0]["points"] == 250
    assert result["items"][0]["hn_url"] == "https://news.ycombinator.com/item?id=40001"


def test_hackernews_bad_input_empty_query_returns_error_dict(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    result = hackernews_tool(query="   ", sort_by="invalid_enum", max_results=5)

    assert result["error"] == "ValueError"
    assert "query" in result["message"].lower()
    assert calls == []


def test_hackernews_http_failure_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))

    result = hackernews_tool(query="OpenAI", sort_by="date", max_results=5)

    assert result["error"] == "HTTPError"
    assert "503" in result["message"]


# ---------------- NEW TOOL 2: datetime_now ----------------

def test_datetime_now_returns_expected_fields_for_valid_timezone() -> None:
    result = datetime_now_tool(timezone="Asia/Ho_Chi_Minh")
    assert result["tool"] == "get_current_datetime"
    assert result["timezone"] == "Asia/Ho_Chi_Minh"
    assert result["utc_offset"] == "+07:00"
    assert "date" in result and "time" in result and "weekday_vi" in result


def test_datetime_now_empty_timezone_falls_back_to_default() -> None:
    result = datetime_now_tool(timezone="   ")
    assert result["timezone"] == "Asia/Ho_Chi_Minh"
    assert result["utc_offset"] == "+07:00"


def test_datetime_now_invalid_timezone_returns_error_dict() -> None:
    result = datetime_now_tool(timezone="Mars/Phobos")
    assert "error" in result
    assert "Unknown timezone" in result["message"]


# ---------------- NEW TOOL 3: wikipedia ----------------

def test_wikipedia_happy_path_maps_summary_response(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Artificial intelligence",
        "extract": "AI is intelligence demonstrated by machines.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Artificial_intelligence"}},
    }))

    result = wikipedia_tool(title="Artificial intelligence", language="en")

    assert len(calls) == 1
    assert "en.wikipedia.org/api/rest_v1/page/summary/Artificial_intelligence" in calls[0]["url"]
    assert result["items"][0]["title"] == "Artificial intelligence"
    assert result["items"][0]["summary"] == "AI is intelligence demonstrated by machines."


def test_wikipedia_bad_input_empty_title_returns_error_dict(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    result = wikipedia_tool(title="   ", language="invalid_lang")
    assert result["error"] == "ValueError"
    assert calls == []


def test_wikipedia_http_failure_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    result = wikipedia_tool(title="OpenAI", language="en")
    assert result["error"] == "HTTPError"


# ---------------- NEW TOOL 4: crypto_price ----------------

def test_crypto_price_happy_path_returns_formatted_price(fake_http) -> None:
    calls = fake_http(FakeResponse({"bitcoin": {"usd": 92500}}))
    result = crypto_price_tool(coin_id="Bitcoin", currency="USD")
    assert len(calls) == 1
    assert calls[0]["params"] == {"ids": "bitcoin", "vs_currencies": "usd"}
    assert result["price"] == 92500
    assert result["formatted"] == "92500 USD"


def test_crypto_price_bad_input_empty_coin_returns_error_dict(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    result = crypto_price_tool(coin_id="   ", currency="usd")
    assert result["error"] == "ValueError"
    assert calls == []


def test_crypto_price_http_failure_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    result = crypto_price_tool(coin_id="ethereum", currency="usd")
    assert result["error"] == "HTTPError"
