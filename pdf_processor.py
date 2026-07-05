import fitz  # PyMuPDF
import os
import base64
from PIL import Image #pillow

def extract_pdf_pages(pdf_path):
    """
    Extract text from PDF.
    Automatically detects scanned vs text-based.
    """
    from ocr_processor import (
        is_scanned_pdf,
        extract_text_from_scanned_pdf
    )

    # Check if scanned
    if is_scanned_pdf(pdf_path):
        # Use OCR for scanned PDFs
        return extract_text_from_scanned_pdf(pdf_path)
    else:
        # Use normal text extraction
        import fitz
        import base64
        import os

        doc = fitz.open(pdf_path)
        pages_data = []
        os.makedirs("temp_images", exist_ok=True)

        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            image_path = f"temp_images/page_{i+1:04d}.png"
            pix.save(image_path)

            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(
                    img_file.read()
                ).decode("utf-8")

            text = page.get_text()

            pages_data.append({
                "page_number": i + 1,
                "image_path": image_path,
                "base64_image": encoded,
                "text_content": text,
            })

            print(f"  Page {i + 1} processed.")

        doc.close()
        return pages_data