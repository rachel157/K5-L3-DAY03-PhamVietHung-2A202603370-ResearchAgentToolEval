from __future__ import annotations

import json
import os
import sys
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
    page_title="Research Agent - Day 03 Lab v2",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- Custom Light Green (Xanh Lá Nhạt) CSS Styling -----------------
st.markdown("""
<style>
    /* Global background & fonts */
    .stApp {
        background-color: #F8FAF8;
    }
    
    /* Header styling with fresh light green */
    .main-header {
        font-size: 2.3rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
        color: #065F46;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #047857;
        margin-bottom: 1.2rem;
        background: #ECFDF5;
        padding: 0.5rem 0.9rem;
        border-radius: 8px;
        border-left: 4px solid #10B981;
    }
    
    /* Badges & Chips */
    .badge-chip {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.82rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 0.5rem;
        background-color: #D1FAE5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .badge-tool {
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #6EE7B7;
    }
    .badge-provider {
        background-color: #E6F4EA;
        color: #137333;
        border: 1px solid #CEEAD6;
    }

    /* Tool Call Card / Expander Highlight */
    .tool-box {
        border-left: 4px solid #10B981;
        padding: 0.6rem 0.9rem;
        margin: 0.5rem 0;
        background: #F0FDF4;
        border-radius: 0 8px 8px 0;
        border: 1px solid #D1FAE5;
        border-left-width: 4px;
    }
    
    /* Quick Prompt Buttons customization */
    div.stButton > button {
        border-radius: 8px;
        border: 1px solid #A7F3D0;
        background-color: #F0FDF4;
        color: #065F46;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #D1FAE5;
        border-color: #34D399;
        color: #064E3B;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.15);
    }
    
    /* Primary buttons (Confirm) */
    div.stButton > button[kind="primary"] {
        background-color: #10B981;
        color: #FFFFFF;
        border: 1px solid #059669;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #059669;
        color: #FFFFFF;
    }

    /* Sidebar background tint */
    [data-testid="stSidebar"] {
        background-color: #F0FDF4;
        border-right: 1px solid #E5E7EB;
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

init_session_state()


# ----------------- Sidebar Configuration -----------------
with st.sidebar:
    st.markdown("### 🌿 Cấu hình Agent")

    default_provider_idx = 0 if os.getenv("OPENAI_API_KEY") else 1
    provider_name = st.selectbox(
        "Model Provider",
        options=["openai", "openrouter", "gemini", "anthropic", "ollama"],
        index=default_provider_idx,
        help="Chọn LLM provider được hỗ trợ trong thư mục providers/",
    )

    version_label = st.selectbox(
        "Artifact Version",
        options=["v3", "v2", "v1", "v0"],
        index=0,
        help="Phiên bản artifact prompt/tools đang thử nghiệm",
    )

    col1, col2 = st.columns(2)
    with col1:
        max_tool_rounds = st.number_input("Max Tool Rounds", min_value=1, max_value=8, value=4)
    with col2:
        history_window = st.number_input("History Window", min_value=1, max_value=10, value=5)

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
    st.markdown("#### 🏷️ Version & Hash Info")
    st.caption(f"**Artifact Version:** `{ver_info.get('artifact_version')}`")
    st.caption(f"**Prompt Hash:** `{ver_info.get('prompt_hash', '')[:10]}`")
    st.caption(f"**Tools Hash:** `{ver_info.get('tools_hash', '')[:10]}`")

    with st.expander(f"🛠️ Danh sách Tool ({len(tool_decls)})", expanded=False):
        for tool in tool_decls:
            t_name = tool.get("name", "unknown")
            t_desc = tool.get("description", "")
            st.markdown(f"**`{t_name}`**")
            st.caption(t_desc)

    with st.expander("📝 Xem System Prompt", expanded=False):
        st.text_area("System Prompt", value=system_prompt_text, height=200, disabled=True)

    st.markdown("---")
    if st.button("🧹 Làm mới phiên trò chuyện (Reset)", use_container_width=True):
        st.session_state.messages = []
        st.session_state.raw_history = []
        st.session_state.turn_index = 0
        st.session_state.transcript = None
        st.session_state.transcript_path = None
        st.session_state.waiting_for_user = None
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
        )


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
        "model": None,
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


# ----------------- Main Chat Layout -----------------
st.markdown('<div class="main-header">🌿 Research Agent Workspace</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Hệ thống Nghiên cứu Thông tin Đa Nguồn (X/Twitter, Web, Papers, Policy, Telegram) · VinAI Day 03 Lab v2</div>',
    unsafe_allow_html=True,
)

# Badges bar with light green theme
st.markdown(
    f'<span class="badge-chip">Phiên bản: {ver_info.get("artifact_version")}</span>'
    f'<span class="badge-chip badge-provider">Provider: {provider_name}</span>'
    f'<span class="badge-chip badge-tool">{len(tool_decls)} Tools sẵn sàng</span>',
    unsafe_allow_html=True,
)

st.write("")

# ----------------- Quick Prompts for Showdown Demo -----------------
st.markdown("##### ⚡ Câu hỏi mẫu thử nhanh (Showdown 1-Click Demo):")
q_col1, q_col2, q_col3, q_col4 = st.columns(4)

with q_col1:
    if st.button("📰 Tin tức AI hôm nay", use_container_width=True):
        st.session_state.quick_prompt = "Tin tức AI hôm nay có gì nổi bật?"
        st.rerun()

with q_col2:
    if st.button("🐦 Tweet của Sam Altman", use_container_width=True):
        st.session_state.quick_prompt = "Tweet mới nhất của Sam Altman là gì?"
        st.rerun()

with q_col3:
    if st.button("🔍 Bàn luận GPT-5 trên X", use_container_width=True):
        st.session_state.quick_prompt = "Mọi người đang bàn gì về GPT-5 trên Twitter?"
        st.rerun()

with q_col4:
    if st.button("📢 Gửi Telegram (Cần xác nhận)", use_container_width=True):
        st.session_state.quick_prompt = "Gửi bản tin tổng hợp AI hôm nay lên kênh Telegram"
        st.rerun()

st.divider()

# ----------------- Render Chat History -----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        tool_rounds = msg.get("rounds", [])
        if tool_rounds:
            total_calls = sum(len(r.get("tool_calls", [])) for r in tool_rounds)
            with st.expander(f"🛠️ Chi tiết thực thi công cụ ({total_calls} tool call(s))", expanded=False):
                for r in tool_rounds:
                    st.markdown(f"**Vòng {r.get('round', 1)}:**")
                    for tc in r.get("tool_calls", []):
                        st.markdown(f"- 🔧 Gọi tool: **`{tc.get('name')}`**")
                        st.json(tc.get("args", {}), expanded=False)
                    for res in r.get("tool_results", []):
                        st.markdown(f"- 📥 Kết quả từ **`{res.get('tool')}`**:")
                        st.json(res.get("result", {}), expanded=False)

        st.markdown(msg["content"])


# ----------------- Interactive Clarification / Confirmation Buttons -----------------
if st.session_state.waiting_for_user:
    wait_info = st.session_state.waiting_for_user
    st.info(f"❓ **Agent cần bạn xác nhận / làm rõ:** {wait_info.get('question', '')}")

    resp_type = wait_info.get("response_type", "text")
    options = wait_info.get("options", [])

    if resp_type == "yes_no" or not options:
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
    elif options:
        opt_cols = st.columns(len(options))
        for idx, opt in enumerate(options):
            with opt_cols[idx]:
                if st.button(opt, key=f"btn_opt_{idx}", use_container_width=True):
                    st.session_state.quick_prompt = opt
                    st.session_state.waiting_for_user = None
                    st.rerun()


# ----------------- Handle User Input -----------------
user_input = st.chat_input("Nhập yêu cầu nghiên cứu hoặc câu hỏi...")
prompt_to_process = None

if st.session_state.quick_prompt:
    prompt_to_process = st.session_state.quick_prompt
    st.session_state.quick_prompt = None
elif user_input:
    prompt_to_process = user_input.strip()

if prompt_to_process:
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt_to_process})
    with st.chat_message("user"):
        st.markdown(prompt_to_process)

    # 2. Prepare message history for Agent
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

    # 3. Call Model Tool Loop
    with st.chat_message("assistant"):
        with st.spinner("Đang suy luận và gọi tools..."):
            try:
                provider = make_provider(provider_name)
                selected_model = getattr(provider, "default_model", None)
                if transcript.get("model") is None:
                    transcript["model"] = selected_model

                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=None,
                    max_tool_rounds=int(max_tool_rounds),
                )
                turn_record.update(result)
                assistant_text = result.get("assistant_text") or "Không có phản hồi từ Agent."

                # Render tool execution details
                tool_rounds = result.get("rounds", [])
                if tool_rounds:
                    total_calls = sum(len(r.get("tool_calls", [])) for r in tool_rounds)
                    with st.expander(f"🛠️ Chi tiết thực thi công cụ ({total_calls} tool call(s))", expanded=True):
                        for r in tool_rounds:
                            st.markdown(f"**Vòng {r.get('round', 1)}:**")
                            for tc in r.get("tool_calls", []):
                                st.markdown(f"- 🔧 Gọi tool: **`{tc.get('name')}`**")
                                st.json(tc.get("args", {}), expanded=False)
                            for res in r.get("tool_results", []):
                                st.markdown(f"- 📥 Kết quả từ **`{res.get('tool')}`**:")
                                st.json(res.get("result", {}), expanded=False)

                st.markdown(assistant_text)

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
                        "response_type": (clarify_event.get("args", {}).get("response_type") if clarify_event else "text"),
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
                st.error(f"❌ Lỗi Provider: {err_msg}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Lỗi xảy ra trong quá trình xử lý: {err_msg}",
                    "rounds": [],
                })

        # Save transcript
        turn_record["ended_at"] = now_iso()
        transcript["turns"].append(turn_record)
        write_transcript(transcript_path, transcript)

    # Rerun to render options or clean layout
    st.rerun()
