"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    pytest.skip(TODO)


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    pytest.skip(TODO)


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    pytest.skip(TODO)


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    pytest.skip(TODO)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    pytest.skip(TODO)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds (datetime_now below has 4 test functions):
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

# ---- datetime_now (team tool) ----
# Time is frozen by patching the tool's single clock function `_now`.

from datetime import datetime  # noqa: E402

import tools.datetime_now.tool as datetime_tool  # noqa: E402


@pytest.fixture
def frozen_now(monkeypatch: pytest.MonkeyPatch):
    """Freeze the clock at 2026-11-10 (a Tuesday) 03:30 UTC."""
    from datetime import timezone as dt_timezone

    fixed_utc = datetime(2026, 11, 10, 3, 30, 0, tzinfo=dt_timezone.utc)
    monkeypatch.setattr(datetime_tool, "_now", lambda tz: fixed_utc.astimezone(tz))


def test_datetime_now_defaults_to_vietnam_time_with_week_bounds(frozen_now) -> None:
    result = TOOL_FUNCTIONS["datetime_now"]()

    assert result["timezone"] == "Asia/Ho_Chi_Minh"
    assert result["iso"] == "2026-11-10T10:30:00+07:00"
    assert result["weekday"] == "Tuesday" and result["weekday_vi"] == "Thứ Ba"
    assert result["utc_offset"] == "+07:00"
    assert (result["week_start"], result["week_end"]) == ("2026-11-09", "2026-11-15")


def test_datetime_now_converts_to_requested_timezone(frozen_now) -> None:
    result = TOOL_FUNCTIONS["datetime_now"](timezone="America/New_York")

    assert result["timezone"] == "America/New_York"
    assert result["date"] == "2026-11-09"          # still Monday evening in New York
    assert result["time"] == "22:30:00"
    assert result["weekday"] == "Monday"


@pytest.mark.parametrize("bad", ["", "   ", None, 42])
def test_datetime_now_bad_input_falls_back_to_default(frozen_now, bad) -> None:
    result = TOOL_FUNCTIONS["datetime_now"](timezone=bad)

    assert "error" not in result
    assert result["timezone"] == "Asia/Ho_Chi_Minh"


@pytest.mark.parametrize("bad", ["Mars/Base", "GMT+7", "../etc/passwd"])
def test_datetime_now_unknown_timezone_returns_error_dict_not_exception(bad) -> None:
    result = TOOL_FUNCTIONS["datetime_now"](timezone=bad)

    assert result["error"]
    assert bad in result["message"] and "IANA" in result["message"]
    assert "iso" not in result
