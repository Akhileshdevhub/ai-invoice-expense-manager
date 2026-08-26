# Limitations

Stated plainly, for anyone (including an interviewer) evaluating this
project honestly.

## OCR / extraction

- OCR accuracy depends heavily on photo quality; blurry, low-light, or
  heavily creased receipts produce noisier text and more extraction
  misses. No formal accuracy benchmark was run against a labeled test set
  of real receipts — none was available to use without a privacy
  concern, and the sample receipts used for development were synthetic.
  See `docs/OCR_PIPELINE.md` for concrete failure cases.
- Field extraction is regex/heuristic-based and only recognizes the
  label phrasings it's been given (`app/extraction/fields.py`). A total
  labeled in an unrecognized way falls back to "largest amount on the
  page," which is a guess, not a reliable extraction.
- Only the first page of a multi-page PDF is processed.
- Currency detection defaults to INR when no symbol/code is found — a
  reasonable default for this project's target market, not a general
  solution.
- Dates are parsed with a `dayfirst=True` assumption (DD/MM/YYYY) for
  ambiguous numeric dates, which matches Indian receipts but would
  misparse a US-style MM/DD/YYYY date with no other indicator.

## Merchant normalization

- The alias table (`app/normalization/merchant.py`) covers a small,
  deliberately short list of merchants observed during development —
  it is not, and isn't meant to be, a comprehensive merchant database.
  An unfamiliar merchant with an unusual legal-entity suffix may not
  normalize as cleanly as the ones in the alias table.
- Fuzzy matching against known merchants (`rapidfuzz`) uses a fixed
  similarity threshold (90). This is a manually chosen tradeoff between
  catching genuine near-duplicates and avoiding false merges of
  unrelated merchants with similar names — it hasn't been tuned against
  a labeled dataset of merchant-name pairs.

## Categorization

- The rule-based categorizer only knows the merchants and keywords in
  `app/classification/rules.py`. An unrecognized merchant with no
  matching keyword in the OCR text defaults to "Other."
- The ML classifier is trained on 240 synthetic, templated examples —
  see `docs/ML_PIPELINE.md` for why its high measured accuracy on that
  data doesn't imply similarly high accuracy on real, messy receipts for
  merchants outside its training vocabulary. It is shown only as a
  secondary suggestion for this reason.

## Natural-language queries

- The intent parser (`app/llm/query_parser.py`) recognizes a bounded set
  of English/Hinglish keywords. Questions phrased entirely outside that
  vocabulary fall back to a default interpretation (total spending, this
  month) rather than failing loudly — see `docs/LLM_ARCHITECTURE.md`.
- The optional LLM layer (`OpenAIProvider`) has not been exercised
  against a live API key in this environment — no key was available
  during development. Its code path is implemented against OpenAI's
  documented API shape and has unit-test coverage up to the provider
  boundary, but the actual network call has not been run.

## General

- This is a single-user, local-first prototype: there is no
  authentication, no multi-user support, and the SQLite database is a
  single file with no encryption at rest.
- No performance/load testing has been done. It has not been evaluated
  against more than a few dozen transactions or with concurrent users
  (Streamlit's single-process model isn't built for that; see Future
  Improvements).
- It is a portfolio/learning project demonstrating an OCR-to-analytics
  pipeline, not audited or validated financial software, and should not
  be used to make real accounting or tax decisions.

## Future improvements

Realistic next steps, not implemented here because they weren't
necessary to demonstrate the core pipeline honestly:

- A cloud OCR fallback (Google Document AI / AWS Textract) behind the
  same `run_ocr_with_confidence` interface, for harder documents.
- GST-specific field extraction (CGST/SGST/IGST line items individually,
  not just a single "tax" figure).
- Recurring-expense detection (e.g. flagging the same merchant + similar
  amount on a monthly cadence).
- Simple anomaly detection (a transaction well outside a category's
  usual range for this user).
- Budget alerts (a user-set monthly limit per category, with a dashboard
  warning when exceeded).
- Retraining the ML classifier on real confirmed-transaction history
  instead of synthetic data, once there's enough of it (see
  `docs/ML_PIPELINE.md`).
- Bank statement / email receipt ingestion as additional input sources
  alongside manual upload.
- Multi-user auth and per-user data isolation, if this ever became more
  than a single-user tool.
- Encrypting `data/app.db` at rest.
