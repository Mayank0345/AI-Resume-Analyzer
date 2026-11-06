"""Extract readable text from uploaded PDF resume data."""

from __future__ import annotations

from io import BytesIO

from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Return text from a PDF held in memory.

    Args:
        pdf_bytes: The raw bytes from an uploaded PDF file.

    Raises:
        ValueError: If the PDF is empty, locked, or contains no extractable text.
    """
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    reader = PdfReader(BytesIO(pdf_bytes))
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError("This PDF is password-protected. Upload an unlocked PDF.")

    pages = [page.extract_text() or "" for page in reader.pages]
    extracted_text = "\n".join(pages).strip()
    if not extracted_text:
        raise ValueError(
            "No text could be extracted. Scanned PDFs need OCR before analysis."
        )
    return extracted_text
