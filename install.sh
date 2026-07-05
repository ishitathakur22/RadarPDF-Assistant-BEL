#!/bin/bash
echo "=== PDF Q&A System - Installation ==="
echo ""

# System packages
echo "Installing system packages..."
sudo apt update
sudo apt install python3 python3-pip tesseract-ocr ffmpeg -y

# Ollama
echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Virtual environment
echo "Creating virtual environment..."
python3 -m venv pdf_qa
source pdf_qa/bin/activate

# Python packages
echo "Installing Python packages..."
pip install -r requirements.txt

# PyTorch + ColPali (GPU)
echo "Installing PyTorch and ColPali..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install byaldi colpali-engine

# Ollama model
echo "Downloading Llama 3.2 model..."
ollama pull llama3.2

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "To run the project:"
echo "  source pdf_qa/bin/activate"
echo "  ollama serve &"
echo "  python3 main.py"