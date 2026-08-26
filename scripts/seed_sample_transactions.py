"""Seed the database with synthetic, already-confirmed sample transactions.

Purpose: give the dashboard something to show for demos/screenshots
without requiring a real spending history. These are clearly synthetic
(random.seed fixed for reproducibility) and inserted directly as
'confirmed' — they skip OCR entirely because they aren't meant to test
that pipeline, only the analytics/dashboard layer.

Run: python scripts/seed_sample_transactions.py
"""

import random
from datetime import date, timedelta

from app.database.db import init_db
from app.database import repository as repo
from app.models.transaction import Transaction, CONFIRMED

random.seed(7)

# (merchant, category, amount range)
SAMPLE_MERCHANTS = [
    ("Swiggy", "Food", (150, 550)),
    ("Zomato", "Food", (150, 500)),
    ("Cafe Coffee Day", "Food", (80, 250)),
    ("Uber", "Travel", (100, 450)),
    ("Ola", "Travel", (100, 400)),
    ("IRCTC", "Travel", (400, 1500)),
    ("Amazon", "Shopping", (300, 2500)),
    ("Flipkart", "Shopping", (300, 2000)),
    ("Myntra", "Shopping", (500, 1800)),
    ("GitHub", "Software", (350, 900)),
    ("Notion", "Software", (400, 400)),
    ("Udemy", "Education", (400, 900)),
    ("Coursera", "Education", (999, 2499)),
    ("Apollo Pharmacy", "Healthcare", (100, 600)),
    ("BSES Electricity", "Utilities", (900, 2200)),
    ("Netflix", "Entertainment", (199, 649)),
    ("PVR Cinemas", "Entertainment", (300, 900)),
    ("BigBasket", "Groceries", (400, 1600)),
    ("Blinkit", "Groceries", (150, 700)),
    ("Airtel", "Bills", (300, 800)),
]


def random_date_in_month(year: int, month: int) -> date:
    start = date(year, month, 1)
    next_month = date(year + (month == 12), (month % 12) + 1, 1)
    days_in_month = (next_month - start).days
    return start + timedelta(days=random.randint(0, days_in_month - 1))


def seed(months: list[tuple[int, int]], transactions_per_month: int = 18) -> int:
    init_db()
    count = 0
    for year, month in months:
        for _ in range(transactions_per_month):
            merchant, category, (low, high) = random.choice(SAMPLE_MERCHANTS)
            amount = round(random.uniform(low, high), 2)
            txn = Transaction(
                merchant_raw=merchant,
                merchant=merchant,
                amount=amount,
                currency="INR",
                transaction_date=random_date_in_month(year, month).isoformat(),
                category=category,
                source_file="sample_data",
                raw_text="Synthetic seed data — not from OCR.",
                extraction_confidence=1.0,
                confirmation_status=CONFIRMED,
            )
            repo.insert_transaction(txn)
            count += 1
    return count


def main() -> None:
    today = date.today()
    this_month = (today.year, today.month)
    last_month_date = today.replace(day=1) - timedelta(days=1)
    last_month = (last_month_date.year, last_month_date.month)
    two_months_ago_date = last_month_date.replace(day=1) - timedelta(days=1)
    two_months_ago = (two_months_ago_date.year, two_months_ago_date.month)

    total = seed([two_months_ago, last_month, this_month])
    print(f"Inserted {total} synthetic confirmed transactions across 3 months.")


if __name__ == "__main__":
    main()
