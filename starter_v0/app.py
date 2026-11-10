from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# Setup import paths
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import (
    run_model_tool_loop,
    trim_history,
    write_transcript,
    now_iso,
    safe_slug,
    ARTIFACTS_DIR,
)

# Load environment
load_lab_env(APP_DIR)
TRANSCRIPTS_DIR = APP_DIR / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------- Streamlit Page Configuration -----------------
st.set_page_config(
    page_title="Research Agent Workspace - Day 03 Lab v2",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- Modern Light Green (Xanh Lá Nhạt) Design System -----------------
st.markdown("""
<style>
    /* Global Background & Font */
    .stApp {
        background-color: #F8FAF9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Top Hero Header Card */
    .hero-banner {
        background: linear-gradient(135deg, #ECFDF5 0%, #E6F4EA 50%, #D1FAE5 100%);
        border: 1px solid #A7F3D0;
        border-radius: 16px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.08);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #065F46;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #047857;
        margin-top: 0.4rem;
        margin-bottom: 0.8rem;
    }

    /* Status Badges */
    .badge-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #FFFFFF;
        color: #065F46;
        border: 1px solid #6EE7B7;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-right: 0.5rem;
    }

    /* Column-based Chat Alignment */
    /* User Message Bubble (Right Column) */
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stChatMessage"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        border-radius: 18px 18px 4px 18px !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
        border: none !important;
        padding: 0.9rem 1.2rem !important;
    }
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stChatMessage"] p,
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stChatMessage"] span,
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stChatMessage"] div {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }

    /* Assistant Message Bubble (Left Column) */
    div[data-testid="stColumn"]:nth-child(1) div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1FAE5 !important;
        border-left: 5px solid #10B981 !important;
        border-radius: 18px 18px 18px 4px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
        padding: 1.1rem 1.3rem !important;
    }

    /* Tool Call Execution Card */
    .tool-exec-card {
        background-color: #F0FDF4;
        border: 1px solid #A7F3D0;
        border-left: 4px solid #059669;
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
        margin: 0.6rem 0;
    }
    .tool-badge-pill {
        background: #DCFCE7;
        color: #065F46;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        border: 1px solid #86EFAC;
    }

    /* Quick Prompt Cards */
    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #A7F3D0;
        background-color: #FFFFFF;
        color: #065F46;
        font-weight: 600;
        padding: 0.5rem 0.8rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div.stButton > button:hover:not(:disabled) {
        background-color: #ECFDF5;
        border-color: #34D399;
        color: #047857;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.15);
    }
    div.stButton > button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    /* Primary Action Buttons */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: #FFFFFF;
        border: none;
        box-shadow: 0 3px 8px rgba(16, 185, 129, 0.3);
    }
    div.stButton > button[kind="primary"]:hover:not(:disabled) {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: #FFFFFF;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F2FBF6;
        border-right: 1px solid #E2E8F0;
    }

    /* Pulsing Running Glow */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .running-pulse {
        animation: pulseGlow 1.5s infinite;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ----------------- State Management -----------------
def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "raw_history" not in st.session_state:
        st.session_state.raw_history = []
    if "turn_index" not in st.session_state:
        st.session_state.turn_index = 0
    if "transcript" not in st.session_state:
        st.session_state.transcript = None
    if "transcript_path" not in st.session_state:
        st.session_state.transcript_path = None
    if "quick_prompt" not in st.session_state:
        st.session_state.quick_prompt = None
    if "waiting_for_user" not in st.session_state:
        st.session_state.waiting_for_user = None
    if "is_running" not in st.session_state:
        st.session_state.is_running = False

init_session_state()


# ----------------- Sidebar Configuration -----------------
with st.sidebar:
    st.markdown("### 🌿 Cấu hình Research Agent")

    default_provider_idx = 0 if os.getenv("OPENAI_API_KEY") else 1
    provider_name = st.selectbox(
        "Model Provider",
        options=["openai", "openrouter", "gemini", "anthropic", "ollama"],
        index=default_provider_idx,
        disabled=st.session_state.is_running,
        help="Chọn LLM provider được hỗ trợ trong thư mục providers/",
    )

    version_label = st.selectbox(
        "Artifact Version",
        options=["v3", "v2", "v1", "v0"],
        index=0,
        disabled=st.session_state.is_running,
        help="Nhãn cho file prompt/tools hiện tại; chọn nhãn cũ không khôi phục nội dung phiên bản cũ.",
    )

    model_override = st.text_input(
        "Model (để trống dùng mặc định provider)",
        value="",
        disabled=st.session_state.is_running,
    ).strip() or None

    col1, col2 = st.columns(2)
    with col1:
        max_tool_rounds = st.number_input("Max Tool Rounds", min_value=1, max_value=8, value=4, disabled=st.session_state.is_running)
    with col2:
        history_window = st.number_input("History Window", min_value=1, max_value=10, value=5, disabled=st.session_state.is_running)

    system_prompt_file = ARTIFACTS_DIR / "system_prompt.md"
    tools_file = ARTIFACTS_DIR / "tools.yaml"

    # Load artifacts and build version hash
    system_prompt_text = system_prompt_file.read_text(encoding="utf-8") if system_prompt_file.exists() else ""
    tool_decls = load_tool_declarations(tools_file) if tools_file.exists() else []
    openai_tools = to_openai_tools(tool_decls)

    try:
        art_ver = build_artifact_version(version_label, system_prompt_file, tools_file)
        ver_info = artifact_version_dict(art_ver)
    except Exception:
        ver_info = {
            "artifact_version": version_label,
            "prompt_hash": "unknown",
            "tools_hash": "unknown",
        }

    st.markdown("---")
    st.markdown("#### 🏷️ Metadata & Hashes")
    st.caption(f"**Artifact Version:** `{ver_info.get('artifact_version')}`")
    st.caption(f"**Prompt Hash:** `{ver_info.get('prompt_hash', '')[:10]}...`")
    st.caption(f"**Tools Hash:** `{ver_info.get('tools_hash', '')[:10]}...`")

    with st.expander(f"🛠️ Danh sách Tool ({len(tool_decls)})", expanded=False):
        for tool in tool_decls:
            t_name = tool.get("name", "unknown")
            t_desc = tool.get("description", "")
            st.markdown(f"**`{t_name}`**")
            st.caption(t_desc)

    with st.expander("📝 Xem System Prompt", expanded=False):
        st.text_area("System Prompt", value=system_prompt_text, height=200, disabled=True)

    st.markdown("---")
    if st.button("🧹 Làm mới phiên trò chuyện (Reset)", use_container_width=True, disabled=st.session_state.is_running):
        st.session_state.messages = []
        st.session_state.raw_history = []
        st.session_state.turn_index = 0
        st.session_state.transcript = None
        st.session_state.transcript_path = None
        st.session_state.waiting_for_user = None
        st.session_state.is_running = False
        st.rerun()

    if st.session_state.transcript_path and Path(st.session_state.transcript_path).exists():
        with open(st.session_state.transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()
        st.download_button(
            label="📥 Tải Transcript JSON",
            data=transcript_content,
            file_name=Path(st.session_state.transcript_path).name,
            mime="application/json",
            use_container_width=True,
            disabled=st.session_state.is_running,
        )


# Start a fresh conversation when its provider/model/artifacts change so the
# transcript metadata always describes the calls recorded in that file.
conversation_config = (provider_name, model_override, ver_info.get("artifact_version"), int(history_window), int(max_tool_rounds))
if st.session_state.get("conversation_config") != conversation_config:
    for state_key in ("messages", "raw_history"):
        st.session_state[state_key] = []
    for state_key in ("transcript", "transcript_path", "waiting_for_user", "quick_prompt"):
        st.session_state[state_key] = None
    st.session_state.turn_index = 0
    st.session_state.conversation_config = conversation_config

# ----------------- Transcript Initialization -----------------
def get_or_create_transcript() -> tuple[dict[str, Any], Path]:
    if st.session_state.transcript is not None and st.session_state.transcript_path is not None:
        return st.session_state.transcript, Path(st.session_state.transcript_path)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{timestamp}"
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **ver_info,
        "provider": provider_name,
        "model": model_override,
        "system_prompt": str(system_prompt_file),
        "tools": str(tools_file),
        "history_window": int(history_window),
        "max_tool_rounds": int(max_tool_rounds),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.transcript = transcript
    st.session_state.transcript_path = str(transcript_path)
    return transcript, transcript_path


# ----------------- Top Hero Header Card -----------------
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🌿 Research Agent Workspace</div>
    <div class="hero-subtitle">
        Trợ lý Nghiên cứu Thông tin Đa Nguồn Thông minh · Function Calling (MCP) · VinAI Day 03 Lab v2
    </div>
    <div>
        <span class="badge-chip">🚀 Phiên bản: <b>""" + str(ver_info.get("artifact_version")) + """</b></span>
        <span class="badge-chip">⚡ Provider: <b>""" + str(provider_name) + """</b></span>
        <span class="badge-chip">🛠️ Công cụ: <b>""" + str(len(tool_decls)) + """ tools</b></span>
        <span class="badge-chip">🔒 Guardrail: <b>Active</b></span>
    </div>
</div>
""", unsafe_allow_html=True)


# ----------------- Quick Prompts for Showdown Demo -----------------
st.markdown("##### ⚡ Câu hỏi mẫu thử nhanh (1-Click Showdown Demo):")
q_col1, q_col2, q_col3, q_col4 = st.columns(4)

with q_col1:
    if st.button("📰 Tin tức AI hôm nay", use_container_width=True, disabled=st.session_state.is_running):
        st.session_state.quick_prompt = "Tin tức AI hôm nay có gì nổi bật?"
        st.rerun()

with q_col2:
    if st.button("🐦 Tweet của Sam Altman", use_container_width=True, disabled=st.session_state.is_running):
        st.session_state.quick_prompt = "Tweet mới nhất của Sam Altman là gì?"
        st.rerun()

with q_col3:
    if st.button("🔍 Bàn luận GPT-5 trên X", use_container_width=True, disabled=st.session_state.is_running):
        st.session_state.quick_prompt = "Mọi người đang bàn gì về GPT-5 trên Twitter?"
        st.rerun()

with q_col4:
    if st.button("📢 Gửi Telegram (Cần xác nhận)", use_container_width=True, disabled=st.session_state.is_running):
        st.session_state.quick_prompt = "Gửi bản tin tổng hợp AI hôm nay lên kênh Telegram"
        st.rerun()

st.divider()


# ----------------- Render Chat History (Distinct Left/Right Layout) -----------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        # User message: Pushed to the right (1 part empty space, 4 parts user)
        col_empty, col_user = st.columns([1, 4])
        with col_user:
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(f"**Bạn**\n\n{msg['content']}")
    else:
        # Agent message: Kept on the left (4 parts agent, 1 part empty space)
        col_agent, col_empty = st.columns([4, 1])
        with col_agent:
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(msg["content"])
                tool_rounds = [r for r in msg.get("rounds", []) if r.get("tool_calls")]
                if tool_rounds:
                    with st.expander("Chi tiết công cụ: tham số và kết quả", expanded=False):
                        for round_record in tool_rounds:
                            st.markdown(f"**Vòng {round_record.get('round', 1)}**")
                            for call in round_record.get("tool_calls", []):
                                st.code(call.get("name", ""), language=None)
                                st.json(call.get("args", {}))
                            for event in round_record.get("tool_results", []):
                                st.caption(f"Kết quả: {event.get('tool', '')}")
                                st.json(event.get("result", {}))


# ----------------- Interactive Clarification / Confirmation Buttons -----------------
if st.session_state.waiting_for_user and not st.session_state.is_running:
    wait_info = st.session_state.waiting_for_user
    st.info(f"❓ **Agent cần bạn xác nhận / làm rõ:** {wait_info.get('question', '')}")

    resp_type = wait_info.get("response_type", "text")
    options = wait_info.get("options", [])

    if resp_type == "yes_no":
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("✅ Đồng ý / Xác nhận", key="btn_confirm_yes", type="primary", use_container_width=True):
                st.session_state.quick_prompt = "Tôi xác nhận đồng ý."
                st.session_state.waiting_for_user = None
                st.rerun()
        with c2:
            if st.button("❌ Không đồng ý / Hủy bỏ", key="btn_confirm_no", use_container_width=True):
                st.session_state.quick_prompt = "Không, tôi không đồng ý."
                st.session_state.waiting_for_user = None
                st.rerun()
    elif resp_type == "choice" and options:
        opt_cols = st.columns(len(options))
        for idx, opt in enumerate(options):
            with opt_cols[idx]:
                if st.button(opt, key=f"btn_opt_{idx}", use_container_width=True):
                    st.session_state.quick_prompt = opt
                    st.session_state.waiting_for_user = None
                    st.rerun()
    else:
        st.caption("💬 *Vui lòng nhập câu trả lời hoặc thông tin bổ sung vào ô chat bên dưới và nhấn Enter.*")


# ----------------- Handle User Input with Lock & Loading Effect -----------------
chat_placeholder = "Nhập yêu cầu nghiên cứu hoặc câu hỏi..."
if st.session_state.is_running:
    chat_placeholder = "⏳ Agent đang xử lý yêu cầu, vui lòng chờ..."
elif st.session_state.waiting_for_user:
    chat_placeholder = "✍️ Nhập thông tin bổ sung cho Agent..."

user_input = st.chat_input(
    chat_placeholder,
    disabled=st.session_state.is_running,
)

prompt_to_process = None
if st.session_state.quick_prompt and not st.session_state.is_running:
    prompt_to_process = st.session_state.quick_prompt
    st.session_state.quick_prompt = None
elif user_input and not st.session_state.is_running:
    prompt_to_process = user_input.strip()

if prompt_to_process:
    # 1. Lock state immediately to prevent spamming & clear waiting state
    st.session_state.is_running = True
    st.session_state.waiting_for_user = None

    # 2. Render User Message IMMEDIATELY on the right before agent starts
    col_empty, col_user = st.columns([1, 4])
    with col_user:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(f"**Bạn**\n\n{prompt_to_process}")

    # 3. Append to history state
    st.session_state.messages.append({"role": "user", "content": prompt_to_process})
    st.session_state.turn_index += 1
    transcript, transcript_path = get_or_create_transcript()

    messages = [
        {"role": "system", "content": system_prompt_text},
        *trim_history(st.session_state.raw_history, int(history_window)),
        {"role": "user", "content": prompt_to_process},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": prompt_to_process,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    # 4. Render Agent response on the left with clean disappearing spinner
    col_agent, col_empty = st.columns([4, 1])
    with col_agent:
        with st.chat_message("assistant", avatar="🌿"):
            loading_placeholder = st.empty()
            with loading_placeholder:
                with st.spinner("🌿 Đang suy luận và thực thi công cụ..."):
                    try:
                        provider = make_provider(provider_name)
                        selected_model = model_override or getattr(provider, "default_model", None)
                        if transcript.get("model") is None:
                            transcript["model"] = selected_model

                        result = run_model_tool_loop(
                            provider=provider,
                            messages=messages,
                            tools=openai_tools,
                            model=model_override,
                            max_tool_rounds=int(max_tool_rounds),
                        )
                        turn_record.update(result)
                        assistant_text = result.get("assistant_text") or "Không có phản hồi từ Agent."
                        tool_rounds = result.get("rounds", [])

                        # Update history
                        st.session_state.raw_history.append({"role": "user", "content": prompt_to_process})
                        st.session_state.raw_history.append({"role": "assistant", "content": assistant_text})

                        # Check if waiting for user (clarify tool triggered)
                        if result.get("status") == "waiting_for_user":
                            clarify_event = next(
                                (e for e in result.get("tool_events", []) if e.get("result", {}).get("awaiting_user")),
                                None,
                            )
                            st.session_state.waiting_for_user = {
                                "question": assistant_text,
                                "response_type": ((clarify_event.get("result", {}).get("response_type") or clarify_event.get("args", {}).get("response_type") or "text") if clarify_event else "text"),
                                "options": (clarify_event.get("args", {}).get("options") if clarify_event else []),
                            }
                        else:
                            st.session_state.waiting_for_user = None

                        # Store in session messages
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_text,
                            "rounds": tool_rounds,
                        })

                    except Exception as exc:
                        err_msg = f"{type(exc).__name__}: {str(exc)}"
                        turn_record.update({
                            "status": "provider_error",
                            "error": err_msg,
                        })
                        assistant_text = f"❌ Lỗi Provider: {err_msg}"
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_text,
                            "rounds": [],
                        })

                    # Save transcript
                    turn_record["ended_at"] = now_iso()
                    transcript["turns"].append(turn_record)
                    write_transcript(transcript_path, transcript)

            # 5. Clean up: Disappear the running indicator and show ONLY the clean final answer
            loading_placeholder.empty()
            st.markdown(assistant_text)

    # 6. Unlock state and refresh smoothly
    st.session_state.is_running = False
    st.rerun()
