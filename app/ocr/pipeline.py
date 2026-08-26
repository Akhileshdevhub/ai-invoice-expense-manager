"""Orchestrates validation -> PDF/image loading -> preprocessing -> OCR.

This is the one function the UI calls; everything else in app/ocr is an
implementation detail behind it.
"""

import io
from dataclasses import dataclass

from pdf2image import convert_from_bytes
from PIL import Image

from app.ocr.engine import run_ocr_with_confidence
from app.ocr.preprocess import preprocess_for_ocr
from app.utils.validators import validate_upload

# Receipts are short; a multi-page PDF is almost always a scanned
# statement rather than a single receipt, which this pipeline isn't
# built to segment. OCR the first page and say so, rather than silently
# guessing which page has the total.
MAX_PDF_PAGES_PROCESSED = 1


@dataclass
class OcrResult:
    success: bool
    raw_text: str = ""
    ocr_confidence: float = 0.0
    error: str | None = None


def process_upload(filename: str, file_bytes: bytes) -> OcrResult:
    validation = validate_upload(filename, file_bytes)
    if not validation.is_valid:
        return OcrResult(success=False, error=validation.error)

    try:
        image = _load_first_page(filename, file_bytes)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a clear error, not a crash
        return OcrResult(success=False, error=f"Could not open file: {exc}")

    try:
        processed = preprocess_for_ocr(image)
        text, confidence = run_ocr_with_confidence(processed)
    except Exception as exc:  # noqa: BLE001
        return OcrResult(success=False, error=f"OCR failed: {exc}")

    if not text.strip():
        return OcrResult(
            success=False,
            error="OCR could not read any text from this file. Try a clearer photo.",
        )

    return OcrResult(success=True, raw_text=text, ocr_confidence=confidence)


def _load_first_page(filename: str, file_bytes: bytes) -> Image.Image:
    if filename.lower().endswith(".pdf"):
        pages = convert_from_bytes(file_bytes, dpi=300, first_page=1, last_page=MAX_PDF_PAGES_PROCESSED)
        if not pages:
            raise ValueError("PDF has no pages")
        return pages[0]
    return Image.open(io.BytesIO(file_bytes))
