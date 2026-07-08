import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

import pickle
import faiss
import numpy as np
from file_indexer import scan_folders
from pdf_processor import extract_pdf_pages
from vector_db_manager import create_chunks, embedder  # ← embedder import karo
from scanned_handler import is_scanned_pdf, extract_text_from_scanned_pdf

# Paths
INDEX_SAVE_PATH = "./saved_index/faiss_index.bin"
CHUNKS_SAVE_PATH = "./saved_index/chunks.pkl"

# embedder yahan se import ho raha hai — dobara load nahi hoga! ✅


def index_exists():
    """Check if saved index exists."""
    return os.path.exists(INDEX_SAVE_PATH) and os.path.exists(CHUNKS_SAVE_PATH)


def save_index(index, chunks):
    """Save FAISS index and chunks to disk."""
    os.makedirs("./saved_index", exist_ok=True)
    faiss.write_index(index, INDEX_SAVE_PATH)
    with open(CHUNKS_SAVE_PATH, "wb") as f:
        pickle.dump(chunks, f)
    print("Index saved successfully.")


def load_index():
    """Load FAISS index and chunks from disk."""
    print("Loading saved index...")
    index = faiss.read_index(INDEX_SAVE_PATH)
    with open(CHUNKS_SAVE_PATH, "rb") as f:
        chunks = pickle.load(f)
    print(f"Index loaded. Total vectors: {index.ntotal}")
    return index, chunks


def build_index(root_path):


    """
    Scan all PDFs and build FAISS index.
    Save to disk for future use.
    """
    print(f"Scanning folder: {root_path}")
    pdf_index = scan_folders(root_path)
    print(f"Found {len(pdf_index)} PDFs.")

    all_chunks = []

    for pdf in pdf_index:
        print(f"Processing: {pdf['name']}...")

        try:
            if is_scanned_pdf(pdf["path"]):
                pages = extract_text_from_scanned_pdf(pdf["path"])
            else:
                pages = extract_pdf_pages(pdf["path"])

            chunks = create_chunks(pages)

            for chunk in chunks:
                chunk["pdf_name"] = pdf["name"]
                chunk["pdf_path"] = pdf["path"]
                chunk["folder"] = pdf["folder"]

            all_chunks.extend(chunks)
            print(f"  {len(chunks)} chunks created.")

        except Exception as e:
            print(f"  Error processing {pdf['name']}: {e}")
            continue

    print(f"\nTotal chunks: {len(all_chunks)}")

    # Create embeddings using shared embedder
    print("Creating embeddings...")
    texts = [c.get("text_content", c.get("text", "")) for c in all_chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    print(f"Index built. Total vectors: {index.ntotal}")

    # Save to disk
    save_index(index, all_chunks)

    return index, all_chunks

def sync_index(root_path):
    """
    Detect new PDFs (not already indexed) and add ONLY those to the index.
    Much faster than full rebuild — reuses existing embeddings.
    Returns: (index, chunks, num_new_pdfs)
    """
    # Load existing index if present, otherwise start fresh
    if index_exists():
        index, chunks = load_index()
        already_indexed_paths = set(c.get("pdf_path") for c in chunks if "pdf_path" in c)
    else:
        index = None
        chunks = []
        already_indexed_paths = set()

    print(f"Scanning folder: {root_path}")
    pdf_index = scan_folders(root_path)

    # Find PDFs that are NOT yet indexed
    new_pdfs = [pdf for pdf in pdf_index if pdf["path"] not in already_indexed_paths]

    if not new_pdfs:
        print("No new PDFs found. Index is already up to date.")
        return index, chunks, 0

    print(f"Found {len(new_pdfs)} new PDF(s) to index.")

    new_chunks = []

    for pdf in new_pdfs:
        print(f"Processing new PDF: {pdf['name']}...")
        try:
            if is_scanned_pdf(pdf["path"]):
                pages = extract_text_from_scanned_pdf(pdf["path"])
            else:
                pages = extract_pdf_pages(pdf["path"])

            pdf_chunks = create_chunks(pages)

            for chunk in pdf_chunks:
                chunk["pdf_name"] = pdf["name"]
                chunk["pdf_path"] = pdf["path"]
                chunk["folder"] = pdf["folder"]

            new_chunks.extend(pdf_chunks)
            print(f"  {len(pdf_chunks)} chunks created.")

        except Exception as e:
            print(f"  Error processing {pdf['name']}: {e}")
            continue

    if not new_chunks:
        print("No chunks generated from new PDFs.")
        return index, chunks, 0

    # Embed ONLY the new chunks
    print("Creating embeddings for new chunks...")
    texts = [c.get("text_content", c.get("text", "")) for c in new_chunks]
    new_embeddings = embedder.encode(texts, show_progress_bar=True)
    new_embeddings = np.array(new_embeddings).astype("float32")

    if index is None:
        # No existing index — create a fresh one
        dimension = new_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)

    # Add new vectors to the existing index (no rebuild needed!)
    index.add(new_embeddings)
    chunks.extend(new_chunks)

    print(f"Index updated. Total vectors now: {index.ntotal}")

    # Save updated index + chunks
    save_index(index, chunks)

    return index, chunks, len(new_pdfs)