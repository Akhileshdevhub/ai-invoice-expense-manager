"""Small display-formatting helpers shared by the Streamlit pages."""

from datetime import date, datetime

CURRENCY_SYMBOLS = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}


def format_amount(amount: float | None, currency: str = "INR") -> str:
    if amount is None:
        return "—"
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def format_date_friendly(iso_date: str | None) -> str:
    if not iso_date:
        return "—"
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return iso_date
    return parsed.strftime("%d %b %Y")
