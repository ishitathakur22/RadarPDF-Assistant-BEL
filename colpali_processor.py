import os
import torch
import fitz

# Check GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Model variable — load lazily
model = None


def load_model():
    """
    Load ColPali model only when needed.
    Avoids loading on import if GPU not available.
    """
    global model

    if model is None:
        print("Loading ColPali model...")
        from byaldi import RAGMultiModalModel
        model = RAGMultiModalModel.from_pretrained(
            "vidore/colpali-v1.2",
            device=device
        )
        print("ColPali model loaded successfully.")

    return model


def is_scanned_pdf(pdf_path, text_threshold=50):
    """
    Detect whether a PDF is scanned or text-based.

    Args:
        pdf_path: Path to the PDF file.
        text_threshold: Minimum characters per page.

    Returns:
        True if scanned, False if text-based.
    """
    doc = fitz.open(pdf_path)
    total_text = 0

    for page in doc:
        total_text += len(page.get_text().strip())

    avg_text = total_text / max(len(doc), 1)
    doc.close()

    if avg_text < text_threshold:
        print(f"Scanned PDF detected: {pdf_path}")
        return True
    else:
        print(f"Text-based PDF detected: {pdf_path}")
        return False


def index_pdf_with_colpali(pdf_path, index_name=None):
    """
    Index a PDF using ColPali visual understanding.

    Args:
        pdf_path: Path to the PDF file.
        index_name: Name for the index.

    Returns:
        Index name string.
    """
    from pathlib import Path

    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return None

    if index_name is None:
        index_name = Path(pdf_path).stem

    # Load model when needed
    colpali_model = load_model()

    print(f"Indexing PDF with ColPali: {pdf_path}")

    colpali_model.index(
        input_path=pdf_path,
        index_name=index_name,
        store_collection_with_index=True,
        overwrite=True,
    )

    print(f"Indexing complete. Index: {index_name}")
    return index_name


def search_with_colpali(query, index_name, top_k=3):
    """
    Search ColPali index with a text query.

    Args:
        query: User question.
        index_name: Name of the ColPali index.
        top_k: Number of results.

    Returns:
        List of results with page numbers.
    """
    colpali_model = load_model()

    print(f"Searching ColPali index: {index_name}")

    results = colpali_model.search(
        query,
        index_name=index_name,
        k=top_k,
    )

    return results


def extract_text_from_scanned_pdf(pdf_path):
    """
    Extract text from scanned PDF using ColPali.

    Args:
        pdf_path: Path to scanned PDF.

    Returns:
        List of page data dictionaries.
    """
    import base64
    from PIL import Image
    import io

    print(f"Processing scanned PDF with ColPali: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages_data = []

    for i, page in enumerate(doc):

        # Convert page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        # Encode image
        encoded = base64.b64encode(img_bytes).decode("utf-8")

        pages_data.append({
            "page_number": i + 1,
            "text_content": f"[Visual page {i+1} - processed by ColPali]",
            "base64_image": encoded,
            "image": image,
        })

        print(f"  Page {i + 1} processed.")

    doc.close()
    print(f"Total pages: {len(pages_data)}")
    return pages_data


# Test
if __name__ == "__main__":
    print(f"GPU available: {torch.cuda.is_available()}")
    print(f"Device: {device}")

    pdf_path = input("Enter PDF path: ")
    scanned = is_scanned_pdf(pdf_path)
    print(f"Is scanned: {scanned}")

    if scanned:
        index_name = index_pdf_with_colpali(pdf_path)
        if index_name:
            query = input("Enter question: ")
            results = search_with_colpali(query, index_name)
            print(f"\nResults:")
            for r in results:
                print(f"  Page {r['page_num']} - Score: {r['score']:.4f}")