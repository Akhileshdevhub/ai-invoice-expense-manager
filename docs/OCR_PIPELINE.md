# OCR Pipeline

## Why Tesseract

Tesseract was chosen over PaddleOCR or a cloud OCR API for three practical
reasons:

1. **Runs fully offline, no account/API key.** Anyone cloning this repo
   can `apt install tesseract-ocr` and run the whole pipeline — no signup,
   no billing, no network dependency. That matters for a project meant to
   be run and inspected by someone else (an interviewer, a grader).
2. **It's the OCR engine most receipts-processing tutorials and papers
   compare against.** Its behavior, config flags, and failure modes are
   well documented, which makes it possible to actually understand and
   tune (see `TESSERACT_CONFIG` in `app/ocr/engine.py`) rather than treat
   as a black box.
3. **Good enough for printed receipts.** Tesseract's LSTM engine (v4+)
   handles printed text at typical receipt-photo resolution well. It is
   not the state of the art for OCR generally — PaddleOCR and cloud
   services (Google Document AI, AWS Textract) outperform it on rotated
   text, complex layouts, and handwriting — but this project's inputs
   (printed receipts/invoices) are within Tesseract's strengths.

No cloud fallback is implemented. Adding one would mean a second,
functionally identical `app/ocr/engine.py` implementation behind the same
interface (`run_ocr_with_confidence(image) -> (text, confidence)`) — the
architecture supports it, but it wasn't built because it would need an
API key this project shouldn't require to run.

## Pipeline stages

```
upload (Streamlit file_uploader)
  -> app/utils/validators.py     validate type, size, non-empty, non-corrupted
  -> app/ocr/pipeline.py         load first page (PDF -> pdf2image, image -> PIL.Image.open)
  -> app/ocr/preprocess.py       grayscale -> upscale (if small) -> denoise -> adaptive threshold
  -> app/ocr/engine.py           pytesseract.image_to_data (--oem 3 --psm 6)
  -> raw text + mean word confidence
```

### Preprocessing steps, and why each one is there

- **Grayscale**: color carries no text information and roughly triples
  the pixel data Tesseract has to process.
- **Upscale if small** (`MIN_DIMENSION_FOR_UPSCALE = 1000px`): Tesseract's
  LSTM models were trained mostly on ~300 DPI scans. A receipt photo
  downsized by a messaging app (WhatsApp compresses images aggressively)
  can fall well below the resolution where character shapes are still
  distinguishable; upscaling with cubic interpolation before OCR
  measurably reduced misreads during development.
- **Denoising** (`cv2.fastNlMeansDenoising`): phone cameras in typical
  indoor lighting introduce sensor grain that Tesseract can mistake for
  extra character strokes (e.g. reading "0" as "8").
- **Adaptive thresholding**: converts to pure black/white using a
  locally-computed threshold per region, rather than one global cutoff.
  This matters specifically for receipts because a phone photo very often
  has uneven lighting (a shadow across half the receipt, glare on thermal
  paper) — a global threshold would blow out one half of the image.

### `--psm 6`

Tesseract's page segmentation mode controls how it looks for text blocks.
The default (`--psm 3`) tries to detect a page layout (columns, headers).
Receipts are a single narrow, dense column of text, not a laid-out page —
`--psm 6` ("assume a single uniform block of text") consistently
performed better on the sample receipts used during development. This is
a real, documented tradeoff: `--psm 6` would perform worse on a genuinely
multi-column document.

## Known failure cases

These are real limitations, not hypothetical ones:

- **Low-quality/blurry photos.** Motion blur or very low light produces
  raw text with enough character-level errors that regex field extraction
  (which expects fairly clean label text like "Total") can miss the total
  line entirely. The pipeline falls back to "largest number on the page,"
  which is a guess, not a real extraction — this is why `amount_source`
  is tracked and surfaced to the user (see `docs/ARCHITECTURE.md`,
  "human verification gate").
- **Handwritten receipts.** Tesseract's LSTM models are trained on
  printed text; handwriting recognition is a fundamentally different,
  much harder problem this project doesn't attempt.
- **Non-standard layouts.** A receipt where the total is printed *before*
  the line items, or where labels are abbreviated in ways not in
  `app/extraction/fields.py`'s label lists (e.g. "Net Amt" instead of
  "Total"), won't be recognized as a labeled total and falls back to the
  largest-number heuristic.
- **Multi-page PDFs.** Only the first page is OCR'd
  (`MAX_PDF_PAGES_PROCESSED = 1` in `app/ocr/pipeline.py`). A multi-page
  PDF is treated as a single-page receipt; if the total is on page 2,
  extraction will not find it.
- **Numbers embedded in IDs.** An invoice/bill number containing digits
  (e.g. "EB2026080099") could, in principle, be picked up by a naive
  "largest number" fallback. `app/extraction/fields.py` guards against
  this by requiring an amount to be its own token (not glued to letters
  or more digits) — see the `AMOUNT_NUMBER` regex and its comment — but
  this guard is heuristic, not a guarantee for every possible layout.

## Confidence: what it does and doesn't mean

Two separate confidence numbers exist in this codebase, and it's worth
being precise about what each measures:

- **OCR confidence** (`app/ocr/engine.py`, `run_ocr_with_confidence`):
  Tesseract's own mean per-word confidence (0-100). This reflects how
  sure the OCR engine is about the *characters* it read — it says
  nothing about which word is the merchant name vs. an address line.
- **Extraction confidence** (`app/extraction/fields.py`,
  `_estimate_confidence`): a hand-written heuristic (0-1) based on
  whether a labeled total was found vs. guessed, and whether a date and
  merchant were found at all. It is not a calibrated statistical
  probability and is not derived from any model — it exists purely to
  decide when to show the user an extra warning on the verification
  screen.
