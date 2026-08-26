"""Shared data shape for a transaction.

A plain dataclass rather than a full ORM model — every layer of the
pipeline (extraction, classification, database, UI) passes this same
shape around, so it's defined once here instead of re-declared per layer.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


VALID_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Software",
    "Education",
    "Healthcare",
    "Utilities",
    "Entertainment",
    "Rent",
    "Bills",
    "Groceries",
    "Other",
]

# Extraction writes here; analytics only ever reads "confirmed" rows.
PENDING = "pending"
CONFIRMED = "confirmed"


@dataclass
class Transaction:
    merchant_raw: str
    merchant: str
    amount: Optional[float]
    currency: str
    transaction_date: Optional[str]  # ISO 8601: YYYY-MM-DD
    category: str
    source_file: str
    raw_text: str
    invoice_number: Optional[str] = None
    tax: Optional[float] = None
    subtotal: Optional[float] = None
    payment_method: Optional[str] = None
    extraction_confidence: float = 0.0
    confirmation_status: str = PENDING
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)
