"""Turn the metrics in metrics.py into short, specific sentences.

Every sentence produced here embeds a number that came from
app/analytics/metrics.py — nothing is phrased generically ("spending is
up") without the actual figure attached. If a comparison isn't possible
(e.g. no data for the previous month), that insight is simply not
generated rather than guessed at.
"""

from datetime import date

import pandas as pd

from app.analytics import metrics as m


def generate_insights(df: pd.DataFrame, as_of: date | None = None) -> list[str]:
    if df.empty:
        return ["No confirmed transactions yet — insights will appear once you confirm some receipts."]

    as_of = as_of or date.today()
    insights: list[str] = []

    insights += _month_over_month_insights(df, as_of)
    insights += _category_insights(df, as_of)
    insights += _merchant_concentration_insights(df, as_of)
    insights += _average_transaction_insight(df, as_of)

    return insights


def _current_and_previous_month_frames(df: pd.DataFrame, as_of: date):
    current_start = as_of.replace(day=1)
    prev_month_end = current_start - pd.Timedelta(days=1)
    prev_start = prev_month_end.replace(day=1)

    current_df = df[(df["transaction_date"] >= pd.Timestamp(current_start)) & (df["transaction_date"] <= pd.Timestamp(as_of))]
    prev_df = df[(df["transaction_date"] >= pd.Timestamp(prev_start)) & (df["transaction_date"] <= pd.Timestamp(prev_month_end))]
    return current_df, prev_df


def _month_over_month_insights(df: pd.DataFrame, as_of: date) -> list[str]:
    current_df, prev_df = _current_and_previous_month_frames(df, as_of)
    if current_df.empty or prev_df.empty:
        return []

    current_total = current_df["amount"].sum()
    prev_total = prev_df["amount"].sum()
    change = m.percentage_change(current_total, prev_total)
    if change is None:
        return []

    diff = round(current_total - prev_total, 2)
    direction = "more" if diff >= 0 else "less"
    sentences = [
        f"You spent ₹{abs(diff):,.0f} {direction} this month than last month "
        f"({change:+.1f}%)."
    ]

    # Category-level month-over-month, only for categories present in both months.
    current_cat = current_df.groupby("category")["amount"].sum()
    prev_cat = prev_df.groupby("category")["amount"].sum()
    for category in current_cat.index.intersection(prev_cat.index):
        cat_change = m.percentage_change(current_cat[category], prev_cat[category])
        if cat_change is not None and abs(cat_change) >= 15:
            trend = "increased" if cat_change > 0 else "decreased"
            sentences.append(
                f"{category} spending {trend} {abs(cat_change):.0f}% compared with last month."
            )
    return sentences


def _category_insights(df: pd.DataFrame, as_of: date) -> list[str]:
    current_df, _ = _current_and_previous_month_frames(df, as_of)
    if current_df.empty:
        return []
    breakdown = m.category_breakdown(current_df)
    if not breakdown:
        return []
    top = breakdown[0]
    return [
        f"Your largest category this month is {top['category']} at ₹{top['total']:,.0f} "
        f"({top['share_pct']}% of this month's spending)."
    ]


def _merchant_concentration_insights(df: pd.DataFrame, as_of: date) -> list[str]:
    current_df, _ = _current_and_previous_month_frames(df, as_of)
    if current_df.empty:
        return []
    breakdown = m.category_breakdown(current_df)
    if not breakdown:
        return []
    top_category = breakdown[0]["category"]
    merchants = m.merchant_breakdown(current_df, category=top_category, top_n=2)
    if len(merchants) < 2:
        return []
    category_total = sum(row["total"] for row in m.merchant_breakdown(current_df, category=top_category, top_n=1000))
    top_two_total = sum(row["total"] for row in merchants)
    if category_total == 0:
        return []
    share = round(top_two_total / category_total * 100, 0)
    if share < 40:
        return []
    names = " and ".join(row["merchant"] for row in merchants)
    return [f"{names} account for {share:.0f}% of your {top_category} spending this month."]


def _average_transaction_insight(df: pd.DataFrame, as_of: date) -> list[str]:
    current_df, _ = _current_and_previous_month_frames(df, as_of)
    if current_df.empty:
        return []
    avg = current_df["amount"].mean()
    return [f"Your average transaction this month is ₹{avg:,.0f}."]
