"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py

Reuses chat.py's multi-round tool loop and writes the same transcript JSON
(transcripts/*.transcript.json), so UI sessions count as live chats for the report.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    execute_tool_call,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"

EXAMPLES = [
    "Tin mới nhất về OpenAI trong tuần này?",
    "Sam Altman vừa đăng gì trên X?",
    "Tóm tắt bài này giúp mình",
    "Tìm paper arXiv về AI agent evaluation",
]

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")


# ---------------------------------------------------------------- state ----
def new_session(provider_name: str, model: str | None, version: str) -> None:
    """Reset chat state and start a fresh transcript."""
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    transcript_id = "_".join([
        safe_slug(version),
        safe_slug(provider_name),
        datetime.now().strftime("%Y%m%dT%H%M%S%f"),
    ])
    st.session_state.update(
        messages=[],          # what is rendered
        history=[],           # what is sent to the model (user/assistant text only)
        turn_index=0,
        pending_send=None,    # {"text": ...} awaiting human approval
        transcript_path=TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json",
        transcript={
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact_version),
            "provider": provider_name,
            "model": model,
            "system_prompt": str(SYSTEM_PROMPT_PATH),
            "tools": str(TOOLS_PATH),
            "interface": "streamlit",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        },
    )


def save_transcript() -> None:
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)


# ----------------------------------------------------------- tool guard ----
def guarded_executor(pending: list[str]):
    """Run tools, but never let the model send to Telegram by itself.

    `send` is forced to confirmed=False; the text is parked for human approval
    in the UI. This enforces confirmation regardless of what the prompt says.
    """
    def run(call: ToolCall) -> dict[str, Any]:
        if call.name == "send":
            pending.append(str(call.args.get("text", "")))
            safe_call = ToolCall(name="send", args={**call.args, "confirmed": False})
            return execute_tool_call(safe_call)
        return execute_tool_call(call)
    return run


# ------------------------------------------------------------ rendering ----
def render_events(events: list[dict[str, Any]]) -> None:
    for event in events:
        result = event.get("result", {})
        failed = isinstance(result, dict) and "error" in result
        icon = "❌" if failed else "🔧"
        args = ", ".join(f"{k}={v!r}" for k, v in (event.get("args") or {}).items())
        with st.expander(f"{icon} {event['tool']}({args[:120]})", expanded=False):
            st.json(result, expanded=1)


def render_message(msg: dict[str, Any]) -> None:
    with st.chat_message(msg["role"], avatar="🔎" if msg["role"] == "assistant" else None):
        if msg.get("status") == "waiting_for_user":
            st.caption("❓ The agent needs more information")
        elif msg.get("status") == "max_tool_rounds":
            st.caption("⚠️ Stopped at the tool-round limit")
        elif msg.get("status") == "provider_error":
            st.error(msg["content"])
            return
        if msg.get("events"):
            render_events(msg["events"])
        st.markdown(msg["content"])


# -------------------------------------------------------------- sidebar ----
with st.sidebar:
    st.title("🔎 Research Agent")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model (blank = provider default)", value="").strip() or None
    version = st.text_input("Version label", value="v0")
    history_window = st.slider("History window (turns)", 0, 10, 5)
    max_rounds = st.slider("Max tool rounds", 1, 10, 6)
    if "messages" not in st.session_state:
        new_session(provider_name, model, version)
    if st.button("🗑️ New chat", use_container_width=True):
        new_session(provider_name, model, version)
        st.rerun()

    st.divider()
    st.caption("Tools available")
    try:
        for decl in load_tool_declarations(TOOLS_PATH):
            with st.expander(decl["name"]):
                st.write(decl.get("description", ""))
    except Exception as exc:  # bad YAML while editing tools.yaml
        st.error(f"Cannot read tools.yaml: {exc}")
    st.divider()
    st.caption(f"Transcript: `{st.session_state.transcript_path.name}`")
    st.caption(f"Artifact: `{st.session_state.transcript['artifact_version']}`")


# ----------------------------------------------------------------- main ----
st.header("Research Agent")
st.caption("Ask for news, posts, web pages, papers, or company policy. Tool calls appear under each answer.")

for message in st.session_state.messages:
    render_message(message)

if not st.session_state.messages:
    cols = st.columns(len(EXAMPLES))
    for col, example in zip(cols, EXAMPLES):
        if col.button(example, use_container_width=True):
            st.session_state.queued = example
            st.rerun()

# Human-in-the-loop approval for Telegram sends.
pending = st.session_state.pending_send
if pending:
    with st.container(border=True):
        st.warning("📨 The agent wants to post this to Telegram. Nothing was sent yet.")
        st.markdown(pending["text"] or "_(empty message)_")
        approve, cancel, _ = st.columns([1, 1, 4])
        if approve.button("✅ Send", type="primary"):
            result = TOOL_FUNCTIONS["send"](text=pending["text"], confirmed=True)
            ok = isinstance(result, dict) and result.get("status") == "sent"
            note = "📨 Sent to Telegram." if ok else f"❌ Telegram send failed: {result.get('message', result)}"
            st.session_state.messages.append({"role": "assistant", "content": note})
            st.session_state.history.append({"role": "user", "content": "[UI] I approved the Telegram message."})
            st.session_state.history.append({"role": "assistant", "content": note})
            st.session_state.transcript["turns"].append({
                "type": "ui_action", "action": "approve_send", "at": now_iso(),
                "text": pending["text"], "result": result,
            })
            st.session_state.pending_send = None
            save_transcript()
            st.rerun()
        if cancel.button("🚫 Cancel"):
            st.session_state.messages.append({"role": "assistant", "content": "Cancelled. Nothing was sent."})
            st.session_state.history.append({"role": "user", "content": "[UI] I cancelled the Telegram message."})
            st.session_state.history.append({"role": "assistant", "content": "Cancelled. Nothing was sent."})
            st.session_state.transcript["turns"].append({
                "type": "ui_action", "action": "cancel_send", "at": now_iso(), "text": pending["text"],
            })
            st.session_state.pending_send = None
            save_transcript()
            st.rerun()

user_text = st.chat_input("Ask the research agent…") or st.session_state.pop("queued", None)

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    render_message(st.session_state.messages[-1])
    st.session_state.turn_index += 1
    turn: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    reply: dict[str, Any]
    try:
        provider = make_provider(provider_name)
        tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))
        system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(st.session_state.history, history_window),
            {"role": "user", "content": user_text},
        ]
        sends: list[str] = []
        with st.chat_message("assistant", avatar="🔎"):
            with st.spinner("Thinking and calling tools…"):
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=tools,
                    model=model,
                    max_tool_rounds=max_rounds,
                    tool_executor=guarded_executor(sends),
                )
        turn.update(result)
        if sends:
            st.session_state.pending_send = {"text": sends[-1]}
        st.session_state.history.append({"role": "user", "content": user_text})
        st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
        reply = {
            "role": "assistant",
            "content": result["assistant_text"] or "_(no text)_",
            "events": result["tool_events"],
            "status": result["status"],
        }
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        turn.update({"status": "provider_error", "error": error})
        reply = {"role": "assistant", "content": error, "status": "provider_error"}

    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn)
    st.session_state.messages.append(reply)
    save_transcript()
    st.rerun()
