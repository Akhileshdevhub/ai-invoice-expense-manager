from datetime import date

from app.llm.query_engine import answer_query
from app.llm.providers.null_provider import NullProvider

TRANSACTIONS = [
    {"merchant": "Swiggy", "category": "Food", "amount": 450, "transaction_date": "2026-08-10", "confirmation_status": "confirmed"},
    {"merchant": "Zomato", "category": "Food", "amount": 320, "transaction_date": "2026-08-12", "confirmation_status": "confirmed"},
    {"merchant": "Uber", "category": "Travel", "amount": 280, "transaction_date": "2026-08-15", "confirmation_status": "confirmed"},
    {"merchant": "Swiggy", "category": "Food", "amount": 200, "transaction_date": "2026-07-20", "confirmation_status": "confirmed"},
]


def test_category_total_matches_hand_calculated_sum():
    answer = answer_query("Food pe kitna kharcha hua?", TRANSACTIONS, as_of=date(2026, 8, 20))
    assert answer.result_value == 770  # 450 + 320, August only
    assert "770" in answer.template_answer


def test_last_month_category_total():
    answer = answer_query("Maine last month food pe kitna spend kiya?", TRANSACTIONS, as_of=date(2026, 8, 20))
    assert answer.result_value == 200


def test_top_merchant_query():
    answer = answer_query("Which merchant did I spend the most on?", TRANSACTIONS, as_of=date(2026, 8, 20))
    assert answer.result_value["merchant"] == "Swiggy"
    assert answer.result_value["total"] == 450


def test_null_provider_means_template_answer_is_final_answer():
    answer = answer_query("Food pe kitna kharcha hua?", TRANSACTIONS, provider=NullProvider(), as_of=date(2026, 8, 20))
    assert answer.used_llm is False
    assert answer.final_answer == answer.template_answer


def test_no_transactions_returns_zero_not_error():
    answer = answer_query("How much did I spend this month?", [], as_of=date(2026, 8, 20))
    assert answer.result_value == 0.0
