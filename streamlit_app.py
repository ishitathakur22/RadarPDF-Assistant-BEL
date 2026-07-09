import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from file_indexer import get_folder_signature

import streamlit as st
from index_manager import index_exists, load_index, build_index, sync_index
from vector_db_manager import search_similar_chunks as search_chunks
from ollama_connector import get_answer
from folder_suggester import build_folder_embeddings, suggest_folders, check_answer_confidence
from voice_input import get_voice_query
from chat_history import (
    init_db, create_new_chat, save_message,
    update_chat_title, load_all_chats,
    load_chat_messages, delete_chat, group_chats_by_date
)

# ============================================================
# Page config
# ============================================================
st.set_page_config(
    page_title="PDF Q&A System - BEL",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
    .chat-title {
        font-size: 13px;
        padding: 6px 10px;
        border-radius: 6px;
        cursor: pointer;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sidebar-header {
        font-size: 11px;
        color: gray;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 10px 0 4px 0;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
        align-items: stretch;
    }
    div[data-testid="column"]:nth-of-type(2) button {
        background-color: rgb(38, 39, 48) !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
        border-radius: 8px !important;
        height: 100% !important;
        min-height: 52px !important;
        font-size: 18px !important;
        color: rgb(250, 250, 250) !important;
    }
    div[data-testid="column"]:nth-of-type(2) button:hover {
        border-color: rgba(250, 250, 250, 0.5) !important;
        background-color: rgb(48, 49, 58) !important;
    }

    /* --- Question input row: mic button (left) + chat_input (right) --- */
    .st-key-qa_input_row {
        max-width: 1020px;
        margin: 0 auto;
    }
    .st-key-qa_input_row div[data-testid="stChatInput"] {
        border-radius: 14px !important;
    }
    .st-key-qa_input_row div[data-testid="column"]:last-of-type button {
        width: 100% !important;
        height: 100% !important;
        min-height: 52px !important;
        border-radius: 14px !important;
        font-size: 26px !important;
        background-color: rgb(38, 39, 48) !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
        color: rgb(250, 250, 250) !important;
    }
    .st-key-qa_input_row div[data-testid="column"]:last-of-type button:hover {
        border-color: rgba(250, 250, 250, 0.5) !important;
        background-color: rgb(48, 49, 58) !important;
    }
    /* Compact 3-dot menu trigger button */
    div[data-testid="stPopover"] > div > button {
        padding: 2px 10px !important;
        min-height: 26px !important;
        font-size: 14px !important;
        border-radius: 6px !important;
        line-height: 1 !important;
    }

    /* Compact popover panel */
    div[data-testid="stPopoverBody"] {
        padding: 8px !important;
        min-width: 120px !important;
        width: auto !important;
    }

    /* Compact buttons inside the popover */
    div[data-testid="stPopoverBody"] button {
        padding: 4px 10px !important;
        min-height: 30px !important;
        font-size: 13px !important;
        margin-bottom: 4px !important;
    }
</style>
""", unsafe_allow_html=True)

ROOT_PATH = "./sample_pdfs"

init_db()

# ============================================================
# Session state defaults
# ============================================================
defaults = {
    "current_chat_id": None,
    "messages": [],
    "index": None,
    "chunks": None,
    "folder_data": None,
    "processing": False,
    "folder_signature": None,
    "voice_query": None,
    "retry_prompt": None,
    "editing_index": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# Core: initialize + sync (used both at startup and as a safety net)
# ============================================================
def _first_time_index():
    """No caching here — always reads fresh from disk (fast anyway)."""
    if index_exists():
        index, chunks = load_index()
    else:
        index, chunks = build_index(ROOT_PATH)
    folder_data = build_folder_embeddings(ROOT_PATH)
    return index, chunks, folder_data


def ensure_system_ready():
    """
    Guarantees index/chunks/folder_data are loaded AND up to date with
    any new PDFs on disk. Safe to call multiple times — cheap if nothing changed.
    """
    if st.session_state.index is None:
        idx, chks, fdata = _first_time_index()
        st.session_state.index = idx
        st.session_state.chunks = chks
        st.session_state.folder_data = fdata
        st.session_state.folder_signature = get_folder_signature(ROOT_PATH)
        return

    if st.session_state.folder_signature is None:
        st.session_state.folder_signature = get_folder_signature(ROOT_PATH)

    current_signature = get_folder_signature(ROOT_PATH)
    if current_signature != st.session_state.folder_signature:
        idx, chks, new_count = sync_index(ROOT_PATH)
        st.session_state.index = idx
        st.session_state.chunks = chks
        st.session_state.folder_data = build_folder_embeddings(ROOT_PATH)
        st.session_state.folder_signature = current_signature
        if new_count > 0:
            st.toast(f"✅ {new_count} new PDF(s) indexed automatically!", icon="📄")


@st.cache_resource
def warm_up_ollama():
    """Loads the Ollama model into memory once, so the first real question is fast."""
    try:
        from ollama_connector import get_answer
        get_answer("hello", [], [])
        print("Ollama warmed up successfully.")
    except Exception as e:
        print(f"Ollama warm-up failed: {e}")
    return True


# ============================================================
# Startup: initialize once (cheap/idempotent on every run because of
# st.cache_resource on the heavy parts, so it's safe to call unconditionally)
# ============================================================
with st.spinner("Initializing system..."):
    ensure_system_ready()
    warm_up_ollama()


# ============================================================
# Background PDF watcher — runs as an ISOLATED fragment.
# This is the key fix: a fragment only reruns itself, never the whole
# page, so it can NEVER interrupt or race with chat_input / get_answer()
# processing in the main body below. This is what was previously causing
# the same question to be captured and appended twice.
# ============================================================
@st.fragment(run_every="15s")
def watch_for_new_pdfs():
    if st.session_state.processing:
        return  # a question is currently being answered, don't touch anything

    current_signature = get_folder_signature(ROOT_PATH)
    if current_signature != st.session_state.folder_signature:
        with st.spinner("📄 New PDF detected. Updating index..."):
            ensure_system_ready()
        st.toast("✅ New PDF(s) indexed automatically!", icon="📄")


watch_for_new_pdfs()


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("### 📄 PDF Q&A")
    st.caption("BEL — Radar Department")
    st.divider()

    if st.button("New Chat", use_container_width=True, type="primary"):
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()

    all_chats = load_all_chats()
    grouped = group_chats_by_date(all_chats)

    for group_name, chats in grouped.items():
        if chats:
            st.markdown(f"<div class='sidebar-header'>{group_name}</div>", unsafe_allow_html=True)
            for chat in chats:
                chat_id, title, created_at = chat
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(title, key=f"chat_{chat_id}", use_container_width=True):
                        st.session_state.current_chat_id = chat_id
                        msgs = load_chat_messages(chat_id)
                        st.session_state.messages = [{"role": m[0], "content": m[1]} for m in msgs]
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{chat_id}"):
                        delete_chat(chat_id)
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                            st.session_state.messages = []
                        st.rerun()

    st.divider()
    st.markdown("<div class='sidebar-header'>DOCUMENTS</div>", unsafe_allow_html=True)
    st.caption("New PDFs are detected automatically. Rebuild only if needed.")

    if st.button("Rebuild Index", use_container_width=True):
        with st.spinner("Rebuilding..."):
            idx, chks = build_index(ROOT_PATH)
            st.session_state.index = idx
            st.session_state.chunks = chks
            st.session_state.folder_data = build_folder_embeddings(ROOT_PATH)
            st.session_state.folder_signature = get_folder_signature(ROOT_PATH)
        st.success("Done!")


# ============================================================
# Main chat area
# ============================================================
st.markdown("## PDF Q&A System")
st.caption("Bharat Electronics Limited — Radar Department | Intelligent Document Search")
st.divider()

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):

        if message["role"] == "user" and st.session_state.editing_index == i:
            edited_text = st.text_input("Edit your question:", value=message["content"], key=f"edit_input_{i}")
            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button("✅ Save & Resend", key=f"save_edit_{i}"):
                    st.session_state.messages = st.session_state.messages[:i]
                    st.session_state.retry_prompt = edited_text
                    st.session_state.editing_index = None
                    st.rerun()
            with col_cancel:
                if st.button("Cancel", key=f"cancel_edit_{i}"):
                    st.session_state.editing_index = None
                    st.rerun()

        else:
            is_user = message["role"] == "user"
            is_failed = message["role"] == "assistant" and "Answer not found" in message["content"]

            msg_col, menu_col = st.columns([20, 1],)

            with msg_col:
                st.markdown(message["content"])

            with menu_col:
                if is_user or is_failed:
                    with st.popover("⋮"):
                        if is_user:
                            if st.button("Edit", key=f"edit_{i}", use_container_width=True):
                                st.session_state.editing_index = i
                                st.rerun()
                        if is_failed:
                            if st.button("Retry", key=f"retry_{i}", use_container_width=True):
                                if i > 0 and st.session_state.messages[i - 1]["role"] == "user":
                                    st.session_state.retry_prompt = st.session_state.messages[i - 1]["content"]
                                    st.session_state.messages = st.session_state.messages[:i - 1]
                                    st.rerun()
                            if st.button("Remove", key=f"remove_{i}", use_container_width=True):
                                if i > 0 and st.session_state.messages[i - 1]["role"] == "user":
                                    st.session_state.messages = st.session_state.messages[:i - 1] + st.session_state.messages[i + 1:]
                                else:
                                    st.session_state.messages = st.session_state.messages[:i] + st.session_state.messages[i + 1:]
                                st.rerun()

prompt = None

if st.session_state.voice_query:
    prompt = st.session_state.voice_query
    st.session_state.voice_query = None

if st.session_state.retry_prompt:
    prompt = st.session_state.retry_prompt
    st.session_state.retry_prompt = None

status_placeholder = st.empty()

VOICE_RECORD_SECONDS = 6  # how long the mic listens per click

with st.bottom:
    with st.container(key="qa_input_row"):
        input_col, mic_col = st.columns([11, 1])

        with input_col:
            user_input = st.chat_input(
                "Ask a question about your documents...",
                disabled=st.session_state.processing,
            )

        with mic_col:
            mic_clicked = st.button(
                "🎙️",
                key="mic_button",
                disabled=st.session_state.processing,
                help="Click and speak your question",
            )

if user_input:
    prompt = user_input

# ============================================================
# Mic button handling — records + transcribes right here (blocking),
# then stores the result in voice_query and reruns. The next run picks
# it up via the "if st.session_state.voice_query" check above, so it
# goes through the exact same path as a typed question.
# ============================================================
if mic_clicked:
    with status_placeholder.container():
        with st.spinner(f"🎙️ Listening... speak now ({VOICE_RECORD_SECONDS}s)"):
            try:
                transcribed_text = get_voice_query(duration=VOICE_RECORD_SECONDS)
            except Exception as e:
                transcribed_text = ""
                st.error(f"Voice input failed: {e}")

    if transcribed_text and transcribed_text.strip():
        st.session_state.voice_query = transcribed_text.strip()
        st.rerun()
    else:
        st.warning("Couldn't hear anything clearly — please try again.")

# ============================================================
# Duplicate-submission guard.
# If processing is already True, a run is already handling a prompt
# (or a previous run was interrupted mid-way). Treat any prompt that
# arrives in that state as a stray duplicate and ignore it, instead
# of appending/processing the same question a second time.
# ============================================================
if prompt and st.session_state.processing:
    prompt = None

# ============================================================
# Handle the question — this whole block is self-contained and runs
# synchronously in a single script execution, with no intermediate
# st.rerun() between capturing the prompt and generating the answer.
# ============================================================
if prompt:
    st.session_state.processing = True

    with st.spinner("Getting everything ready..."):
        ensure_system_ready()

    if st.session_state.current_chat_id is None:
        new_id = create_new_chat("New Chat")
        st.session_state.current_chat_id = new_id

    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.current_chat_id, "user", prompt)

    if len(st.session_state.messages) == 1:
        update_chat_title(st.session_state.current_chat_id, prompt[:50])

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking... (answer may take a minute while the model loads)"):

            # Only enrich the search query with prior context for genuine
            # short follow-ups (e.g. "explain more", "what about them") —
            # never for normal standalone questions.
            search_query = prompt
            pronoun_indicators = ["them", "it", "this", "that", "these", "those", "more", "further", "continue"]
            words = prompt.lower().split()
            is_followup = len(words) <= 3 and any(w in pronoun_indicators for w in words)

            if is_followup and len(st.session_state.messages) >= 2:
                last_assistant_msg = st.session_state.messages[-2]["content"] \
                    if st.session_state.messages[-2]["role"] == "assistant" else ""
                search_query = f"{last_assistant_msg} {prompt}"

            relevant_chunks = search_chunks(
                search_query,
                st.session_state.index,
                st.session_state.chunks
            )

            answer = get_answer(prompt, relevant_chunks, st.session_state.messages[:-1])
            st.markdown(answer)

            sources = list(set([
                f"{c['pdf_name']} — {c.get('folder', 'Unknown folder')} (Page {c['page_number']})"
                for c in relevant_chunks
            ]))
            if sources:
                st.caption("Sources: " + " | ".join(sources[:3]))

            if check_answer_confidence(answer):
                current_folders = list(set([c.get("folder", "") for c in st.session_state.chunks]))
                suggestions = suggest_folders(prompt, st.session_state.folder_data, current_folders)
                if suggestions:
                    st.warning("Try these folders:")
                    for s in suggestions:
                        st.write(f"📁 {s['folder']} ({s['similarity']:.0%})")

            sources_str = " | ".join(sources[:3])
            save_message(st.session_state.current_chat_id, "assistant", answer, sources_str)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    st.session_state.processing = False
    st.rerun()
