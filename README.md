# Radar Offline Intel-Query Assistant 📄

**Summer Internship 2026 — Radar Department | Bharat Electronics Limited (BEL)**

An intelligent, **fully offline** PDF Search and Question-Answering System built for deployment on air-gapped Linux (RHEL) systems at Bharat Electronics Limited. The system searches through large collections of PDFs stored across nested folder structures, understands natural language questions submitted by text or voice, and returns accurate, source-attributed answers — with **zero dependency on internet connectivity** during operation, in line with the security requirements of a defense manufacturing environment.

---

## Why Offline Matters

This isn't a system that merely *can* run offline — it was engineered from the ground up for a target machine with **no internet access whatsoever**. Every model, every Python dependency, and every binary the application needs was pre-downloaded, packaged, and transferred via removable media, then installed using `pip install --no-index`, which refuses to contact any package index. Explicit offline environment flags are also set at application startup, *before* any model-loading library is imported, to guarantee no network call is ever attempted:

```python
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
```

The result is a system that, once installed, requires no internet connection ever again — not for search, not for answering questions, not for voice transcription, and not for restarting the application.

---

## Architecture

```
User Input (Text / Voice)
        ↓
File Indexer → Scans all folders & subfolders
        ↓
Auto-Sync → Detects new/removed PDFs automatically (background watcher)
        ↓
RAG Pipeline
├── PDF Parser (PyMuPDF / Tesseract OCR / ColPali)
├── Chunker (500 word chunks, 50 word overlap)
├── Embedder (sentence-transformers, offline cached)
├── FAISS Vector Store
└── Ollama LLM (Llama 3.2) → Answer
        ↓
Conversation-aware follow-up handling
        ↓
Smart Folder Suggestion (if answer not found)
```

---

## Features

- 🔍 Multi-PDF search across nested folders and subfolders
- 🎙️ Voice-based query input — record via microphone, review the transcription, then send
- 💬 Persistent chat history — organized by date, fully browsable across sessions
- 🧠 Context-aware follow-ups — understands references like "explain more about them"
- 📄 Scanned PDF support — Tesseract OCR (CPU) or ColPali (GPU), selected automatically at runtime
- 📁 Smart folder suggestions when an answer isn't found in the currently indexed documents
- 📂 Full source attribution — every answer shows the exact PDF, folder path, and page number it was drawn from
- ♻️ Automatic incremental re-indexing — new PDFs are detected and embedded in the background every 15 seconds, with no manual rebuild required; deleted PDFs are automatically pruned from the index
- ✏️ Edit, retry, and remove controls on any question — refine or resend a query without retyping it, synced with the underlying chat database
- 🔌 **100% offline operation** — no internet required after the one-time setup bundle is installed
- 🖥️ Streamlit-based interactive web interface
- 🌐 Cross-platform — developed on Windows, deployed on Linux (RHEL 9.2)

---

## Tech Stack

| Component | Technology |
|---|---|
| Language Model | Ollama — Llama 3.2 (fully local inference) |
| Vector Search | FAISS |
| PDF Parsing | PyMuPDF |
| Scanned PDFs | Tesseract OCR (CPU) / ColPali (GPU) |
| Voice Input | OpenAI Whisper + sounddevice/PortAudio |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Frontend | Streamlit |
| Chat Storage | SQLite |
| Hardware Adaptation | Auto-detects GPU → ColPali; falls back to CPU → Tesseract |

---

## Project Structure

```
PDF_QA_System/
├── streamlit_app.py        # Main Streamlit web application
├── file_indexer.py          # Folder scanning and PDF indexing
├── pdf_processor.py         # Text-based PDF extraction
├── vector_db_manager.py     # FAISS vector store + embeddings
├── index_manager.py         # Incremental index build/sync/save/load
├── ollama_connector.py       # LLM answer generation
├── ocr_processor.py          # Tesseract OCR (CPU), OS-aware
├── colpali_processor.py      # ColPali visual model (GPU)
├── scanned_handler.py        # Automatic GPU/CPU hardware detection
├── folder_suggester.py       # Semantic folder suggestions
├── voice_input.py             # Voice query recording + Whisper transcription
├── chat_history.py            # SQLite-based persistent chat history
├── install.sh                 # Linux offline installer
├── Start_PDF_App.vbs          # Windows silent background launcher
├── requirements.txt
└── sample_pdfs/                # Local test document set (not tracked in repo)
```

---

## Offline Deployment Overview

Deployment to the target RHEL 9.2 machine — which has no internet access — was carried out in two phases:

**Phase A (preparation, on a machine with internet access):**
- All Python dependencies downloaded as **Linux-compatible (`manylinux`) wheel files**, including a CPU-only build of PyTorch
- The embedding model and Llama 3.2 weights cached locally via one-time downloads
- The Ollama Linux runtime binary obtained directly (`.tar.zst` archive)
- All of the above bundled together on removable media, alongside the full application source code

**Phase B (installation, on the offline target machine):**
- Python 3.11, Tesseract, and ffmpeg installed via the system package manager (`dnf`)
- All Python dependencies installed with `pip install --no-index --find-links=<bundle>`, which never contacts PyPI
- Cached model directories restored to their expected locations (`~/.cache/huggingface`, `~/.ollama`)
- The Ollama and Streamlit processes configured as **systemd services**, so the application starts automatically on every boot and restarts automatically if it ever stops — with no terminal or manual command required

This two-phase approach means the offline bundle is fully portable: it can be copied to any number of target machines and installed identically on each, without repeating the preparation phase.

---

## Installation

### Windows (Development)
```bash
conda create -n pdf_qa python=3.11
conda activate pdf_qa
pip install -r requirements.txt
ollama pull llama3.2

# Download embedding model once (requires internet)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Linux (BEL, fully offline)
```bash
chmod +x install.sh
./install.sh
```
See the accompanying offline deployment guide for the complete, verified step-by-step procedure, including offline package bundling, Ollama binary installation, and systemd auto-start configuration.

---

## Running the Project

```bash
# Windows
conda activate pdf_qa
python -m streamlit run streamlit_app.py --server.fileWatcherType none

# Linux
source pdf_qa/bin/activate
python3.11 -m streamlit run streamlit_app.py --server.fileWatcherType none --server.address=0.0.0.0
```

Open browser: `http://localhost:8501`

> **Note:** `--server.fileWatcherType none` is required — without it, Streamlit's automatic file watcher can interrupt an in-progress answer whenever the chat history database is written to mid-response.

### Windows — Silent Background Launch
Double-click `Start_PDF_App.vbs` (or its desktop shortcut) to start the app in the background with no visible terminal window, and automatically open it in the browser after a short delay.

### Linux — Persistent Auto-Start
Once configured as systemd services (`ollama.service` and `radarpdf.service`), the application survives reboots automatically. After any restart, simply open a browser to `http://localhost:8501` — no manual commands needed.

---

## Adding New Documents

Drop new PDFs into the configured document root folder (or any subfolder) at any time while the app is running. A background process — implemented as an isolated Streamlit fragment so it can never interrupt an answer in progress — checks for changes every 15 seconds and indexes new documents automatically. Deleted PDFs are detected the same way and pruned from the search index.

> **Note:** Large PDFs (100+ pages) can take several minutes to index on CPU-only systems, since every page must be chunked and embedded. Keep the app open and avoid asking questions until indexing completes — a toast notification confirms when it's done.

---

## Developer

**Ishita Thakur**
B.Tech CSE (2024–2028) | Maharaja Surajmal Institute of Technology
Summer Intern — Radar Department | Bharat Electronics Limited | 2026

[![GitHub](https://img.shields.io/badge/GitHub-ishitathakur22-black)](https://github.com/ishitathakur22)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ishita_Thakur-blue)](https://www.linkedin.com/in/ishita-thakur-857743322/)
