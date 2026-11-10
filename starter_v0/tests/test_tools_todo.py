"""Tool Unit Test Challenge — completed unit tests for built-in tools and new tool (`hackernews`).

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


# ---------------- YOUR NEW TOOL: hackernews ----------------

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


# ---------------- deduplicate (new core tool) ----------------

def test_deduplicate_removes_url_duplicates_and_preserves_order() -> None:
    items = [
        {"title": "First", "url": "https://Example.com/story/#top"},
        {"title": "Duplicate", "url": "https://example.com/story"},
        {"title": "Other", "url": "https://example.com/other"},
    ]

    result = TOOL_FUNCTIONS["deduplicate"](items=items)

    assert result["item_count"] == 2
    assert result["duplicate_count"] == 1
    assert result["items"] == [items[0], items[2]]


def test_deduplicate_rejects_non_list_input() -> None:
    result = TOOL_FUNCTIONS["deduplicate"](items="not a list")

    assert result["error"] == "ValueError"
    assert result["message"] == "items must be a list"


def test_deduplicate_rejects_non_object_item() -> None:
    result = TOOL_FUNCTIONS["deduplicate"](items=[{"title": "Valid"}, "invalid"])

    assert result["error"] == "ValueError"
    assert result["message"] == "every item must be an object"


# ---------------- wiki (new bonus tool) ----------------

from tools.github_search.tool import github_search  # noqa: E402
from tools.wiki.tool import wiki_summary  # noqa: E402


def test_wiki_sends_search_request_and_orders_pages_by_index(fake_http) -> None:
    calls = fake_http(FakeResponse({"query": {"pages": {
        "2": {"index": 2, "title": "Transformer (deep learning)", "fullurl": "https://en.wikipedia.org/wiki/T2", "extract": "Second. "},
        "1": {"index": 1, "title": "Attention (machine learning)", "fullurl": "https://en.wikipedia.org/wiki/A1", "extract": " First."},
    }}}))

    result = wiki_summary(query="transformer model", lang="en", limit=2)

    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[0]["params"]["gsrsearch"] == "transformer model"
    assert calls[0]["params"]["gsrlimit"] == 2
    assert "User-Agent" in calls[0]["headers"]
    assert [item["title"] for item in result["items"]] == ["Attention (machine learning)", "Transformer (deep learning)"]
    assert result["items"][0] == {
        "title": "Attention (machine learning)", "url": "https://en.wikipedia.org/wiki/A1",
        "source": "en.wikipedia.org", "summary": "First.",
    }


def test_wiki_vietnamese_lang_uses_vi_domain_and_clamps_limit(fake_http) -> None:
    calls = fake_http(FakeResponse({"query": {"pages": {}}}))

    result = wiki_summary(query="Trí tuệ nhân tạo", lang="VI", limit="50")

    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert calls[0]["params"]["gsrlimit"] == 5
    assert result["items"] == []


def test_wiki_empty_query_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))

    result = wiki_summary(query="   ")

    assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_unsupported_lang_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))

    result = wiki_summary(query="AI", lang="fr")

    assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert wiki_summary(query="AI")["error"] == "HTTPError"


def test_wiki_is_registered_in_tool_registry() -> None:
    assert TOOL_FUNCTIONS["wiki"] is wiki_summary


# ---------------- github_search (new bonus tool) ----------------

def test_github_search_builds_query_with_language_and_maps_repos(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = fake_http(FakeResponse({"items": [
        {"full_name": "org/agent-kit", "html_url": "https://github.com/org/agent-kit", "description": None,
         "stargazers_count": 4200, "language": "Python", "pushed_at": "2026-11-01T00:00:00Z"},
    ]}))

    result = github_search(query="llm agent", language="Python", limit=1)

    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "llm agent language:Python", "per_page": 1, "sort": "stars", "order": "desc"}
    assert "Authorization" not in calls[0]["headers"]
    assert result["items"] == [{
        "title": "org/agent-kit", "url": "https://github.com/org/agent-kit", "summary": "",
        "stars": 4200, "language": "Python", "updated_at": "2026-11-01T00:00:00Z",
    }]


def test_github_search_best_match_omits_sort_and_uses_token(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    calls = fake_http(FakeResponse({"items": []}))

    github_search(query="mcp server", sort="best_match")

    assert "sort" not in calls[0]["params"]
    assert calls[0]["headers"]["Authorization"] == "Bearer test-token"


def test_github_search_invalid_input_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))

    assert github_search(query="")["error"] == "ValueError"
    assert github_search(query="agent", sort="forks")["error"] == "ValueError"
    assert calls == []


def test_github_search_rate_limit_returns_error_dict(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fake_http(FakeResponse(status_code=403))
    assert github_search(query="agent")["error"] == "HTTPError"
