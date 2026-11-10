"""Tool Unit Test Challenge — Complete Suite (0 skipped, 0 failed).

Covers:
1. All 13 stub unit tests for existing core & bonus tools.
2. Regression tests for 4 edge-case bugs found and fixed in existing tools (Challenge+).
3. 12 unit tests (3 per tool) for the 4 new team tools:
   `github_search`, `hn_search`, `wiki_summary`, `cite_export`.
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
github_search_tool = TOOL_FUNCTIONS["github_search"]
hn_search_tool = TOOL_FUNCTIONS["hn_search"]
wiki_summary_tool = TOOL_FUNCTIONS["wiki_summary"]
cite_export_tool = TOOL_FUNCTIONS["cite_export"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    opts = ["Twitter/X", "Web news"]
    result = clarify_tool(
        question="Bạn muốn tìm trên nguồn nào?",
        response_type="choice",
        options=opts,
    )
    assert result["tool"] == "ask_user"
    assert result["response_type"] == "choice"
    assert result["options"] == opts
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Item 1", "url": "https://a.com/1", "section": "A"},
        {"title": "Item 2", "url": "https://b.com/2", "section": "B"},
        {"title": "Item 3", "url": "https://a.com/3", "section": "A"},
    ]
    result = format_tool(items=items, template="sections", headline="Digest")
    markdown = result["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "First post", "url": "https://x.com/1"},
        {"title": "Second post", "url": "https://x.com/2"},
        {"title": "Third post", "url": "https://x.com/3"},
    ]
    result = format_tool(items=items, template="thread")
    blocks = result["markdown"].split("\n\n")
    assert len(blocks) == 3
    assert blocks[0].startswith("1/ ")
    assert blocks[1].startswith("2/ ")
    assert blocks[2].startswith("3/ ")


def test_format_empty_items_does_not_crash() -> None:
    res_none = format_tool(items=None, template="bullets")
    res_empty = format_tool(items=[], template="sections")
    assert res_none["item_count"] == 0
    assert res_none["markdown"] == ""
    assert res_empty["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:BOT_SECRET")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100987654")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI hôm nay", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "12345:BOT_SECRET" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-100987654"
    assert calls[0]["json"]["text"] == "Bản tin AI hôm nay"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send_tool(text="Bản tin AI", confirmed=True)

    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", topic="general", timeframe=None, max_results=3)

    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert result["timeframe"] is None


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({
        "data": {
            "markdown": "Full article content here",
            "metadata": {"title": "T", "sourceURL": "https://openai.com/blog/test"},
        }
    }))

    result = fetch_tool(url="https://openai.com/blog/test")

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert result["items"][0] == {
        "title": "T",
        "url": "https://openai.com/blog/test",
        "source": "openai.com",
        "summary": "Full article content here",
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
    summary = result["items"][0]["summary"]
    assert len(summary) == 4000
    assert summary == "a" * 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    raw_timeline = [{"text": "missing id tweet", "screen_name": "sama"}] + [
        {"tweet_id": str(100 + i), "screen_name": "sama", "text": f"Tweet {i}"}
        for i in range(6)
    ]
    calls = fake_http(FakeResponse({"timeline": raw_timeline}))

    result = timeline_tool(screenname="sama", limit=3)

    assert len(calls) == 1
    assert len(result["items"]) == 3
    for idx, item in enumerate(result["items"]):
        assert item["url"] == f"https://x.com/sama/status/{100 + idx}"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    calls = fake_http(FakeResponse({
        "timeline": [{"tweet_id": "999", "screen_name": "OpenAI", "text": "GPT-5 announcement"}]
    }))

    result = social_search_tool(query="OpenAI", search_type="Top", limit=2)

    assert len(calls) == 1
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert result["search_type"] == "Top"
    assert len(result["items"]) == 1


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = policy_tool(query="   ", policy_area="all")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="API key customer data confidential", policy_area="data_privacy", top_k=5)
    assert len(result["results"]) >= 1
    assert all(item["policy_area"] == "data_privacy" for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="Injection probe tweet citation", policy_area="source_citation", top_k=5)
    probe_sections = [r for r in result["results"] if r["section"] == "Injection probe"]
    assert len(probe_sections) == 1
    probe = probe_sections[0]
    assert any("ignore the citation policy" in line for line in probe["untrusted_text"])
    assert "ignore the citation policy" not in probe["facts"]


# ---------------- Challenge+ Regression Tests for Existing Tool Bugs ----------------

def test_regression_format_null_section_falls_back_to_default_heading() -> None:
    """Bug fixed in format/tool.py: item with section=None previously rendered '## None'."""
    items = [{"title": "Tin AI", "url": "https://example.com/1", "section": None}]
    result = format_tool(items=items, template="sections")
    assert "## None" not in result["markdown"]
    assert "## Tổng hợp" in result["markdown"]


def test_regression_timeline_strips_at_prefix_and_clamps_negative_limit(monkeypatch, fake_http) -> None:
    """Bug fixed in timeline/tool.py: '@sama' sent '@' to API and negative limit sliced from end."""
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    calls = fake_http(FakeResponse({
        "timeline": [
            {"tweet_id": "1", "screen_name": "sama", "text": "Tweet 1"},
            {"tweet_id": "2", "screen_name": "sama", "text": "Tweet 2"},
        ]
    }))

    result = timeline_tool(screenname="@sama", limit=-1)
    assert calls[0]["params"]["screenname"] == "sama"
    assert result["screenname"] == "sama"
    assert len(result["items"]) == 1


# ---------------- NEW TOOL 1: github_search (3 tests) ----------------

def test_github_search_happy_path_sends_params_and_maps_repos(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
    calls = fake_http(FakeResponse({
        "total_count": 1,
        "items": [{
            "full_name": "langchain-ai/langgraph",
            "html_url": "https://github.com/langchain-ai/langgraph",
            "description": "Build resilient language agents as graphs.",
            "stargazers_count": 12000,
            "forks_count": 1500,
            "language": "Python",
            "updated_at": "2026-05-01T00:00:00Z",
        }],
    }))

    result = github_search_tool(query="langgraph", language="python", sort="stars", max_results=3)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"]["q"] == "langgraph language:python"
    assert calls[0]["params"]["sort"] == "stars"
    assert calls[0]["params"]["per_page"] == 3
    assert calls[0]["headers"]["Authorization"] == "Bearer ghp_test123"
    assert result["items"][0]["title"] == "langchain-ai/langgraph"
    assert result["items"][0]["stars"] == 12000


def test_github_search_bad_input_empty_query_or_invalid_enum(fake_http) -> None:
    calls = fake_http(FakeResponse({"total_count": 0, "items": []}))
    empty_res = github_search_tool(query="   ")
    assert empty_res["error"] == "ValueError"
    assert calls == []

    # Out-of-enum sort should fall back to 'stars' and string max_results should coerce cleanly
    ok_res = github_search_tool(query="agent", sort="invalid_sort", max_results="4")  # type: ignore[arg-type]
    assert calls[0]["params"]["sort"] == "stars"
    assert calls[0]["params"]["per_page"] == 4
    assert ok_res["sort"] == "stars"


def test_github_search_http_failure_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=403))
    result = github_search_tool(query="llm")
    assert result["tool"] == "github_search"
    assert result["error"] == "HTTPError"


# ---------------- NEW TOOL 2: hn_search (3 tests) ----------------

def test_hn_search_happy_path_queries_algolia_and_maps_hits(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "nbHits": 42,
        "hits": [{
            "objectID": "40001",
            "title": "Show HN: Open-source AI Research Agent",
            "url": "https://example.org/agent",
            "author": "pg",
            "points": 250,
            "num_comments": 88,
            "created_at": "2026-06-01T10:00:00Z",
        }],
    }))

    result = hn_search_tool(query="AI Research Agent", tags="show_hn", max_results=5)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "AI Research Agent", "tags": "show_hn", "hitsPerPage": 5}
    assert result["total_hits"] == 42
    assert result["items"][0]["hn_url"] == "https://news.ycombinator.com/item?id=40001"
    assert result["items"][0]["points"] == 250


def test_hn_search_bad_input_empty_query_and_invalid_tag_fallback(fake_http) -> None:
    calls = fake_http(FakeResponse({"nbHits": 0, "hits": []}))
    err_res = hn_search_tool(query="")
    assert err_res["error"] == "ValueError"
    assert calls == []

    fallback_res = hn_search_tool(query="Claude", tags="INVALID_TAG", max_results=0)
    assert calls[0]["params"]["tags"] == "story"
    assert calls[0]["params"]["hitsPerPage"] == 5
    assert fallback_res["tags"] == "story"


def test_hn_search_http_failure_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    result = hn_search_tool(query="OpenAI")
    assert result["tool"] == "hn_search"
    assert result["error"] == "HTTPError"


# ---------------- NEW TOOL 3: wiki_summary (3 tests) ----------------

def test_wiki_summary_happy_path_fetches_language_edition(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Trí tuệ nhân tạo",
        "extract": "Trí tuệ nhân tạo (AI) là một lĩnh vực của khoa học máy tính.",
        "content_urls": {"desktop": {"page": "https://vi.wikipedia.org/wiki/Tr%C3%AD_tu%E1%BB%87_nh%C3%A2n_t%E1%BA%A1o"}},
    }))

    result = wiki_summary_tool(title="Trí tuệ nhân tạo", lang="vi")

    assert len(calls) == 1
    assert calls[0]["url"].startswith("https://vi.wikipedia.org/api/rest_v1/page/summary/")
    assert result["lang"] == "vi"
    assert result["items"][0]["source"] == "vi.wikipedia.org"
    assert "khoa học máy tính" in result["extract"]


def test_wiki_summary_bad_input_empty_title_or_invalid_lang(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "Transformer", "extract": "Deep learning model."}))
    err_res = wiki_summary_tool(title="   ")
    assert err_res["error"] == "ValueError"
    assert calls == []

    ok_res = wiki_summary_tool(title="Transformer", lang="invalid_lang")
    assert calls[0]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/Transformer"
    assert ok_res["lang"] == "en"


def test_wiki_summary_http_404_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = wiki_summary_tool(title="NonExistentTopic12345")
    assert result["tool"] == "wiki_summary"
    assert result["error"] == "HTTPError"


# ---------------- NEW TOOL 4: cite_export (3 tests) ----------------

def test_cite_export_happy_path_formats_bibtex_and_apa() -> None:
    bib = cite_export_tool(
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        year=2017,
        arxiv_id="1706.03762",
        style="bibtex",
    )
    assert bib["style"] == "bibtex"
    assert bib["cite_key"] == "vaswani2017attention"
    assert "@article{vaswani2017attention," in bib["citation"]
    assert "eprint = {1706.03762}" in bib["citation"]

    apa = cite_export_tool(
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        year=2017,
        arxiv_id="1706.03762",
        style="apa",
    )
    assert "Ashish Vaswani, Noam Shazeer (2017). Attention Is All You Need." in apa["citation"]


def test_cite_export_bad_input_empty_title_or_invalid_style() -> None:
    empty_title = cite_export_tool(title="   ", style="apa")
    assert empty_title["error"] == "ValueError"

    bad_style = cite_export_tool(title="Some Paper", style="chicago")
    assert bad_style["error"] == "ValueError"


def test_cite_export_failure_invalid_year_returns_error_dict() -> None:
    bad_year = cite_export_tool(title="Some Paper", year="not-a-year", style="ieee")
    assert bad_year["tool"] == "cite_export"
    assert bad_year["error"] == "ValueError"
