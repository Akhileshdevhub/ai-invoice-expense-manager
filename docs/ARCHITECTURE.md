# Architecture

## Why this shape

The product does one thing end to end: turn a photo/PDF of a receipt into a
row in a database the user can trust, then answer questions about that data.
Everything in `app/` mirrors a stage of that pipeline, so a new contributor
(or interviewer) can read the folder names and already know the data flow:

```
receipt file
    -> app/utils        (validate: type, size, not corrupted/empty)
    -> app/ocr           (preprocess image, run Tesseract, return raw text)
    -> app/extraction    (clean text, pull merchant/amount/date/etc via regex)
    -> app/normalization (collapse merchant name variants to one canonical name)
    -> app/classification (assign a category: rules first, optional ML fallback)
    -> [human verification in the UI, before anything is "confirmed"]
    -> app/database      (store as a Transaction row)
    -> app/analytics     (aggregate confirmed rows: totals, trends, insights)
    -> app/llm           (optional: turn a typed question into a query + answer)
    -> app/ui            (Streamlit pages that call the above)
```

No layer reaches backward. `analytics` never touches OCR; `ocr` never touches
the database. Each package is independently testable, which is why
`tests/` mirrors the same folder names.

## Module layout

```
app/
  ui/              Streamlit pages: upload, verify, dashboard, transactions, ask
  ocr/              file validation, image preprocessing, Tesseract wrapper
  extraction/       regex/heuristic field extraction + text cleaning
  normalization/     merchant name normalization
  classification/    rule-based category baseline + optional sklearn classifier
  analytics/         deterministic aggregation + insight generation (pandas)
  llm/               optional pluggable LLM layer, works with zero API keys
  database/          sqlite3 schema + repository functions (no ORM)
  models/            plain dataclasses shared across layers
  utils/             file validators, currency/date formatting

tests/               one test module per app/ package
data/                app.db (sqlite, gitignored), trained classifier artifact
sample_receipts/     synthetic receipt images used for demos/tests
scripts/             generate sample data, train the classifier
docs/                architecture + pipeline documentation
```

## Deliberate simplicity choices

- **No ORM.** `sqlite3` + hand-written SQL in `database/repository.py`. The
  schema is one table (plus a tiny category list); an ORM would add a
  dependency and an abstraction layer for no real benefit at this scale.
- **No microservices / API layer.** Streamlit calls the `app/` packages as
  plain Python functions in-process. There's one user, one process — a
  REST API would be architecture for a problem this project doesn't have.
- **Rule-based categorization is the default**, not the ML classifier. The
  training set is small and synthetic (see `docs/ML_PIPELINE.md`); a
  transparent keyword/merchant map that a user can predict and reason
  about is more trustworthy for a finance tool than a classifier trained
  on ~200 synthetic rows. The classifier exists, is evaluated honestly,
  and is documented as an optional experiment, not the primary path.
- **LLM is additive, never load-bearing.** Every numeric answer the app
  ever shows (dashboard totals, insights, or an answer to a typed
  question) comes from `app/analytics` running against the SQLite data.
  The LLM, when a key is configured, is only ever used to parse an
  ambiguous question into a structured intent or to reword an
  already-computed answer in natural language.

## Data flow: human verification gate

OCR and regex extraction are both imperfect. A wrong amount silently
entering "confirmed" spending data would make the whole dashboard
untrustworthy. So extraction never writes directly to the analytics-visible
part of the table: every upload creates a transaction with
`confirmation_status = "pending"`, the UI shows the extracted fields in an
editable form, and analytics/insight queries filter to
`confirmation_status = "confirmed"` only. This is the one architectural
decision in the project that exists purely because it's a *financial* tool,
not a generic OCR demo — see `docs/OCR_PIPELINE.md` for the failure cases
that make this necessary.

## Transaction schema

```
transactions
  id                  INTEGER PRIMARY KEY
  merchant_raw         TEXT     -- as read off the receipt
  merchant              TEXT     -- normalized/canonical name
  amount                 REAL
  currency                TEXT
  transaction_date        TEXT     -- ISO 8601 (YYYY-MM-DD)
  category                 TEXT
  invoice_number            TEXT NULL
  tax                        REAL NULL
  subtotal                    REAL NULL
  payment_method                TEXT NULL
  source_file                    TEXT     -- original filename
  raw_text                        TEXT     -- full OCR output, kept for debugging/re-extraction
  extraction_confidence              REAL     -- heuristic 0-1, see extraction docs
  confirmation_status                  TEXT     -- 'pending' | 'confirmed'
  created_at                              TEXT
  updated_at                                TEXT
```

Nullable fields are genuinely optional on real receipts (not every receipt
has a printed invoice number or itemized tax). `amount`, `currency`,
`transaction_date`, `category`, and `confirmation_status` are required —
the UI blocks "Confirm" until amount and date are present, since those two
fields are what analytics depends on.
