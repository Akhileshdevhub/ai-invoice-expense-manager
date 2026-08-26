"""Light text cleanup on raw OCR output.

Kept intentionally minimal. Aggressive cleanup (e.g. auto-correcting
spelling) risks silently changing a digit or currency symbol in a
financial document, which is worse than leaving noisy text for the
extraction regexes to work around.
"""

import re


def clean_ocr_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Tesseract commonly emits runs of spaces/tabs where a receipt had
    # wide gaps (e.g. between an item name and its price).
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ blank lines down to a max of one, but keep single blank
    # lines — they're often meaningful section breaks on a receipt.
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    return "\n".join(lines)
