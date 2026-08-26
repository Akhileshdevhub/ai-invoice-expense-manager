"""Turn a typed question into a structured query intent.

This is rule-based, not an LLM call — every example in the product brief
("Maine last month food pe kitna spend kiya?", "August mein travel
expenses kitne the?") is answerable by matching a small set of keywords
for metric / category / date range. Keeping this deterministic means the
app works with zero API keys and means a wrong parse is debuggable
(which keyword matched) instead of an opaque model decision.

If an LLM key is configured, query_engine.py can still use the LLM layer
to *reword* the final answer — but the number and the intent behind it
always come from this parser + app/analytics, never from the LLM. See
docs/LLM_ARCHITECTURE.md.
"""

import re
from dataclasses import dataclass
from typing import Optional

CATEGORY_KEYWORDS = {
    "food": "Food", "khana": "Food", "khane": "Food",
    "travel": "Travel", "safar": "Travel", "yatra": "Travel", "cab": "Travel",
    "shopping": "Shopping", "kharidari": "Shopping",
    "software": "Software", "subscription": "Software",
    "education": "Education", "padhai": "Education", "course": "Education",
    "healthcare": "Healthcare", "medical": "Healthcare", "dawai": "Healthcare",
    "utilities": "Utilities", "bijli": "Utilities", "electricity": "Utilities",
    "entertainment": "Entertainment", "movie": "Entertainment",
    "rent": "Rent", "kiraya": "Rent",
    "bills": "Bills", "bill": "Bills", "recharge": "Bills",
    "groceries": "Groceries", "grocery": "Groceries", "kirana": "Groceries",
}

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

TOP_MERCHANT_PATTERNS = [r"which merchant", r"kis (?:merchant|dukaan|jagah)", r"spent the most on"]
BIGGEST_EXPENSE_PATTERNS = [r"biggest expense", r"largest expense", r"sabse (?:bada|zyada) kharch"]
AVERAGE_PATTERNS = [r"average", r"ausat", r"per transaction"]
COUNT_PATTERNS = [r"how many transactions", r"kitne transactions", r"number of transactions"]

LAST_MONTH_PATTERNS = [r"last month", r"pichl?e\s*mahine", r"pichl?e\s*month"]
THIS_WEEK_PATTERNS = [r"this week", r"is\s*hafte", r"is\s*week"]
ALL_TIME_PATTERNS = [r"overall", r"all time", r"total ever", r"kul milaakar"]


@dataclass
class QueryIntent:
    metric: str  # 'total_spending' | 'category_total' | 'top_merchant' | 'biggest_expense' | 'average_transaction' | 'transaction_count'
    category: Optional[str] = None
    date_range: str = "this_month"  # 'this_month' | 'last_month' | 'this_week' | 'all_time' | 'month:<1-12>'
    unparsed_question: str = ""


def parse_query(question: str) -> QueryIntent:
    lowered = question.lower().strip()

    category = _match_category(lowered)
    date_range = _match_date_range(lowered)
    metric = _match_metric(lowered, category)

    return QueryIntent(
        metric=metric,
        category=category,
        date_range=date_range,
        unparsed_question=question,
    )


def _match_category(text: str) -> Optional[str]:
    for keyword, category in CATEGORY_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            return category
    return None


def _match_date_range(text: str) -> str:
    for pattern in LAST_MONTH_PATTERNS:
        if re.search(pattern, text):
            return "last_month"
    for pattern in THIS_WEEK_PATTERNS:
        if re.search(pattern, text):
            return "this_week"
    for pattern in ALL_TIME_PATTERNS:
        if re.search(pattern, text):
            return "all_time"
    for name, number in MONTH_NAMES.items():
        if re.search(rf"\b{name}\b", text):
            return f"month:{number}"
    # No explicit date phrase: assume the user means the current month,
    # which is the most common intent behind an unscoped spending question.
    return "this_month"


def _match_metric(text: str, category: Optional[str]) -> str:
    if any(re.search(p, text) for p in TOP_MERCHANT_PATTERNS):
        return "top_merchant"
    if any(re.search(p, text) for p in BIGGEST_EXPENSE_PATTERNS):
        return "biggest_expense"
    if any(re.search(p, text) for p in AVERAGE_PATTERNS):
        return "average_transaction"
    if any(re.search(p, text) for p in COUNT_PATTERNS):
        return "transaction_count"
    if category:
        return "category_total"
    return "total_spending"
