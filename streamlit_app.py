import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

import streamlit as st
import numpy as np
from sentence_transformers import SentenceTransformer
from index_manager import index_exists, load_index, build_index

from ollama_connector import get_answer
from folder_suggester import build_folder_embeddings, suggest_folders, check_answer_confidence
from voice_input import get_voice_query
from chat_history import (
    init_db, create_new_chat, save_message,
    update_chat_title, load_all_chats,
    load_chat_messages, delete_chat, group_chats_by_date
)

# Page config
st.set_page_config(
    page_title="PDF Q&A System - BEL",
    page_icon="📄",
    layout="wide"
)

# Custom CSS

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

    /* Reduce gap between chat input and mic button */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
        align-items: stretch;
    }

    /* Match mic button color and size to chat input box */
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
</style>
""", unsafe_allow_html=True)

# Root path
ROOT_PATH = "./sample_pdfs"

# Embedder
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize DB
init_db()


def search_chunks(query, index, chunks, top_k=5):
    query_emb = embedder.encode([query])
    query_emb = np.array(query_emb).astype("float32")
    distances, indices = index.search(query_emb, top_k)
    return [chunks[i] for i in indices[0] if i < len(chunks)]


# Session state
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "folder_data" not in st.session_state:
    st.session_state.folder_data = None


@st.cache_resource
def initialize_system():
    if index_exists():
        index, chunks = load_index()
    else:
        index, chunks = build_index(ROOT_PATH)
    folder_data = build_folder_embeddings(ROOT_PATH)
    return index, chunks, folder_data


# Auto initialize
if st.session_state.index is None:
    with st.spinner("Initializing system..."):
        idx, chks, fdata = initialize_system()
        st.session_state.index = idx
        st.session_state.chunks = chks
        st.session_state.folder_data = fdata


# Sidebar
with st.sidebar:

    # Header
    st.markdown("### 📄 PDF Q&A")
    st.caption("BEL — Radar Department")
    st.divider()

    # New Chat button
    if st.button("New Chat", use_container_width=True, type="primary"):
        new_id = create_new_chat("New Chat")
        st.session_state.current_chat_id = new_id
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Chat history
    all_chats = load_all_chats()
    grouped = group_chats_by_date(all_chats)

    for group_name, chats in grouped.items():
        if chats:
            st.markdown(f"<div class='sidebar-header'>{group_name}</div>",
                       unsafe_allow_html=True)
            for chat in chats:
                chat_id, title, created_at = chat
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(
                        title,
                        key=f"chat_{chat_id}",
                        use_container_width=True
                    ):
                        st.session_state.current_chat_id = chat_id
                        msgs = load_chat_messages(chat_id)
                        st.session_state.messages = [
                            {"role": m[0], "content": m[1]}
                            for m in msgs
                        ]
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{chat_id}"):
                        delete_chat(chat_id)
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                            st.session_state.messages = []
                        st.rerun()

    

    st.divider()

    # Rebuild index section
    st.markdown("<div class='sidebar-header'>DOCUMENTS</div>", unsafe_allow_html=True)
    st.caption("Added new PDFs? Rebuild the index to include them in search.")
    
    if st.button("Rebuild Index", use_container_width=True):
        with st.spinner("Rebuilding..."):
            idx, chks = build_index(ROOT_PATH)
            st.session_state.index = idx
            st.session_state.chunks = chks
        st.success("Done!")



# Main chat area
st.markdown("## PDF Q&A System")
st.caption("Bharat Electronics Limited — Radar Department | Intelligent Document Search")
st.divider()

# Create new chat if none selected
if st.session_state.current_chat_id is None:
    new_id = create_new_chat("New Chat")
    st.session_state.current_chat_id = new_id

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice query
prompt = None
if "voice_query" in st.session_state and st.session_state.voice_query:
    prompt = st.session_state.voice_query
    st.session_state.voice_query = None

# Chat input with mic button beside it
col1, col2 = st.columns([10, 1])

# Recording status placeholder
status_placeholder = st.empty()

st.markdown('<div class="mic-wrapper">', unsafe_allow_html=True)
col1, col2 = st.columns([12, 1])

with col1:
    user_input = st.chat_input("Ask a question about your documents...")

with col2:
    if st.button("🎤", key="mic_button"):
        status_placeholder.info("🔴 Recording for 20 seconds...")
        voice_text = get_voice_query(duration=20)
        status_placeholder.empty()
        if voice_text:
            st.session_state.voice_query = voice_text
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

if user_input:
    prompt = user_input

if prompt:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    save_message(
        st.session_state.current_chat_id,
        "user",
        prompt
    )

    # Update chat title from first question
    if len(st.session_state.messages) == 1:
        update_chat_title(
            st.session_state.current_chat_id,
            prompt[:50]
        )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Build a search-friendly query using recent history
            search_query = prompt
            if len(st.session_state.messages) >= 2:
                last_user_msg = st.session_state.messages[-2]["content"]if st.session_state.messages[-2]["role"] == "user" else ""
                last_assistant_msg = st.session_state.messages[-1]["content"] if len(st.session_state.messages) >= 1 else ""
                search_query = f"{last_assistant_msg} {prompt}"
            relevant_chunks = search_chunks(
                search_query,
                st.session_state.index,
                st.session_state.chunks
            )

            answer = get_answer(prompt, relevant_chunks, st.session_state.messages[:-1])
            st.markdown(answer)

            # Sources
            sources = list(set([
                f"{c['pdf_name']} (Page {c['page_number']})"
                for c in relevant_chunks
            ]))
            if sources:
                st.caption("Sources: " + " | ".join(sources[:3]))

            # Folder suggestions
            if check_answer_confidence(answer):
                current_folders = list(set([
                    c.get("folder", "")
                    for c in st.session_state.chunks
                ]))
                suggestions = suggest_folders(
                    prompt,
                    st.session_state.folder_data,
                    current_folders
                )
                if suggestions:
                    st.warning("Try these folders:")
                    for s in suggestions:
                        st.write(f"📁 {s['folder']} ({s['similarity']:.0%})")

            # Save assistant message
            sources_str = " | ".join(sources[:3])
            save_message(
                st.session_state.current_chat_id,
                "assistant",
                answer,
                sources_str
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })