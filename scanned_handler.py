import torch

# Automatically detect GPU and choose processor
if torch.cuda.is_available():
    print("GPU detected. Using ColPali for scanned PDFs.")
    from colpali_processor import (
        is_scanned_pdf,
        extract_text_from_scanned_pdf,
        index_pdf_with_colpali,
        search_with_colpali,
    )
    PROCESSOR = "colpali"
else:
    print("No GPU detected. Using Tesseract OCR for scanned PDFs.")
    from ocr_processor import (
        is_scanned_pdf,
        extract_text_from_scanned_pdf,
    )
    PROCESSOR = "tesseract"

print(f"Scanned PDF processor: {PROCESSOR}")