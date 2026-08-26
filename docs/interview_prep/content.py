# -*- coding: utf-8 -*-
"""Content for the Interview Preparation Guide PDF.

Kept as plain Python data (not hardcoded into the PDF-building script) so
the guide's content can be reviewed/edited independently of the
reportlab layout code in build_guide.py.

Scope note: the product brief asked for 20 questions across 11
categories (220 total). This file deliberately ships fewer, curated
questions per category (~90 total) at full depth (short answer, detailed
answer, how to say it out loud, likely follow-up) instead. A 220-question
bank nobody can actually study beats a shorter one that gets read and
remembered — this project's own principle (README, "Engineering quality
over number of features") applied to its own interview guide.
"""

PITCH_30S = (
    "It's an AI Invoice and Expense Manager — you upload a photo or PDF of a "
    "receipt, it runs OCR with Tesseract, pulls out the merchant, amount, date "
    "and a few other fields with regex-based extraction, normalizes the "
    "merchant name, and suggests a category. Nothing gets saved as real data "
    "until I review and confirm it on a verification screen — that gate is "
    "the one decision I'd defend hardest, because OCR is never perfect and a "
    "financial dashboard built on unverified numbers isn't trustworthy. "
    "Confirmed transactions feed a dashboard with deterministic analytics "
    "— monthly totals, category breakdowns, insight sentences — and there's "
    "an optional natural-language query layer that works with or without an "
    "LLM key, because the actual numbers always come from a database query, "
    "never from the model."
)

PITCH_2MIN = (
    "The problem I was solving is that tracking expenses from paper or PDF "
    "receipts is tedious enough that most people just don't do it, and most "
    "OCR-based tools I looked at treat extraction as a black box — you get a "
    "number with no way to tell if it's confident or a guess.\n\n"
    "So the pipeline is: you upload a receipt, it goes through file "
    "validation, then Tesseract OCR with some OpenCV preprocessing — "
    "grayscale, upscaling small images, denoising, adaptive thresholding — "
    "because phone photos of receipts are noisy and unevenly lit. The raw "
    "OCR text then goes through a regex-based extraction layer that pulls "
    "out merchant, amount, date, currency, invoice number, tax, and payment "
    "method. For amount specifically, I prioritize a clearly labeled total "
    "over just grabbing the biggest number on the page, and I track whether "
    "the amount came from a real label or a fallback guess.\n\n"
    "That extracted data never goes straight into the database as "
    "confirmed. It shows up on a verification screen where every field is "
    "editable, and only an explicit 'Confirm Transaction' click marks it "
    "confirmed — analytics only ever reads confirmed rows. That's the one "
    "architectural decision in the whole project that exists specifically "
    "because this is a financial tool, not a generic OCR demo.\n\n"
    "For categorization, the default is a transparent rule-based lookup "
    "— known merchants map directly, otherwise keywords in the OCR text "
    "map to a category. I also built an ML classifier — TF-IDF plus "
    "logistic regression trained on a small synthetic dataset — but it's "
    "shown as a secondary suggestion, not the default, because I can "
    "defend exactly why a rule fired but a logistic regression's decision "
    "is a lot harder for a user to reason about, and the dataset is "
    "synthetic and small enough that I don't want to overstate what its "
    "accuracy numbers actually prove.\n\n"
    "Analytics is plain pandas aggregation over confirmed transactions — "
    "monthly and weekly totals, category breakdowns, percentage changes, "
    "and a handful of insight sentences that are always built from an "
    "actual computed number, never phrased generically.\n\n"
    "And then there's an optional natural-language query feature — you can "
    "type something like 'Food pe kitna kharcha hua?' and it'll answer "
    "with a real number. The intent parsing is rule-based keyword "
    "matching, not an LLM call, specifically so the feature works with "
    "zero API keys. If you do configure an OpenAI key, it's only ever used "
    "to reword the answer I've already computed — the prompt literally "
    "tells it not to change the numbers, and if the call fails for any "
    "reason it just falls back to the template sentence. The whole point "
    "was that the LLM is additive, never load-bearing."
)

ARCHITECTURE_TEXT = (
    "The codebase is organized as one package per pipeline stage: "
    "app/ocr, app/extraction, app/normalization, app/classification, "
    "app/analytics, app/llm, app/database, app/models, app/utils, and "
    "app/ui. Each package only depends on the ones before it in the "
    "pipeline — analytics never imports from ocr, ocr never imports from "
    "the database. That's not a rule I imposed for its own sake; it falls "
    "out naturally from the fact that a receipt genuinely flows through "
    "these stages in one direction, and it's what makes each package "
    "independently testable (tests/ mirrors the same folder names).\n\n"
    "There's no ORM — app/database/repository.py is plain sqlite3 and "
    "hand-written SQL over one table. There's no REST API layer — the "
    "Streamlit pages call the app/ packages as normal Python function "
    "calls in the same process. Both of those are conscious decisions to "
    "not build architecture for problems this project doesn't have: one "
    "user, one process, one table that actually matters."
)

DATA_FLOW_TEXT = (
    "receipt file -> app/utils/validators.py (type/size/corruption check) "
    "-> app/ocr/pipeline.py (load the file, PDF or image) -> "
    "app/ocr/preprocess.py (grayscale, upscale, denoise, adaptive "
    "threshold) -> app/ocr/engine.py (pytesseract, returns raw text + "
    "mean word confidence) -> app/extraction/cleaning.py (light "
    "whitespace/line cleanup) -> app/extraction/fields.py (regex "
    "extraction: merchant, amount, date, currency, invoice number, tax, "
    "subtotal, payment method, plus a heuristic confidence score) -> "
    "app/normalization/merchant.py (strip corporate suffixes, alias "
    "table, fuzzy-match against known merchants) -> "
    "app/classification/categorize.py (rule-based category + optional ML "
    "suggestion) -> inserted into SQLite with confirmation_status="
    "'pending' -> shown on the verification screen (app/ui/upload_page.py) "
    "-> user edits/confirms -> app/database/repository.py marks it "
    "confirmed -> app/analytics/metrics.py and insights.py compute "
    "everything the dashboard and the query engine show, reading only "
    "confirmed rows."
)

CONCEPTS = {
    "OCR": (
        "Optical Character Recognition (OCR) is the process of turning an "
        "image of text into machine-readable text. I use Tesseract, an "
        "open-source OCR engine, through the pytesseract wrapper. Before "
        "OCR runs, I preprocess the image with OpenCV: convert to "
        "grayscale (color carries no text signal), upscale if the image "
        "is smaller than 1000px on its longest side (Tesseract's LSTM "
        "models expect roughly scan-quality resolution), denoise with "
        "fastNlMeansDenoising (phone-camera sensor grain can look like "
        "extra character strokes), and apply adaptive thresholding to "
        "binarize the image using a locally-computed threshold rather "
        "than one global cutoff — that matters because a receipt photo "
        "often has uneven lighting, like a shadow across half the paper. "
        "I run Tesseract with --psm 6 ('assume a single uniform block of "
        "text') instead of the default --psm 3, because receipts are a "
        "dense narrow column of text, not a page with a detectable "
        "layout. Known OCR failure cases in this project: blurry/low-"
        "light photos, handwritten receipts (Tesseract's models are "
        "trained on printed text), non-standard layouts where labels "
        "don't match what my extraction regexes expect, and multi-page "
        "PDFs (I only process the first page)."
    ),
    "NLP": (
        "The 'NLP' in this project is intentionally narrow and rule-"
        "based, not a trained language model, and I'd say that "
        "explicitly in an interview rather than oversell it. Two places "
        "use it: field extraction (regex patterns matching labels like "
        "'Grand Total' or 'GST' in cleaned OCR text) and the "
        "natural-language query parser (keyword/regex matching for "
        "metric words, category words in English and Hinglish, and date-"
        "range phrases like 'last month' or 'pichle mahine'). There's no "
        "tokenization, embeddings, or a trained NLP model anywhere in "
        "this codebase — I chose keyword/regex matching deliberately "
        "because the actual vocabulary this app needs to understand (a "
        "bounded set of receipt labels, a bounded set of query phrasings) "
        "is small enough that a transparent, zero-dependency rule set "
        "solves it, and because it means the query feature works with no "
        "API key at all."
    ),
    "ML": (
        "The only trained model in this project is the category "
        "classifier: TF-IDF features (unigrams + bigrams) feeding a "
        "scikit-learn LogisticRegression. Feature extraction means "
        "converting text into numeric vectors — TF-IDF weights each word "
        "(or word pair) by how often it appears in a given document "
        "relative to how common it is across all documents, so distinctive "
        "words like 'biryani' or 'electricity' matter more than common "
        "ones. Classification is logistic regression predicting one of "
        "12 category labels. Training uses a stratified 75/25 "
        "train_test_split with a fixed random_state so it's reproducible. "
        "Validation is the held-out 25% test set — I evaluate on data "
        "the model never saw during fitting, which is the whole point of "
        "a test split: training accuracy alone tells you almost nothing "
        "about generalization. I measure accuracy (fraction correct), "
        "macro precision and recall (averaged evenly across all 12 "
        "classes, so a class with fewer examples isn't drowned out), "
        "macro F1 (the harmonic mean of precision and recall), and a "
        "confusion matrix (rows = actual class, columns = predicted "
        "class, so you can see exactly which categories get confused "
        "with which). The measured numbers are in docs/ML_METRICS.md — "
        "around 98% accuracy on this synthetic dataset, which I'm careful "
        "to explain reflects that the synthetic categories use fairly "
        "distinct vocabulary by construction, not that the model would "
        "perform that well on messy real-world receipts."
    ),
    "Analytics": (
        "Analytics here means pandas aggregation, not machine learning. "
        "app/analytics/metrics.py takes a DataFrame of confirmed "
        "transactions and computes: overview stats (total spend, count, "
        "average, largest expense via groupby-free operations like "
        ".sum()/.mean()/.idxmax()), category breakdown (.groupby"
        "('category')['amount'].agg(...) sorted descending, with each "
        "category's percentage share of the total), monthly and weekly "
        "spending (.dt.to_period('M') or ('W') then groupby), and "
        "percentage change between two periods (simple (current - "
        "previous) / previous * 100, returning None rather than infinity "
        "when the previous period is zero — an undefined percentage "
        "change should be represented as undefined, not as a number that "
        "looks real). app/analytics/insights.py turns those metrics into "
        "sentences, but every sentence embeds a real number from the "
        "metrics functions — there's no template that says 'spending is "
        "up' without the actual percentage attached, and insights that "
        "can't be computed (e.g. no data for the previous month) are "
        "simply not generated rather than guessed at."
    ),
    "Database": (
        "One table: transactions, in SQLite, accessed through plain "
        "sqlite3 (no ORM) via app/database/repository.py. The schema "
        "(app/database/db.py) has the fields you'd expect — merchant_raw "
        "and merchant (normalized) kept separately so I never lose the "
        "original OCR text, amount/currency/transaction_date/category as "
        "the core analytics fields, several genuinely-optional fields "
        "(invoice_number, tax, subtotal, payment_method) that aren't on "
        "every receipt, extraction_confidence as a heuristic score, and "
        "confirmation_status ('pending'/'confirmed') as the human-"
        "verification gate. There's one index: "
        "(confirmation_status, transaction_date), because nearly every "
        "query filters by status and sorts or filters by date — at this "
        "project's scale (a personal expense tracker, not a "
        "high-throughput system) that's the one index that actually pays "
        "for itself; I didn't add indexes speculatively. Queries are "
        "parameterized (using ? placeholders, never string-formatted SQL) "
        "specifically to avoid SQL injection, which matters even in a "
        "single-user local app because it's still the correct habit."
    ),
    "LLM": (
        "The LLM layer is opt-in and, by design, never computes a number. "
        "Every dashboard figure and every query answer comes from "
        "app/analytics running against SQLite before an LLM provider is "
        "ever consulted (see app/llm/query_engine.py). The intent parser "
        "(what category, what date range, what metric) is rule-based "
        "keyword matching, not an LLM call — partly so the feature works "
        "with zero API keys, and partly because the actual questions this "
        "app needs to understand are a bounded, known set. If an OpenAI "
        "key is configured, the LLM is handed the already-computed answer "
        "as a fact in the prompt ('do not alter the numbers') and asked "
        "only to reword it more naturally — that's the mechanism that "
        "prevents hallucination: the model is never in the loop for the "
        "arithmetic, only the phrasing. If the API call fails for any "
        "reason (bad key, network issue, rate limit), the code catches "
        "the exception and falls back to the template sentence rather "
        "than surfacing an error to the user."
    ),
    "Security": (
        "Uploads are validated before anything else touches them — file "
        "extension allowlist, a 15MB size cap, an empty-file check, and a "
        "real corruption check (PIL's Image.verify() for images, a "
        "%PDF magic-byte check for PDFs). Uploaded files are never "
        "executed. .env (which would hold OPENAI_API_KEY) is gitignored; "
        "only .env.example with blank values is committed. data/app.db "
        "is gitignored — no real transaction data or receipts are ever "
        "committed to the repo, and the sample data included is entirely "
        "synthetic. SQL queries are parameterized against injection. The "
        "app has no authentication — that's a stated limitation "
        "(docs/LIMITATIONS.md), appropriate for a single-user local "
        "prototype but something I'd flag as the first thing to add "
        "before any real multi-user deployment."
    ),
    "Testing": (
        "53 pytest tests, one module per app/ package. They're mostly "
        "hand-calculated-value tests, not just 'does it run without "
        "crashing' — e.g. test_analytics.py builds a small fixed set of "
        "transactions, works out the correct totals by hand, and asserts "
        "the function returns exactly that. test_repository.py runs "
        "against a temporary SQLite file (never the real data/app.db) via "
        "a pytest fixture, so tests can't corrupt real data and don't "
        "depend on each other's state. Edge cases are tested "
        "deliberately: empty transaction lists, a previous-period value "
        "of zero for percentage change, missing/corrupted/oversized file "
        "uploads, and query-parser questions that don't specify a "
        "category or date range."
    ),
    "Deployment": (
        "The app runs locally with `streamlit run main.py`, requiring "
        "Tesseract and Poppler installed system-wide (pytesseract is a "
        "wrapper around the Tesseract binary, not an installation of it). "
        "docs/DEPLOYMENT.md documents a Streamlit Community Cloud path "
        "(with a packages.txt for the apt-level OCR dependencies) and a "
        "Dockerfile for self-hosting elsewhere. I did not deploy this to "
        "a public URL, and I say why directly: no authentication exists "
        "yet, so a public deployment would let anyone upload files to it "
        "with no login. I did verify the app runs correctly — all the "
        "screenshots in this repo are from a real running instance, "
        "including a real upload going through OCR end-to-end."
    ),
}

CODE_WALKTHROUGH = [
    {
        "file": "app/ocr/pipeline.py",
        "purpose": "Orchestrates validation -> file loading -> preprocessing -> OCR into one function the UI calls.",
        "functions": "process_upload(filename, file_bytes) -> OcrResult",
        "inputs": "Raw uploaded filename and bytes (from Streamlit's file_uploader).",
        "outputs": "OcrResult(success, raw_text, ocr_confidence, error) — a dataclass, not an exception, so the UI can show a clean error message instead of a stack trace.",
        "logic": "Validates the file first (app/utils/validators.py). Loads the first page as a PIL Image — pdf2image.convert_from_bytes for PDFs, PIL.Image.open for images. Runs preprocessing then OCR. Returns failure if OCR produces no text at all.",
        "design_decision": "Every failure path returns a result object with a specific, user-facing error string rather than letting an exception propagate — OCR on a real-world file has several distinct ways to fail (bad file, unreadable PDF, blank image) and each deserves a different message.",
        "failure_cases": "Corrupted PDF that pdf2image can't rasterize; a multi-page PDF where the content that matters is on page 2 (only page 1 is processed); a valid image that's entirely blank or unreadable text (returns success=False with a 'try a clearer photo' message).",
        "interview_question": "Why does this function return a result object instead of raising exceptions for OCR failures?",
    },
    {
        "file": "app/extraction/fields.py",
        "purpose": "Pull merchant, amount, date, currency, invoice number, tax, subtotal, and payment method out of cleaned OCR text using regex heuristics.",
        "functions": "extract_fields(raw_text) -> ExtractedFields; extract_amount, extract_date, extract_merchant, extract_currency, extract_payment_method as separately-testable helpers.",
        "inputs": "Cleaned OCR text (a string, already whitespace-normalized by app/extraction/cleaning.py).",
        "outputs": "ExtractedFields dataclass — every field is Optional; nothing is guessed into existence.",
        "logic": "Amount extraction checks an ordered list of total-label regexes (grand total, total payable, amount paid, etc.) before falling back to 'largest number on the page' — and tracks which path was used (amount_source). Date extraction tries several format patterns and parses ISO year-first dates directly (dateutil's dayfirst flag mishandles them) versus dateutil with dayfirst=True for everything else, matching Indian date conventions. Merchant extraction takes the first line that isn't recognized boilerplate (TAX INVOICE, GSTIN, a URL, etc.).",
        "design_decision": "The AMOUNT_NUMBER regex uses negative lookaround so a number can't be picked up if it's glued to a letter or another digit — this exists specifically because an early version of this code misread a bill number like 'EB2026080099' as a ₹2 billion amount when no labeled total matched.",
        "failure_cases": "A receipt whose total uses a label phrasing not in TOTAL_LABELS (falls back to the largest-number guess, flagged via amount_source); a date format outside the four patterns handled; a merchant name that IS all boilerplate-looking text (returns None, and the verification screen shows it as blank for the user to fill in).",
        "interview_question": "Walk me through what happens when a receipt's total isn't labeled at all.",
    },
    {
        "file": "app/normalization/merchant.py",
        "purpose": "Collapse merchant name variants ('SWIGGY', 'Swiggy Pvt Ltd', 'Swiggy Internet Pvt.') into one canonical name.",
        "functions": "normalize_merchant(raw_name, known_merchants=None) -> str",
        "inputs": "The raw merchant string from extraction, and optionally a list of merchant names already in the database.",
        "outputs": "A canonical, title-cased merchant name, or 'Unknown Merchant' if the input was empty.",
        "logic": "Three layers in order: (1) strip a list of corporate-suffix regex patterns (Pvt Ltd, Ltd, Inc, Internet, .com, etc.); (2) look up the cleaned name in a small hand-maintained alias table for cases suffix-stripping doesn't fully resolve (e.g. Uber's printed legal name reduces to 'Uber India Systems', not 'Uber'); (3) if a list of known merchants is passed in, fuzzy-match against them (rapidfuzz token_sort_ratio, threshold 90) so a near-duplicate OCR misread collapses into an existing merchant instead of creating a lookalike new one.",
        "design_decision": "The alias table is deliberately short — a handful of real cases observed during development, not an attempt at a comprehensive merchant database. A giant hardcoded merchant list would be exactly the kind of fake-impressive complexity this project's brief explicitly said to avoid.",
        "failure_cases": "A merchant with an unusual suffix not in the corporate-suffix list; two genuinely different merchants with similar names that fuzzy-match above the threshold (a false merge) — the threshold of 90 is a manually chosen tradeoff, not tuned against a labeled dataset.",
        "interview_question": "Why maintain both a suffix-stripping step and a separate alias table instead of just one big lookup table?",
    },
    {
        "file": "app/classification/categorize.py",
        "purpose": "The single entry point the rest of the app calls to get a transaction's category — combines the rule-based baseline with an optional ML suggestion.",
        "functions": "categorize(merchant, raw_text, use_ml_suggestion=True) -> CategorizationResult",
        "inputs": "Normalized merchant name and cleaned OCR text.",
        "outputs": "CategorizationResult(category, method, ml_suggestion, ml_confidence) — category/method come from rules.py; ml_suggestion is shown alongside, never substituted in.",
        "logic": "Calls categorize_by_rules() first (merchant table, then keyword table, then 'Other' default). If a trained classifier model file exists, loads it once (module-level cache) and calls predict_category() for a second opinion, returned separately.",
        "design_decision": "The ML suggestion is structurally incapable of silently overriding the rule-based category — the function signature returns both, and the UI (app/ui/upload_page.py) only shows the ML suggestion as a caption when it disagrees with the rule-based result. This was a deliberate choice to keep the more explainable system as the source of truth for a financial tool.",
        "failure_cases": "No trained model file present (predict falls back to ml_suggestion=None — doesn't error); a merchant/keyword combination that matches neither table (defaults to 'Other', method='default').",
        "interview_question": "If the ML classifier and the rule-based categorizer disagree, which one wins and why?",
    },
    {
        "file": "app/analytics/metrics.py",
        "purpose": "Deterministic pandas aggregation over confirmed transactions — the single source of truth for every number the dashboard and the query engine show.",
        "functions": "overview_stats, category_breakdown, merchant_breakdown, monthly_spending, weekly_spending, spending_for_period, percentage_change",
        "inputs": "A pandas DataFrame of transaction dicts, already filtered by the caller to confirmation_status='confirmed'.",
        "outputs": "Plain dicts/lists (via .to_dict(orient='records')) so calling code (Streamlit, the query engine) never has to know pandas.",
        "logic": "overview_stats uses .idxmax() to find the largest expense's full row, not just its amount. category_breakdown groups, sums, sorts descending, and computes each category's percentage share in the same pass. spending_for_period is the shared building block behind both the dashboard's 'This Month' figure and the natural-language query engine's date-scoped answers — written once, used both places.",
        "design_decision": "percentage_change returns None (not infinity or a huge number) when the previous period was zero, because an undefined percentage change genuinely is undefined — returning a large number would look like real data and mislead whoever reads it.",
        "failure_cases": "Empty DataFrame (every function has an explicit empty-input branch, tested in tests/test_analytics.py, returning zeros/empty lists rather than raising).",
        "interview_question": "Why is percentage_change allowed to return None, and what would happen downstream if it returned 0 or infinity instead?",
    },
    {
        "file": "app/llm/query_engine.py",
        "purpose": "Executes a parsed question against the database and produces an answer — the piece that enforces 'the LLM never computes a number.'",
        "functions": "answer_query(question, transactions, provider=None, as_of=None) -> QueryAnswer; resolve_date_range(...)",
        "inputs": "The raw question string, the list of confirmed transactions, and an LLMProvider (defaults to NullProvider).",
        "outputs": "QueryAnswer(intent, result_value, template_answer, final_answer, used_llm) — result_value and template_answer are always populated; final_answer only differs from template_answer if an LLM successfully reworded it.",
        "logic": "Calls parse_query() (rule-based intent parsing) then resolve_date_range() to turn a code like 'last_month' into concrete start/end dates, then dispatches on intent.metric to the right app/analytics call. Only after result_value and template_answer exist does it check provider.is_available and optionally call _reword_with_llm().",
        "design_decision": "The LLM call is wrapped in a try/except that falls back to template_answer on any failure — a network error or bad API key degrades the feature to 'plain sentence' rather than breaking it.",
        "failure_cases": "A question the parser can't confidently categorize (falls back to total_spending / this_month rather than erroring); an LLM provider configured with an invalid key (caught, falls back silently, used_llm=False).",
        "interview_question": "Show me exactly where in this file it would be possible for the LLM to change a number, if at all.",
    },
    {
        "file": "app/database/repository.py",
        "purpose": "All CRUD access to the transactions table — the only file in the app that contains SQL.",
        "functions": "insert_transaction, get_transaction, list_transactions (with optional filters), update_transaction, confirm_transaction, delete_transaction, get_distinct_merchants",
        "inputs": "Transaction dataclass instances (insert) or plain field dicts (update/confirm) plus optional filter kwargs (list).",
        "outputs": "Plain dicts (via sqlite3.Row -> dict), an inserted row's id, or None for a missing row.",
        "logic": "list_transactions builds a WHERE clause dynamically from whichever filters are passed, using parameterized placeholders throughout — never string-formatted SQL. update_transaction restricts writes to an explicit allowlist of column names, so a caller can't accidentally (or maliciously) update a column like id or created_at.",
        "design_decision": "confirm_transaction is a thin wrapper around update_transaction that forces confirmation_status='confirmed' — it's the only path that can move a row from pending to confirmed, which keeps the human-verification gate enforceable at the data-access layer, not just in the UI.",
        "failure_cases": "Calling update_transaction with no allowed fields (returns without touching the database rather than running a no-op or malformed query).",
        "interview_question": "Why is there a column allowlist in update_transaction instead of just accepting whatever dict the caller passes?",
    },
]

CV_BULLETS = {
    "Technical": [
        "Built an end-to-end OCR-to-analytics pipeline (Python, Tesseract, OpenCV) that extracts structured fields from receipt images/PDFs using regex-based heuristics with confidence scoring and graceful handling of missing data.",
        "Designed a SQLite schema and a parameterized, ORM-free data access layer with 53 passing pytest tests covering extraction, normalization, categorization, analytics, and edge cases (empty data, corrupted uploads, malformed input).",
        "Implemented a two-tier expense categorization system: a transparent rule-based baseline plus an optional scikit-learn (TF-IDF + Logistic Regression) classifier, evaluated with accuracy/precision/recall/F1 and a confusion matrix on a held-out test split.",
        "Built a deterministic pandas analytics engine (monthly/weekly aggregation, category breakdowns, percentage-change calculations) that never depends on an external service for its numeric output.",
    ],
    "AI/ML": [
        "Designed an OCR + regex-based document-extraction pipeline for financial receipts, with explicit confidence scoring and a human-in-the-loop verification step to guard against silent extraction errors reaching downstream analytics.",
        "Trained and honestly evaluated a TF-IDF + Logistic Regression text classifier for expense categorization on a documented synthetic dataset, with the tradeoffs between the rule-based baseline and the ML model explicitly analyzed and written up.",
        "Architected an optional LLM layer (provider-swappable interface, OpenAI implementation) constrained so the model only rewords already-computed answers and never performs the underlying calculation — designed specifically to prevent numeric hallucination in a financial context.",
        "Built a rule-based natural-language query parser (English/Hinglish keyword and date-range matching) that maps free-text questions to structured database queries without requiring any LLM API access.",
    ],
    "Product": [
        "Built an AI-assisted expense management web app (Streamlit) that turns a photo of a receipt into a categorized transaction and a live spending dashboard — upload, OCR extraction, human verification, and analytics in one flow.",
        "Designed a human-verification UX step so users review and can correct every OCR-extracted field before it counts toward their spending dashboard, balancing automation with the accuracy financial data requires.",
        "Shipped a spending-insights dashboard (category breakdown, monthly trend, month-over-month change) with data-backed insight sentences and a natural-language question-answering feature, fully functional with or without an AI API key configured.",
    ],
}
