from datetime import date

from app.analytics import metrics as m
from app.analytics.insights import generate_insights

SAMPLE_TRANSACTIONS = [
    {"merchant": "Swiggy", "category": "Food", "amount": 100, "transaction_date": "2026-08-01", "confirmation_status": "confirmed"},
    {"merchant": "Zomato", "category": "Food", "amount": 200, "transaction_date": "2026-08-05", "confirmation_status": "confirmed"},
    {"merchant": "Uber", "category": "Travel", "amount": 300, "transaction_date": "2026-08-10", "confirmation_status": "confirmed"},
]


def test_overview_stats_matches_hand_calculated_totals():
    df = m.transactions_to_dataframe(SAMPLE_TRANSACTIONS)
    stats = m.overview_stats(df)
    assert stats["total_spending"] == 600
    assert stats["transaction_count"] == 3
    assert stats["average_transaction"] == 200
    assert stats["largest_expense"]["merchant"] == "Uber"


def test_category_breakdown_totals_are_correct():
    df = m.transactions_to_dataframe(SAMPLE_TRANSACTIONS)
    breakdown = {row["category"]: row["total"] for row in m.category_breakdown(df)}
    assert breakdown["Food"] == 300
    assert breakdown["Travel"] == 300


def test_overview_stats_on_empty_dataframe_does_not_crash():
    df = m.transactions_to_dataframe([])
    stats = m.overview_stats(df)
    assert stats["total_spending"] == 0.0
    assert stats["transaction_count"] == 0
    assert stats["largest_expense"] is None


def test_percentage_change_basic_case():
    assert m.percentage_change(current=150, previous=100) == 50.0
    assert m.percentage_change(current=80, previous=100) == -20.0


def test_percentage_change_undefined_when_previous_is_zero():
    assert m.percentage_change(current=100, previous=0) is None


def test_spending_for_period_filters_by_date_range():
    df = m.transactions_to_dataframe(SAMPLE_TRANSACTIONS)
    total = m.spending_for_period(df, date(2026, 8, 1), date(2026, 8, 6))
    assert total == 300  # Swiggy + Zomato, Uber falls outside the range


def test_spending_for_period_filters_by_category():
    df = m.transactions_to_dataframe(SAMPLE_TRANSACTIONS)
    total = m.spending_for_period(df, date(2026, 8, 1), date(2026, 8, 31), category="Food")
    assert total == 300


def test_generate_insights_on_empty_data_does_not_crash():
    df = m.transactions_to_dataframe([])
    insights = generate_insights(df)
    assert len(insights) == 1
    assert "No confirmed transactions" in insights[0]


def test_generate_insights_produces_month_over_month_sentence():
    transactions = SAMPLE_TRANSACTIONS + [
        {"merchant": "Swiggy", "category": "Food", "amount": 100, "transaction_date": "2026-07-01", "confirmation_status": "confirmed"},
    ]
    df = m.transactions_to_dataframe(transactions)
    insights = generate_insights(df, as_of=date(2026, 8, 15))
    assert any("more this month than last month" in s or "less this month than last month" in s for s in insights)
