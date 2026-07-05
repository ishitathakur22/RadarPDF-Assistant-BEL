import os
import fitz
import pytesseract
from PIL import Image
import io

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = (
    r"E:\tesseract\tesseract.exe"
)


def is_scanned_pdf(pdf_path, text_threshold=50):
    """
    Detect whether a PDF is scanned or text-based.
    If average text per page is below threshold,
    it is likely scanned.

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


def extract_text_from_scanned_pdf(pdf_path):
    """
    Extract text from a scanned PDF using OCR.

    Args:
        pdf_path: Path to the scanned PDF file.

    Returns:
        List of page data dictionaries.
    """
    print(f"Running OCR on scanned PDF: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages_data = []

    for i, page in enumerate(doc):

        # Convert page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        # Run OCR on the image
        text = pytesseract.image_to_string(image)

        pages_data.append({
            "page_number": i + 1,
            "text_content": text,
        })

        print(f"  Page {i + 1} OCR complete.")

    doc.close()
    print(f"OCR complete. Total pages: {len(pages_data)}")
    return pages_data


# Test
if __name__ == "__main__":
    pdf_path = input("Enter scanned PDF path: ")

    scanned = is_scanned_pdf(pdf_path)
    print(f"Is scanned: {scanned}")

    if scanned:
        pages = extract_text_from_scanned_pdf(pdf_path)
        print(f"\nFirst page OCR text preview:")
        print(pages[0]["text_content"][:300])
    else:
        print("This is a text-based PDF.")
        print("Use pdf_processor.py instead.")