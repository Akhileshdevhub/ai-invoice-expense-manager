"""Collapse merchant name variants ("SWIGGY", "Swiggy Pvt Ltd") to one canonical name.

Two layers, deliberately in this order:

1. Strip common corporate suffixes and normalize case/whitespace. This
   alone handles most variation ("Swiggy Pvt Ltd" -> "Swiggy") without
   needing to know about Swiggy specifically.
2. A small alias table for the handful of merchants whose OCR'd name
   doesn't reduce to the same string after stripping (e.g. "Amzn" for
   Amazon). This is intentionally short — a few common examples for
   demo purposes, not an attempt to hardcode every merchant that exists.
   New aliases are added here as they're observed; that's the
   maintenance story, not a lookup service.
"""

import re

from rapidfuzz import fuzz

CORPORATE_SUFFIXES = [
    r"\bpvt\.?\s*ltd\.?\b", r"\bprivate\s*limited\b", r"\bpvt\.?\b",
    r"\bltd\.?\b", r"\blimited\b", r"\bllp\b", r"\binc\.?\b", r"\bcorp\.?\b",
    r"\bco\.?\b", r"\binternet\b", r"\btechnologies\b", r"\btech\b",
    r"\.?\s*com\b",  # trailing ".com"/". com" (OCR sometimes inserts a stray space before "com")
]

ALIASES = {
    "amzn": "Amazon",
    "amazon.in": "Amazon",
    "amazon seller services": "Amazon",
    "uber india": "Uber",
    "uber india systems": "Uber",  # Uber's printed legal entity name; "Pvt Ltd" strips but "India Systems" doesn't
    "olacabs": "Ola",
    "ola cabs": "Ola",
    "flipkart internet": "Flipkart",
    "myntra designs": "Myntra",
    "big basket": "BigBasket",
    "bigbasket.com": "BigBasket",
    "zomato media": "Zomato",
    "swiggy": "Swiggy",  # already canonical after suffix stripping; kept for clarity
}

FUZZY_MATCH_THRESHOLD = 90  # rapidfuzz token_sort_ratio; conservative to avoid merging unrelated merchants


def normalize_merchant(raw_name: str | None, known_merchants: list[str] | None = None) -> str:
    """Return a canonical merchant name.

    known_merchants (previously normalized names already in the database)
    lets a near-duplicate like "Swiggy Ltd" collapse into an existing
    "Swiggy" row instead of creating a lookalike second one — this is the
    fuzzy-matching layer, used only when the cheaper exact steps miss.
    """
    if not raw_name or not raw_name.strip():
        return "Unknown Merchant"

    cleaned = _strip_suffixes_and_normalize(raw_name)

    alias = ALIASES.get(cleaned.lower())
    if alias:
        return alias

    if known_merchants:
        best = _best_fuzzy_match(cleaned, known_merchants)
        if best:
            return best

    return cleaned


def _strip_suffixes_and_normalize(name: str) -> str:
    cleaned = name.strip()
    for pattern in CORPORATE_SUFFIXES:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[.,]+$", "", cleaned)  # trailing punctuation left after suffix removal
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() if cleaned else name.strip()


def _best_fuzzy_match(name: str, known_merchants: list[str]) -> str | None:
    best_score, best_match = 0, None
    for candidate in known_merchants:
        score = fuzz.token_sort_ratio(name.lower(), candidate.lower())
        if score > best_score:
            best_score, best_match = score, candidate
    if best_score >= FUZZY_MATCH_THRESHOLD:
        return best_match
    return None
