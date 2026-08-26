"""CRUD functions for the transactions table.

Kept as plain functions over a connection rather than a class — there's no
state to wrap, just queries. Every function that returns rows returns
plain dicts (via sqlite3.Row -> dict) so callers don't need to know
anything about sqlite3 itself.
"""

from datetime import datetime, timezone
from typing import Optional

from app.database.db import get_connection
from app.models.transaction import Transaction, CONFIRMED


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_dict(row) -> dict:
    return dict(row) if row is not None else None


def insert_transaction(txn: Transaction) -> int:
    """Insert a newly-extracted transaction (usually confirmation_status='pending')."""
    conn = get_connection()
    try:
        now = _now()
        cur = conn.execute(
            """
            INSERT INTO transactions (
                merchant_raw, merchant, amount, currency, transaction_date,
                category, invoice_number, tax, subtotal, payment_method,
                source_file, raw_text, extraction_confidence,
                confirmation_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                txn.merchant_raw, txn.merchant, txn.amount, txn.currency,
                txn.transaction_date, txn.category, txn.invoice_number,
                txn.tax, txn.subtotal, txn.payment_method, txn.source_file,
                txn.raw_text, txn.extraction_confidence,
                txn.confirmation_status, now, now,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_transaction(txn_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (txn_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def list_transactions(
    status: Optional[str] = None,
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
) -> list[dict]:
    """List transactions with optional filters, newest first.

    All filters are optional and combine with AND — this backs both the
    transaction table's filter controls and the analytics layer's
    "confirmed transactions only" queries.
    """
    conn = get_connection()
    try:
        clauses = []
        params: list = []

        if status:
            clauses.append("confirmation_status = ?")
            params.append(status)
        if category:
            clauses.append("category = ?")
            params.append(category)
        if merchant:
            clauses.append("merchant LIKE ?")
            params.append(f"%{merchant}%")
        if date_from:
            clauses.append("transaction_date >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("transaction_date <= ?")
            params.append(date_to)
        if amount_min is not None:
            clauses.append("amount >= ?")
            params.append(amount_min)
        if amount_max is not None:
            clauses.append("amount <= ?")
            params.append(amount_max)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM transactions {where} "
            "ORDER BY transaction_date DESC, id DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_transaction(txn_id: int, fields: dict) -> None:
    """Update arbitrary allowed fields on a transaction (edit/recategorize/confirm)."""
    if not fields:
        return
    allowed = {
        "merchant", "amount", "currency", "transaction_date", "category",
        "invoice_number", "tax", "subtotal", "payment_method",
        "confirmation_status",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = _now()

    conn = get_connection()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [txn_id]
        conn.execute(
            f"UPDATE transactions SET {set_clause} WHERE id = ?", params
        )
        conn.commit()
    finally:
        conn.close()


def confirm_transaction(txn_id: int, edited_fields: dict) -> None:
    """Apply the user's edits from the verification screen and mark confirmed.

    Only confirmed rows are visible to analytics — see docs/ARCHITECTURE.md
    for why this gate exists.
    """
    edited_fields = dict(edited_fields)
    edited_fields["confirmation_status"] = CONFIRMED
    update_transaction(txn_id, edited_fields)


def delete_transaction(txn_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        conn.commit()
    finally:
        conn.close()


def get_distinct_merchants(status: str = CONFIRMED) -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT merchant FROM transactions "
            "WHERE confirmation_status = ? ORDER BY merchant",
            (status,),
        ).fetchall()
        return [r["merchant"] for r in rows]
    finally:
        conn.close()
