"""Execute a QueryIntent against the database and produce an answer.

Flow: intent (from query_parser) -> pandas query (app/analytics) -> a
template sentence built from the real number -> optionally handed to an
LLM provider to reword. Steps 1-3 always happen and never involve an LLM;
step 4 is skipped entirely when no provider is available (NullProvider).

This ordering is the whole point of the LLM layer being "optional": the
correct numeric answer exists before any LLM is ever consulted.
"""

import calendar
from dataclasses import dataclass
from datetime import date

import pandas as pd

from app.analytics import metrics as m
from app.llm.providers.null_provider import NullProvider
from app.llm.query_parser import QueryIntent, parse_query


@dataclass
class QueryAnswer:
    intent: QueryIntent
    result_value: object
    template_answer: str
    final_answer: str
    used_llm: bool


def resolve_date_range(date_range: str, as_of: date, df: pd.DataFrame) -> tuple[date, date, str]:
    """Return (start, end, label) for a date_range code."""
    if date_range == "this_month":
        start = as_of.replace(day=1)
        return start, as_of, "this month"

    if date_range == "last_month":
        first_of_this_month = as_of.replace(day=1)
        last_month_end = first_of_this_month - pd.Timedelta(days=1)
        last_month_end = last_month_end if isinstance(last_month_end, date) else last_month_end.date()
        start = last_month_end.replace(day=1)
        return start, last_month_end, "last month"

    if date_range == "this_week":
        start = as_of - pd.Timedelta(days=as_of.weekday())
        return start, as_of, "this week"

    if date_range == "all_time":
        if df.empty:
            return as_of, as_of, "all time"
        return df["transaction_date"].min().date(), df["transaction_date"].max().date(), "all time"

    if date_range.startswith("month:"):
        month = int(date_range.split(":")[1])
        year = as_of.year if month <= as_of.month else as_of.year - 1
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        return start, end, f"{calendar.month_name[month]} {year}"

    return as_of.replace(day=1), as_of, "this month"


def answer_query(question: str, transactions: list[dict], provider=None, as_of: date | None = None) -> QueryAnswer:
    provider = provider or NullProvider()
    as_of = as_of or date.today()
    intent = parse_query(question)
    df = m.transactions_to_dataframe(transactions)

    start, end, period_label = resolve_date_range(intent.date_range, as_of, df)
    result_value, template_answer = _execute_intent(intent, df, start, end, period_label)

    final_answer = template_answer
    used_llm = False
    if provider.is_available:
        try:
            final_answer = _reword_with_llm(provider, question, template_answer)
            used_llm = True
        except Exception:
            # An LLM/network failure should never break the answer the
            # user already has — fall back to the template sentence.
            final_answer = template_answer
            used_llm = False

    return QueryAnswer(
        intent=intent,
        result_value=result_value,
        template_answer=template_answer,
        final_answer=final_answer,
        used_llm=used_llm,
    )


def _execute_intent(intent: QueryIntent, df: pd.DataFrame, start: date, end: date, period_label: str):
    if intent.metric == "category_total":
        total = m.spending_for_period(df, start, end, category=intent.category)
        return total, f"You spent ₹{total:,.0f} on {intent.category} {period_label}."

    if intent.metric == "total_spending":
        total = m.spending_for_period(df, start, end)
        return total, f"You spent ₹{total:,.0f} in total {period_label}."

    scoped = df[(df["transaction_date"] >= pd.Timestamp(start)) & (df["transaction_date"] <= pd.Timestamp(end))] if not df.empty else df

    if intent.metric == "biggest_expense":
        if scoped.empty:
            return None, f"There are no confirmed transactions {period_label}."
        stats = m.overview_stats(scoped)
        largest = stats["largest_expense"]
        return largest, f"Your biggest expense {period_label} was ₹{largest['amount']:,.0f} at {largest['merchant']}."

    if intent.metric == "average_transaction":
        if scoped.empty:
            return None, f"There are no confirmed transactions {period_label}."
        stats = m.overview_stats(scoped)
        return stats["average_transaction"], f"Your average transaction {period_label} is ₹{stats['average_transaction']:,.0f}."

    if intent.metric == "transaction_count":
        count = len(scoped)
        return count, f"You made {count} transaction(s) {period_label}."

    if intent.metric == "top_merchant":
        merchants = m.merchant_breakdown(scoped, top_n=1)
        if not merchants:
            return None, f"There are no confirmed transactions {period_label}."
        top = merchants[0]
        return top, f"You spent the most on {top['merchant']} {period_label}, totalling ₹{top['total']:,.0f}."

    total = m.spending_for_period(df, start, end)
    return total, f"You spent ₹{total:,.0f} {period_label}."


def _reword_with_llm(provider, question: str, template_answer: str) -> str:
    """Ask the LLM to phrase the already-computed answer naturally — never to compute it.

    The prompt explicitly hands over the number as a fact, not a question,
    so the model has nothing left to calculate or hallucinate.
    """
    prompt = (
        "Rephrase the following factual answer in one short, natural sentence "
        "that directly addresses the user's question. Do not add, remove, or "
        "change any numbers or facts. If the user wrote in Hindi/Hinglish, "
        "you may reply in the same style.\n\n"
        f"User's question: {question}\n"
        f"Factual answer (do not alter the numbers): {template_answer}\n\n"
        "Reworded answer:"
    )
    return provider.complete(prompt).strip()
