"""Ask a question in natural language (English or Hinglish).

See app/llm/query_engine.py for the actual flow: the parser and the
analytics module compute the real answer before any LLM is consulted.
This page just displays that, plus (for transparency) how the question
was interpreted.
"""

import streamlit as st

from app.database import repository as repo
from app.llm.factory import get_default_provider
from app.llm.query_engine import answer_query

EXAMPLE_QUESTIONS = [
    "Food pe kitna kharcha hua?",
    "Maine last month food pe kitna spend kiya?",
    "What was my biggest expense this month?",
    "Which merchant did I spend the most on?",
]


def render() -> None:
    st.header("Ask About Your Spending")

    provider = get_default_provider()
    if provider.is_available:
        st.caption("An LLM key is configured — answers may be reworded in natural language.")
    else:
        st.caption(
            "No LLM key configured. Questions are still answered — with template "
            "sentences built from your actual data (see .env.example)."
        )

    st.write("Try one of these, or type your own:")
    cols = st.columns(len(EXAMPLE_QUESTIONS))
    clicked_question = None
    for col, question in zip(cols, EXAMPLE_QUESTIONS):
        if col.button(question):
            clicked_question = question

    question = st.text_input("Your question", value=clicked_question or "")

    if st.button("Ask", type="primary") or clicked_question:
        if not question:
            st.warning("Type a question first.")
            return
        transactions = repo.list_transactions(status="confirmed")
        answer = answer_query(question, transactions, provider=provider)

        st.markdown(f"### {answer.final_answer}")
        with st.expander("How this was answered"):
            st.write(f"**Detected intent:** `{answer.intent.metric}`")
            st.write(f"**Category filter:** {answer.intent.category or 'none'}")
            st.write(f"**Date range:** {answer.intent.date_range}")
            st.write(f"**Computed value:** {answer.result_value}")
            st.write(f"**LLM used to reword:** {answer.used_llm}")
            if answer.used_llm:
                st.caption(f"Template answer before rewording: {answer.template_answer}")
