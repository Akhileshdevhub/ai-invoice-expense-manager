"""Pull structured fields out of cleaned OCR text using regex heuristics.

There is no ML here on purpose. Receipt layouts vary, but the *labels*
("Total", "GST", "Invoice No") are fairly standardized, so a labeled-
keyword search gets most of the way there and — unlike a model — every
decision it makes is inspectable and fixable. See docs/OCR_PIPELINE.md
for the known failure cases (unlabeled totals, handwritten receipts,
non-standard layouts).

Nothing here invents a value: if a field can't be found, it comes back
as None and the caller (the verification UI) asks the user to fill it in.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from dateutil import parser as dateutil_parser

CURRENCY_SYMBOLS = {
    "₹": "INR", "rs.": "INR", "rs": "INR", "inr": "INR",
    "$": "USD", "usd": "USD",
    "€": "EUR", "eur": "EUR",
    "£": "GBP", "gbp": "GBP",
}

# Ordered by how strongly the label implies "this is the amount the
# customer actually paid" — a receipt can print subtotal, discount, tax,
# and total all on separate lines, and we want the total, not the first
# number on the page.
TOTAL_LABELS = [
    r"grand\s*total", r"total\s*fare", r"total\s*amount", r"total\s*payable",
    r"amount\s*payable", r"amount\s*paid", r"amount\s*due",
    r"net\s*payable", r"net\s*amount", r"bill\s*amount", r"total",
]
SUBTOTAL_LABELS = [r"sub\s*total", r"item\s*total", r"taxable\s*(?:value|amount)"]
TAX_LABELS = [r"(?:c|s|i)?gst(?:\s*\d{1,2}%)?", r"vat", r"tax(?:\s*\d{1,2}%)?"]
INVOICE_LABELS = [
    r"invoice\s*(?:no\.?|number|#)", r"receipt\s*(?:no\.?|number|#)",
    r"order\s*id", r"bill\s*(?:no\.?|number)",
]
PAYMENT_KEYWORDS = {
    "upi": "UPI", "gpay": "UPI", "google pay": "UPI", "phonepe": "UPI", "paytm": "UPI",
    "credit card": "Card", "debit card": "Card", "card": "Card",
    "net banking": "Net Banking", "netbanking": "Net Banking",
    "cash": "Cash", "wallet": "Wallet", "cod": "Cash on Delivery",
}

# Boilerplate lines that sit above the merchant name (or aren't a
# merchant name at all) and should be skipped when guessing the merchant.
MERCHANT_SKIP_PATTERNS = [
    r"^tax\s*invoice$", r"^invoice$", r"^receipt$", r"^original\b",
    r"^duplicate\b", r"^cash\s*memo$", r"^bill\s*of\s*supply$",
    r"^www\.", r"^gstin", r"^phone", r"^tel\b", r"^\d+$",
]

# Negative lookaround on both sides so a number embedded in an alphanumeric
# ID (e.g. "EB2026080099") is never picked up as an amount — a real amount
# is always its own token, bounded by whitespace, a currency symbol, or
# punctuation, never glued directly to letters or more digits.
AMOUNT_NUMBER = r"(?<![A-Za-z0-9])[\d,]+(?:\.\d{1,2})?(?![A-Za-z0-9])"


@dataclass
class ExtractedFields:
    merchant_raw: Optional[str] = None
    amount: Optional[float] = None
    amount_source: str = "not_found"  # 'labeled_total' | 'largest_amount' | 'not_found'
    currency: str = "INR"
    transaction_date: Optional[str] = None
    invoice_number: Optional[str] = None
    tax: Optional[float] = None
    subtotal: Optional[float] = None
    payment_method: Optional[str] = None
    confidence: float = 0.0


def extract_fields(raw_text: str) -> ExtractedFields:
    lines = raw_text.split("\n")

    amount, amount_source = extract_amount(raw_text)
    txn_date = extract_date(raw_text)
    result = ExtractedFields(
        merchant_raw=extract_merchant(lines),
        amount=amount,
        amount_source=amount_source,
        currency=extract_currency(raw_text),
        transaction_date=txn_date,
        invoice_number=_extract_labeled_text(raw_text, INVOICE_LABELS),
        tax=_extract_labeled_amount(raw_text, TAX_LABELS),
        subtotal=_extract_labeled_amount(raw_text, SUBTOTAL_LABELS),
        payment_method=extract_payment_method(raw_text),
    )
    result.confidence = _estimate_confidence(result)
    return result


def extract_amount(text: str) -> tuple[Optional[float], str]:
    """Prefer a clearly-labeled total; fall back to the largest amount on the page.

    The fallback is a deliberate compromise: on a receipt where OCR
    garbled the word "Total", the largest printed amount is usually still
    the total (line items are smaller). It's flagged with a different
    amount_source so the UI can tell the user it's a guess.
    """
    for label in TOTAL_LABELS:
        match = re.search(
            rf"{label}\s*[:\-]?\s*(?:{'|'.join(re.escape(s) for s in CURRENCY_SYMBOLS)})?\s*({AMOUNT_NUMBER})",
            text, re.IGNORECASE,
        )
        if match:
            value = _to_float(match.group(1))
            if value is not None:
                return value, "labeled_total"

    all_amounts = [
        _to_float(m) for m in re.findall(AMOUNT_NUMBER, text)
    ]
    all_amounts = [a for a in all_amounts if a is not None and a > 0]
    if all_amounts:
        return max(all_amounts), "largest_amount"

    return None, "not_found"


def extract_date(text: str) -> Optional[str]:
    """Return the first parseable date, normalized to ISO 8601 (YYYY-MM-DD)."""
    patterns = [
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",     # 26 Aug 2026
        r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b",    # Aug 26, 2026
        r"\b\d{4}-\d{1,2}-\d{1,2}\b",                 # 2026-08-26
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",            # 26/08/2026 or 26-08-2026
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        parsed = _parse_date(match.group(0))
        if parsed:
            return parsed
    return None


def _parse_date(raw: str) -> Optional[str]:
    # A year-first string (2026-08-05) is unambiguous, but dateutil's
    # dayfirst=True still swaps the remaining two fields for this shape
    # (confirmed by trying it) — so that case is parsed directly instead
    # of trusting dayfirst to leave it alone.
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", raw)
    if iso_match:
        try:
            parsed = datetime(int(iso_match[1]), int(iso_match[2]), int(iso_match[3]))
        except ValueError:
            return None
    else:
        # dayfirst=True because every numeric-date sample this app targets
        # (India-issued receipts) writes DD/MM/YYYY, not MM/DD/YYYY. This
        # is a documented assumption, not a universal one — see
        # docs/OCR_PIPELINE.md.
        try:
            parsed = dateutil_parser.parse(raw, dayfirst=True)
        except (ValueError, OverflowError):
            return None

    if parsed.year < 2000 or parsed.year > datetime.now().year + 1:
        return None
    return parsed.date().isoformat()


def extract_merchant(lines: list[str]) -> Optional[str]:
    """Guess the merchant name: usually the first substantive line before boilerplate.

    Receipts near-universally print the business name at the very top,
    larger than everything else — OCR reads it as the first line(s).
    """
    for line in lines[:6]:
        candidate = line.strip()
        if len(candidate) < 2:
            continue
        if any(re.match(p, candidate, re.IGNORECASE) for p in MERCHANT_SKIP_PATTERNS):
            continue
        alpha_chars = sum(c.isalpha() for c in candidate)
        if alpha_chars < 2:
            continue
        return candidate
    return None


def extract_currency(text: str) -> str:
    lowered = text.lower()
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in lowered:
            return code
    return "INR"  # default market for this project — see docs/LIMITATIONS.md


def extract_payment_method(text: str) -> Optional[str]:
    lowered = text.lower()
    for keyword, method in PAYMENT_KEYWORDS.items():
        if keyword in lowered:
            return method
    return None


def _extract_labeled_amount(text: str, labels: list[str]) -> Optional[float]:
    raw = _extract_labeled_text(text, labels, value_pattern=AMOUNT_NUMBER)
    return _to_float(raw) if raw else None


def _extract_labeled_text(
    text: str, labels: list[str], value_pattern: str = r"[A-Za-z0-9\-/]+"
) -> Optional[str]:
    for label in labels:
        match = re.search(
            rf"{label}\s*[:\-#]?\s*({value_pattern})", text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
    return None


def _to_float(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    try:
        return round(float(raw.replace(",", "")), 2)
    except ValueError:
        return None


def _estimate_confidence(result: ExtractedFields) -> float:
    """A heuristic 0-1 score, not a calibrated probability.

    It exists to drive the UI (flag low-confidence extractions for extra
    scrutiny), not to be reported as a statistical accuracy figure.
    """
    score = 0.0
    if result.amount is not None:
        score += 0.5 if result.amount_source == "labeled_total" else 0.25
    if result.transaction_date is not None:
        score += 0.3
    if result.merchant_raw is not None:
        score += 0.2
    return round(min(score, 1.0), 2)
