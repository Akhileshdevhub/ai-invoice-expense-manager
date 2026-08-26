from app.llm.query_parser import parse_query


def test_parses_food_last_month_query():
    intent = parse_query("Maine last month food pe kitna spend kiya?")
    assert intent.category == "Food"
    assert intent.date_range == "last_month"
    assert intent.metric == "category_total"


def test_parses_unscoped_food_query_defaults_to_this_month():
    intent = parse_query("Food pe kitna kharcha hua?")
    assert intent.category == "Food"
    assert intent.date_range == "this_month"


def test_parses_named_month_travel_query():
    intent = parse_query("August mein travel expenses kitne the?")
    assert intent.category == "Travel"
    assert intent.date_range == "month:8"


def test_parses_top_merchant_query():
    intent = parse_query("Which merchant did I spend the most on?")
    assert intent.metric == "top_merchant"


def test_parses_biggest_expense_this_month_query():
    intent = parse_query("What was my biggest expense this month?")
    assert intent.metric == "biggest_expense"
    assert intent.date_range == "this_month"


def test_parses_average_transaction_query():
    intent = parse_query("What is my average transaction value?")
    assert intent.metric == "average_transaction"


def test_defaults_to_total_spending_when_no_category_mentioned():
    intent = parse_query("How much did I spend this week?")
    assert intent.metric == "total_spending"
    assert intent.date_range == "this_week"
