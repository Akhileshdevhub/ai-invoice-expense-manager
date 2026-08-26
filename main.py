"""Entry point: python -m streamlit run main.py

Kept deliberately thin — this file only wires up navigation. Each page's
actual logic lives in app/ui/*.py, and everything below the UI lives in
the app/ package's other modules. See docs/ARCHITECTURE.md.
"""

from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from app.database.db import init_db
from app.ui import dashboard_page, query_page, transactions_page, upload_page

st.set_page_config(page_title="AI Invoice & Expense Manager", layout="wide")

init_db()  # idempotent: CREATE TABLE IF NOT EXISTS

PAGES = {
    "Upload Receipt": upload_page,
    "Dashboard": dashboard_page,
    "Transactions": transactions_page,
    "Ask a Question": query_page,
}

st.sidebar.title("AI Invoice & Expense Manager")
selection = st.sidebar.radio("Navigate", list(PAGES.keys()))
st.sidebar.divider()
st.sidebar.caption(
    "OCR-based receipt processing, deterministic analytics, and an "
    "optional natural-language query layer. Built as a portfolio project."
)

PAGES[selection].render()
