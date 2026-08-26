"""Tests for the database layer, run against a temp SQLite file (never data/app.db)."""

import os
import tempfile
from pathlib import Path

import pytest

from app.database.db import init_db
from app.database import repository as repo
from app.models.transaction import Transaction, PENDING, CONFIRMED


@pytest.fixture
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_PATH", path)
    init_db(Path(path))
    yield path
    os.remove(path)


def _sample_transaction(**overrides) -> Transaction:
    fields = dict(
        merchant_raw="SWIGGY", merchant="Swiggy", amount=450.0, currency="INR",
        transaction_date="2026-08-10", category="Food", source_file="receipt.jpg",
        raw_text="Swiggy\nTotal 450",
    )
    fields.update(overrides)
    return Transaction(**fields)


def test_insert_and_get_transaction(temp_db):
    txn_id = repo.insert_transaction(_sample_transaction())
    row = repo.get_transaction(txn_id)
    assert row["merchant"] == "Swiggy"
    assert row["confirmation_status"] == PENDING


def test_confirm_transaction_updates_status_and_edited_fields(temp_db):
    txn_id = repo.insert_transaction(_sample_transaction())
    repo.confirm_transaction(txn_id, {"amount": 500.0, "category": "Groceries"})
    row = repo.get_transaction(txn_id)
    assert row["confirmation_status"] == CONFIRMED
    assert row["amount"] == 500.0
    assert row["category"] == "Groceries"


def test_list_transactions_filters_by_status(temp_db):
    repo.insert_transaction(_sample_transaction())
    confirmed_id = repo.insert_transaction(_sample_transaction(merchant="Zomato"))
    repo.confirm_transaction(confirmed_id, {})

    pending = repo.list_transactions(status=PENDING)
    confirmed = repo.list_transactions(status=CONFIRMED)
    assert len(pending) == 1
    assert len(confirmed) == 1
    assert confirmed[0]["merchant"] == "Zomato"


def test_delete_transaction_removes_row(temp_db):
    txn_id = repo.insert_transaction(_sample_transaction())
    repo.delete_transaction(txn_id)
    assert repo.get_transaction(txn_id) is None


def test_list_transactions_filters_by_amount_range(temp_db):
    repo.insert_transaction(_sample_transaction(amount=100.0))
    repo.insert_transaction(_sample_transaction(amount=900.0))
    results = repo.list_transactions(amount_min=500)
    assert len(results) == 1
    assert results[0]["amount"] == 900.0
