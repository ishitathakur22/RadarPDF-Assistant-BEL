#!/bin/bash
echo "=== PDF Q&A System - Installation ==="
echo ""

# System packages
echo "Installing system packages..."
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev tesseract-ocr ffmpeg -y

# Virtual environment
echo "Creating virtual environment..."
python3.11 -m venv pdf_qa
source pdf_qa/bin/activate

# Python packages
echo "Installing Python packages..."
pip install -r requirements.txt

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "Note: Ollama must be installed separately (see README for offline transfer instructions)."
echo ""
echo "To run the project:"
echo "  source pdf_qa/bin/activate"
echo "  python3.11 -m streamlit run streamlit_app.py --server.fileWatcherType none"

# Download embedding model for offline use (requires internet during this step only)
python3.11 -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('all-MiniLM-L6-v2')
print('Embedding model downloaded!')
"