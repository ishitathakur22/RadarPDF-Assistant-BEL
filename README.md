# Intelligent PDF Q&A System 📄

**BEL Internship 2026 — Radar Department | Bharat Electronics Limited**

An intelligent, fully offline PDF Search and Q&A System built for Bharat Electronics Limited (BEL). The system enables users to search through large collections of PDFs stored across nested folder structures, ask natural language questions, and receive accurate answers — all without internet connectivity.

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
├── PDF Parser (PyMuPDF / Tesseract OCR)
├── Chunker (500 word chunks, 50 word overlap)
├── Embedder (sentence-transformers)
├── FAISS Vector Store
└── Ollama LLM (Llama 3.2) → Answer
        ↓
Smart Folder Suggestion (if answer not found)
```

---

## Features

- Multi-PDF search across folders and subfolders
- Voice-based query input using OpenAI Whisper
- RAG pipeline using LangChain + FAISS
- Scanned PDF support — Tesseract OCR (CPU) / ColPali (GPU)
- Smart folder suggestion when answer not found
- Fully offline — no internet required
- Flask-based web frontend
- Cross-platform — Windows development, Linux deployment

---

## Tech Stack

| Component | Technology |
|---|---|
| Language Model | Ollama — Llama 3.2 |
| RAG Pipeline | LangChain + FAISS |
| PDF Parsing | PyMuPDF |
| Scanned PDFs | Tesseract OCR / ColPali |
| Voice Input | OpenAI Whisper |
| Embeddings | sentence-transformers |
| Frontend | Flask + HTML/CSS/JS |
| Auto Processor | GPU → ColPali, CPU → Tesseract |

---

## Project Structure

```
PDF_QA_System/
├── main.py                  # Terminal-based pipeline
├── app.py                   # Flask web application
├── file_indexer.py          # Folder scanning and PDF indexing
├── pdf_processor.py         # Text-based PDF extraction
├── vector_db_manager.py     # FAISS vector store
├── ollama_connector.py      # LLM answer generation
├── ocr_processor.py         # Tesseract OCR (CPU)
├── colpali_processor.py     # ColPali visual model (GPU)
├── scanned_handler.py       # Auto GPU/CPU detection
├── folder_suggester.py      # Smart folder suggestions
├── voice_input.py           # Whisper voice input
├── install.sh               # Linux auto-installer
├── check_setup.sh           # System verification
├── demo_notebook.ipynb      # Jupyter demo
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
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
```

### Linux (BEL)
```bash
chmod +x install.sh
./install.sh
```

---

## Running the Project

### Terminal based
```bash
# Windows
conda activate pdf_qa
python main.py

# Linux
source pdf_qa/bin/activate
python3 main.py
```

### Web Frontend
```bash
# Windows
python app.py

# Linux
python3 app.py
```

Open browser: `http://localhost:5000`

---

## Developer

**Isha Thakur**
B.Tech CSE — 2nd Year | MSIT New Delhi
BEL Machine Learning Intern | Radar Department | 2026


---

**Step 6** — Neeche **"Commit changes"** click karo → **"Commit directly to main"** → **"Commit changes"**

---

Screenshot bhejo! 🔥😄
