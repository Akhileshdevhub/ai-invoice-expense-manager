"""Thin wrapper around pytesseract.

Isolated in its own module so the rest of the app depends on "give me
text from an image" rather than on pytesseract's API directly. Swapping
in PaddleOCR or a cloud OCR service later means changing this one file —
see docs/OCR_PIPELINE.md for why Tesseract was chosen and what its
limitations are.
"""

import pytesseract
from PIL import Image

# --psm 6: "assume a single uniform block of text". Receipts are dense,
# narrow columns of text rather than a page layout with headers/columns,
# and psm 6 consistently outperformed Tesseract's default (psm 3, which
# tries to detect a page layout) on the sample receipts used during
# development.
TESSERACT_CONFIG = "--oem 3 --psm 6"


def run_ocr(image: Image.Image) -> str:
    """Return raw OCR text for a preprocessed image. May be empty on a blank/unreadable image."""
    return pytesseract.image_to_string(image, config=TESSERACT_CONFIG)


def run_ocr_with_confidence(image: Image.Image) -> tuple[str, float]:
    """Return (text, mean_word_confidence 0-100) using Tesseract's own per-word confidences.

    Tesseract's confidence score is per detected word box, not per
    character or per field — it tells you how sure the engine is about
    what it read, not whether that word is the amount vs. an address
    line. That's why extraction (app/extraction) still needs its own
    heuristics to decide *which* words matter.
    """
    data = pytesseract.image_to_data(
        image, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT
    )
    confidences = [int(c) for c in data["conf"] if c not in ("-1", -1)]
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    text = pytesseract.image_to_string(image, config=TESSERACT_CONFIG)
    return text, mean_conf
