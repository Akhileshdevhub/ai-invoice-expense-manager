"""Transaction table: filter, edit, recategorize, delete confirmed transactions.

Edits made here go through the same repository functions the verification
screen uses, so analytics is always reading the latest state — there's no
separate "recalculate" step.
"""

import pandas as pd
import streamlit as st

from app.database import repository as repo
from app.models.transaction import VALID_CATEGORIES

EDITABLE_COLUMNS = ["transaction_date", "merchant", "category", "amount", "payment_method", "invoice_number"]


def render() -> None:
    st.header("Transactions")

    filters = _render_filters()
    transactions = repo.list_transactions(status="confirmed", **filters)

    if not transactions:
        st.info("No confirmed transactions match these filters.")
        return

    st.caption(f"{len(transactions)} transaction(s)")
    _render_editable_table(transactions)
    _render_delete_controls(transactions)


def _render_filters() -> dict:
    with st.expander("Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_from = st.date_input("From", value=None, format="YYYY-MM-DD")
            date_to = st.date_input("To", value=None, format="YYYY-MM-DD")
        with col2:
            category = st.selectbox("Category", ["All"] + VALID_CATEGORIES)
            merchant = st.text_input("Merchant contains")
        with col3:
            amount_min = st.number_input("Min amount", value=0.0, min_value=0.0, step=1.0)
            amount_max = st.number_input("Max amount", value=0.0, min_value=0.0, step=1.0)

    filters = {}
    if date_from:
        filters["date_from"] = date_from.isoformat()
    if date_to:
        filters["date_to"] = date_to.isoformat()
    if category != "All":
        filters["category"] = category
    if merchant:
        filters["merchant"] = merchant
    if amount_min > 0:
        filters["amount_min"] = amount_min
    if amount_max > 0:
        filters["amount_max"] = amount_max
    return filters


def _render_editable_table(transactions: list[dict]) -> None:
    df = pd.DataFrame(transactions)[["id"] + EDITABLE_COLUMNS]
    original = df.copy()

    edited = st.data_editor(
        df,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "transaction_date": st.column_config.TextColumn("Date"),
            "category": st.column_config.SelectboxColumn("Category", options=VALID_CATEGORIES),
            "amount": st.column_config.NumberColumn("Amount", min_value=0.0, format="%.2f"),
        },
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key="transactions_editor",
    )

    if st.button("Save Changes"):
        _save_changes(original, edited)


def _save_changes(original: pd.DataFrame, edited: pd.DataFrame) -> None:
    changed_count = 0
    for _, edited_row in edited.iterrows():
        original_row = original[original["id"] == edited_row["id"]].iloc[0]
        changed_fields = {
            col: edited_row[col]
            for col in EDITABLE_COLUMNS
            if edited_row[col] != original_row[col]
        }
        if changed_fields:
            repo.update_transaction(int(edited_row["id"]), changed_fields)
            changed_count += 1

    if changed_count:
        st.success(f"Updated {changed_count} transaction(s).")
        st.rerun()
    else:
        st.info("No changes to save.")


def _render_delete_controls(transactions: list[dict]) -> None:
    st.subheader("Delete Transactions")
    options = {
        f"#{t['id']} — {t['merchant']} — {t['amount']} — {t['transaction_date']}": t["id"]
        for t in transactions
    }
    selected_labels = st.multiselect("Select transactions to delete", list(options.keys()))
    if st.button("Delete Selected", type="secondary", disabled=not selected_labels):
        for label in selected_labels:
            repo.delete_transaction(options[label])
        st.success(f"Deleted {len(selected_labels)} transaction(s).")
        st.rerun()
