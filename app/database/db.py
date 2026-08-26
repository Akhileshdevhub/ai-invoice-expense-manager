"""SQLite connection + schema setup.

Plain sqlite3, no ORM. The app has one table that matters (transactions);
an ORM would buy abstraction we don't need at this scale and would hide
the SQL from anyone trying to learn how the queries actually work.
"""

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_raw           TEXT NOT NULL,
    merchant                TEXT NOT NULL,
    amount                    REAL,
    currency                    TEXT NOT NULL DEFAULT 'INR',
    transaction_date              TEXT,
    category                        TEXT NOT NULL DEFAULT 'Other',
    invoice_number                    TEXT,
    tax                                  REAL,
    subtotal                              REAL,
    payment_method                          TEXT,
    source_file                              TEXT,
    raw_text                                  TEXT,
    extraction_confidence                      REAL NOT NULL DEFAULT 0,
    confirmation_status                          TEXT NOT NULL DEFAULT 'pending',
    created_at                                    TEXT NOT NULL,
    updated_at                                      TEXT NOT NULL
);

-- Almost every analytics query filters by status and sorts/filters by date,
-- so this is the one index worth having at this scale.
CREATE INDEX IF NOT EXISTS idx_transactions_status_date
    ON transactions (confirmation_status, transaction_date);
"""


def get_db_path() -> Path:
    env_path = os.environ.get("DATABASE_PATH")
    return Path(env_path) if env_path else DEFAULT_DB_PATH


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
