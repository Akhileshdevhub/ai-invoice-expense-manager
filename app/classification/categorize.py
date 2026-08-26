"""Entry point the rest of the app calls to categorize a transaction.

Default path: rule-based (app/classification/rules.py) — transparent,
needs no training data, and its decisions are traceable to a specific
rule. The ML classifier (app/classification/ml_classifier.py) only runs
when explicitly enabled, and only as a second opinion shown alongside the
rule-based result — it never silently overrides it. See
docs/ML_PIPELINE.md for the reasoning.
"""

from dataclasses import dataclass
from typing import Optional

from app.classification.ml_classifier import load_model, predict_category
from app.classification.rules import categorize_by_rules, DEFAULT_CATEGORY

_ml_pipeline_cache = None
_ml_load_attempted = False


@dataclass
class CategorizationResult:
    category: str
    method: str  # 'merchant_match' | 'keyword_match' | 'default'
    ml_suggestion: Optional[str] = None
    ml_confidence: Optional[float] = None


def categorize(merchant: str, raw_text: str, use_ml_suggestion: bool = True) -> CategorizationResult:
    category, method = categorize_by_rules(merchant, raw_text)

    ml_suggestion, ml_confidence = None, None
    if use_ml_suggestion:
        pipeline = _get_ml_pipeline()
        if pipeline is not None:
            ml_suggestion, ml_confidence = predict_category(pipeline, f"{merchant}\n{raw_text}")

    return CategorizationResult(
        category=category,
        method=method,
        ml_suggestion=ml_suggestion,
        ml_confidence=ml_confidence,
    )


def _get_ml_pipeline():
    """Load the trained classifier once per process; a missing model file just disables the suggestion."""
    global _ml_pipeline_cache, _ml_load_attempted
    if not _ml_load_attempted:
        _ml_pipeline_cache = load_model()
        _ml_load_attempted = True
    return _ml_pipeline_cache
