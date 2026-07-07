# RadarPDF-Assistant-BEL 📄

**BEL Internship 2026 — Radar Department | Bharat Electronics Limited**

An intelligent, fully offline PDF Search and Q&A System built for Bharat Electronics Limited (BEL). The system enables users to search through large collections of PDFs stored across nested folder structures, ask natural language questions in text or voice, and receive accurate, context-aware answers — all without internet connectivity.

---

## Architecture

```
User Input (Text / Voice)
        ↓
File Indexer → Scans all folders & subfolders
        ↓
PDF Selector → Select one or more PDFs
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
- 🎙️ Voice-based query input — record directly from the chat interface
- 💬 Persistent chat history — organized by date, switch between past conversations
- 🧠 Context-aware follow-ups — understands references like "explain more about them"
- 📄 Scanned PDF support — Tesseract OCR (CPU) / ColPali (GPU)
- 📁 Smart folder suggestions when an answer isn't found in the current selection
- 🔌 Fully offline — no internet required after initial setup
- 🖥️ Streamlit-based interactive web interface
- 🌐 Cross-platform — developed on Windows, deployed on Linux (BEL)

---

## Tech Stack

| Component | Technology |
|---|---|
| Language Model | Ollama — Llama 3.2 |
| Vector Search | FAISS |
| PDF Parsing | PyMuPDF |
| Scanned PDFs | Tesseract OCR / ColPali |
| Voice Input | SpeechRecognition |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Frontend | Streamlit |
| Chat Storage | SQLite |
| Auto Processor | GPU → ColPali, CPU → Tesseract |

---

## Project Structure

```
PDF_QA_System/
├── streamlit_app.py        # Main Streamlit web application
├── main.py                 # Terminal-based pipeline
├── file_indexer.py          # Folder scanning and PDF indexing
├── pdf_processor.py         # Text-based PDF extraction
├── vector_db_manager.py     # FAISS vector store + embeddings
├── index_manager.py         # Index build/save/load logic
├── ollama_connector.py       # LLM answer generation
├── ocr_processor.py          # Tesseract OCR (CPU)
├── colpali_processor.py      # ColPali visual model (GPU)
├── scanned_handler.py        # Auto GPU/CPU detection
├── folder_suggester.py       # Smart folder suggestions
├── voice_input.py             # Voice query recording
├── chat_history.py            # SQLite-based chat history
├── chat_history.db            # Chat history database
├── install.sh                 # Linux auto-installer
├── run.bat                    # Windows run script
├── demo_notebook.ipynb         # Jupyter demo
├── requirements.txt
├── static/
├── templates/
└── sample_pdfs/
    ├── programming/
    └── scanned/
```

---

## Installation

### Windows
```bash
conda create -n pdf_qa python=3.11
conda activate pdf_qa
pip install -r requirements.txt
ollama pull llama3.2

# Download embedding model once (requires internet)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Linux (BEL)
```bash
chmod +x install.sh
./install.sh
```

---

## Running the Project

### Streamlit Web App
```bash
# Windows
conda activate pdf_qa
python -m streamlit run streamlit_app.py

# Linux
source pdf_qa/bin/activate
python3 -m streamlit run streamlit_app.py
```

Open browser: `http://localhost:8501`

### Terminal-based (optional)
```bash
python main.py
```

---

## Offline Mode

Once the embedding model is downloaded once (with internet), the system runs **fully offline**. This is handled via environment flags set at the top of `streamlit_app.py` and `vector_db_manager.py`:

```python
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
```

Ensure `ollama serve` is running locally before starting the app.

---

## Developer

**Isha Thakur**
B.Tech CSE — 2nd Year | MSIT New Delhi
BEL Machine Learning Intern | Radar Department | 2026

[![GitHub](https://img.shields.io/badge/GitHub-ishitathakur22-black)](https://github.com/ishitathakur22)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ishita_Thakur-blue)](https://www.linkedin.com/in/ishita-thakur-857743322/)
