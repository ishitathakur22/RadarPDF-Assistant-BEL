import os
from flask import Flask, render_template, request, jsonify
from file_indexer import scan_folders, search_pdf_by_name, save_index
from pdf_processor import extract_pdf_pages
from scanned_handler import (
    is_scanned_pdf,
    extract_text_from_scanned_pdf,
)
from vector_db_manager import create_chunks, create_vector_store, search_similar_chunks
from ollama_connector import get_answer
from folder_suggester import build_folder_embeddings, suggest_folders, check_answer_confidence
from voice_input import get_voice_query

app = Flask(__name__)

# Global variables
root_path = "./sample_pdfs"
pdf_index = []
folder_data = {}
current_index = None
current_chunks = []

# Initialize on startup
print("Initializing PDF Q&A System...")
pdf_index = scan_folders(root_path)
save_index(pdf_index)
folder_data = build_folder_embeddings(root_path)
print(f"Found {len(pdf_index)} PDFs.")
print("System ready.")


@app.route("/")
def home():
    """Render the main page."""
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    """Search for PDFs by name."""
    query = request.json.get("query", "")

    if len(query) < 3:
        return jsonify({
            "error": "Please enter at least 3 characters."
        })

    results = search_pdf_by_name(pdf_index, query)

    if not results:
        return jsonify({
            "error": "No PDFs found. Please try a different keyword."
        })

    return jsonify({
        "results": [
            {"id": i, "name": pdf["name"], "path": pdf["path"]}
            for i, pdf in enumerate(results)
        ]
    })


@app.route("/load", methods=["POST"])
def load_pdfs():
    """Load and process selected PDFs."""
    global current_index, current_chunks

    selected_paths = request.json.get("paths", [])

    if not selected_paths:
        return jsonify({"error": "No PDFs selected."})

    all_chunks = []

    for path in selected_paths:
        pdf_name = os.path.basename(path)
        print(f"Processing: {pdf_name}")

        if is_scanned_pdf(path):
            pages = extract_text_from_scanned_pdf(path)
        else:
            pages = extract_pdf_pages(path)

        chunks = create_chunks(pages)

        for chunk in chunks:
            chunk["pdf_name"] = pdf_name

        all_chunks.extend(chunks)

    current_index, current_chunks = create_vector_store(all_chunks)

    return jsonify({
        "message": f"Loaded {len(selected_paths)} PDF(s). Ready for Q&A.",
        "total_chunks": len(all_chunks)
    })


@app.route("/ask", methods=["POST"])
def ask():
    """Answer a question from loaded PDFs."""
    global current_index, current_chunks

    if current_index is None:
        return jsonify({"error": "Please load PDFs first."})

    query = request.json.get("query", "")

    if not query.strip():
        return jsonify({"error": "Please enter a question."})

    # Get relevant chunks
    relevant_chunks = search_similar_chunks(query, current_index, current_chunks)

    # Generate answer
    answer = get_answer(query, relevant_chunks)

    # Get sources
    sources = [
        {"pdf": chunk["pdf_name"], "page": chunk["page_number"]}
        for chunk in relevant_chunks
    ]

    # Check folder suggestions
    suggestions = []
    if check_answer_confidence(answer):
        current_folders = list(set([
            chunk["pdf_name"] for chunk in current_chunks
        ]))
        suggestions = suggest_folders(query, folder_data, current_folders)

    return jsonify({
        "answer": answer,
        "sources": sources,
        "suggestions": [
            {
                "folder": s["folder"],
                "similarity": f"{s['similarity']:.0%}",
                "pdfs": s["pdf_names"]
            }
            for s in suggestions
        ]
    })


@app.route("/voice", methods=["POST"])
def voice():
    """Record and transcribe voice input."""
    duration = request.json.get("duration", 10)
    text = get_voice_query(duration=duration)
    return jsonify({"text": text})


if __name__ == "__main__":
    app.run(debug=True)