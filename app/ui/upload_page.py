"""Upload -> OCR -> extraction -> human verification -> confirm.

This page is the one place in the app where a receipt becomes a
transaction. It deliberately never writes a "confirmed" row itself —
every extraction lands as 'pending' and only the user's explicit
"Confirm Transaction" click (after reviewing/editing the fields) marks
it confirmed. See docs/ARCHITECTURE.md for why that gate exists.
"""

import hashlib

import streamlit as st

from app.classification.categorize import categorize
from app.database import repository as repo
from app.extraction.cleaning import clean_ocr_text
from app.extraction.fields import extract_fields
from app.models.transaction import Transaction, VALID_CATEGORIES
from app.normalization.merchant import normalize_merchant
from app.ocr.pipeline import process_upload
from app.utils.formatting import format_amount


def render() -> None:
    st.header("Upload a Receipt or Invoice")
    st.caption("Supported formats: PDF, JPG, PNG. Files are processed locally with Tesseract OCR.")

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "jpg", "jpeg", "png"])
    if uploaded_file is not None:
        _handle_upload(uploaded_file)

    _render_pending_verification_queue()


def _handle_upload(uploaded_file) -> None:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Streamlit re-runs the whole script on every interaction; without this
    # guard, re-checking a checkbox elsewhere would re-run OCR on the same
    # file and insert a duplicate pending transaction.
    if st.session_state.get("last_processed_hash") == file_hash:
        return

    with st.spinner("Running OCR and extracting fields..."):
        ocr_result = process_upload(uploaded_file.name, file_bytes)

    if not ocr_result.success:
        st.error(ocr_result.error)
        return

    cleaned_text = clean_ocr_text(ocr_result.raw_text)
    fields = extract_fields(cleaned_text)
    known_merchants = repo.get_distinct_merchants()
    merchant = normalize_merchant(fields.merchant_raw, known_merchants=known_merchants)
    category_result = categorize(merchant, cleaned_text)

    txn = Transaction(
        merchant_raw=fields.merchant_raw or "Unknown",
        merchant=merchant,
        amount=fields.amount,
        currency=fields.currency,
        transaction_date=fields.transaction_date,
        category=category_result.category,
        invoice_number=fields.invoice_number,
        tax=fields.tax,
        subtotal=fields.subtotal,
        payment_method=fields.payment_method,
        source_file=uploaded_file.name,
        raw_text=ocr_result.raw_text,
        extraction_confidence=fields.confidence,
    )
    txn_id = repo.insert_transaction(txn)
    st.session_state["last_processed_hash"] = file_hash

    st.success("Extraction complete — review the details below before confirming.")
    if category_result.ml_suggestion and category_result.ml_suggestion != category_result.category:
        st.caption(
            f"ML classifier suggestion: {category_result.ml_suggestion} "
            f"({category_result.ml_confidence:.0%} confidence) — shown for comparison only, "
            f"the rule-based category above was used."
        )
    st.session_state["highlight_txn_id"] = txn_id


def _render_pending_verification_queue() -> None:
    pending = repo.list_transactions(status="pending")
    if not pending:
        return

    st.subheader(f"Pending Verification ({len(pending)})")
    st.caption("Nothing here counts toward your dashboard or analytics until you confirm it.")

    for txn in pending:
        expanded = txn["id"] == st.session_state.get("highlight_txn_id")
        with st.expander(
            f"{txn['merchant']} — {format_amount(txn['amount'], txn['currency'])} "
            f"({txn['source_file']})",
            expanded=expanded,
        ):
            _render_verification_form(txn)


def _render_verification_form(txn: dict) -> None:
    if txn["extraction_confidence"] < 0.6:
        st.warning(
            f"Low extraction confidence ({txn['extraction_confidence']:.0%}). "
            "Please double-check every field below."
        )
    if txn["amount"] is None:
        st.warning("Amount could not be reliably extracted — please enter it manually.")

    with st.form(key=f"verify_form_{txn['id']}"):
        col1, col2 = st.columns(2)
        with col1:
            merchant = st.text_input("Merchant", value=txn["merchant"])
            amount = st.number_input(
                "Amount", value=float(txn["amount"] or 0.0), min_value=0.0, step=1.0
            )
            currency = st.selectbox(
                "Currency", ["INR", "USD", "EUR", "GBP"],
                index=["INR", "USD", "EUR", "GBP"].index(txn["currency"]) if txn["currency"] in ["INR", "USD", "EUR", "GBP"] else 0,
            )
            category = st.selectbox(
                "Category", VALID_CATEGORIES,
                index=VALID_CATEGORIES.index(txn["category"]) if txn["category"] in VALID_CATEGORIES else VALID_CATEGORIES.index("Other"),
            )
        with col2:
            transaction_date = st.text_input(
                "Date (YYYY-MM-DD)", value=txn["transaction_date"] or ""
            )
            invoice_number = st.text_input("Invoice / Receipt Number", value=txn["invoice_number"] or "")
            tax = st.number_input("Tax", value=float(txn["tax"] or 0.0), min_value=0.0, step=1.0)
            payment_method = st.text_input("Payment Method", value=txn["payment_method"] or "")

        # Not st.expander here — this form already renders inside the
        # "Pending Verification" expander, and Streamlit doesn't allow
        # nested expanders.
        if st.checkbox("Show raw OCR text (for debugging)", key=f"show_raw_{txn['id']}"):
            st.text(txn["raw_text"])

        confirm_col, discard_col = st.columns([1, 1])
        confirmed = confirm_col.form_submit_button("Confirm Transaction", type="primary")
        discarded = discard_col.form_submit_button("Discard")

        if confirmed:
            if not transaction_date:
                st.error("Date is required before confirming.")
            elif amount <= 0:
                st.error("Amount must be greater than zero before confirming.")
            else:
                repo.confirm_transaction(txn["id"], {
                    "merchant": merchant,
                    "amount": amount,
                    "currency": currency,
                    "category": category,
                    "transaction_date": transaction_date,
                    "invoice_number": invoice_number or None,
                    "tax": tax or None,
                    "payment_method": payment_method or None,
                })
                st.success("Transaction confirmed and added to your dashboard.")
                st.rerun()

        if discarded:
            repo.delete_transaction(txn["id"])
            st.info("Discarded.")
            st.rerun()
