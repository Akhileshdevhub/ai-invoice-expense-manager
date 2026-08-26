"""Deterministic aggregation over confirmed transactions.

Every function here takes a pandas DataFrame (already filtered to
confirmation_status='confirmed' by the caller) and returns numbers
computed directly from it — no LLM, no estimation. This module is what
the dashboard, the insights generator, and the natural-language query
engine all call for their actual numbers; see docs/LLM_ARCHITECTURE.md
for why that separation matters.
"""

import pandas as pd


def transactions_to_dataframe(transactions: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(transactions)
    if df.empty:
        return df
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


def overview_stats(df: pd.DataFrame) -> dict:
    """Total spend, transaction count, average, and largest single expense."""
    if df.empty:
        return {"total_spending": 0.0, "transaction_count": 0, "average_transaction": 0.0, "largest_expense": None}

    largest = df.loc[df["amount"].idxmax()]
    return {
        "total_spending": round(df["amount"].sum(), 2),
        "transaction_count": len(df),
        "average_transaction": round(df["amount"].mean(), 2),
        "largest_expense": {
            "merchant": largest["merchant"],
            "amount": round(largest["amount"], 2),
            "date": largest["transaction_date"].date().isoformat(),
        },
    }


def category_breakdown(df: pd.DataFrame) -> list[dict]:
    """Total spend per category, sorted highest first."""
    if df.empty:
        return []
    grouped = (
        df.groupby("category")["amount"]
        .agg(total="sum", count="count")
        .sort_values("total", ascending=False)
        .reset_index()
    )
    total_spend = df["amount"].sum()
    grouped["share_pct"] = (grouped["total"] / total_spend * 100).round(1)
    return grouped.round({"total": 2}).to_dict(orient="records")


def merchant_breakdown(df: pd.DataFrame, category: str | None = None, top_n: int = 10) -> list[dict]:
    """Total spend per merchant, optionally scoped to one category."""
    scoped = df if category is None else df[df["category"] == category]
    if scoped.empty:
        return []
    grouped = (
        scoped.groupby("merchant")["amount"]
        .agg(total="sum", count="count")
        .sort_values("total", ascending=False)
        .head(top_n)
        .reset_index()
    )
    return grouped.round({"total": 2}).to_dict(orient="records")


def monthly_spending(df: pd.DataFrame) -> list[dict]:
    """Total spend per calendar month, chronological."""
    if df.empty:
        return []
    monthly = df.copy()
    monthly["month"] = monthly["transaction_date"].dt.to_period("M").astype(str)
    grouped = monthly.groupby("month")["amount"].sum().sort_index().reset_index()
    return grouped.round({"amount": 2}).to_dict(orient="records")


def weekly_spending(df: pd.DataFrame) -> list[dict]:
    """Total spend per ISO week, chronological."""
    if df.empty:
        return []
    weekly = df.copy()
    weekly["week"] = weekly["transaction_date"].dt.to_period("W").astype(str)
    grouped = weekly.groupby("week")["amount"].sum().sort_index().reset_index()
    return grouped.round({"amount": 2}).to_dict(orient="records")


def spending_for_period(df: pd.DataFrame, start, end, category: str | None = None) -> float:
    """Total spend within [start, end] (inclusive), optionally scoped to a category.

    The building block behind both the dashboard's "This Month" figure and
    the natural-language query engine's date-range questions.
    """
    if df.empty:
        return 0.0
    mask = (df["transaction_date"] >= pd.Timestamp(start)) & (df["transaction_date"] <= pd.Timestamp(end))
    scoped = df[mask]
    if category:
        scoped = scoped[scoped["category"] == category]
    return round(scoped["amount"].sum(), 2)


def percentage_change(current: float, previous: float) -> float | None:
    """Percentage change from previous to current. None when previous is 0 (undefined, not infinite)."""
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)
