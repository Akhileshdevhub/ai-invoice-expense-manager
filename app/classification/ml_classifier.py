"""Optional ML category classifier: TF-IDF + Logistic Regression.

Why this algorithm: with ~240 short synthetic text samples, logistic
regression over TF-IDF features is about the most complex model that's
actually justifiable. A neural network would overfit a dataset this size
before it learned anything generalizable, and its decisions would be
harder to inspect than logistic regression's per-word coefficients.
Naive Bayes was also tried during development (see docs/ML_PIPELINE.md
for the comparison) — logistic regression scored marginally higher.

This classifier is NOT the default categorizer — app/classification/rules.py
is. This module exists as a documented, honestly-evaluated experiment;
see categorize.py for how the two are combined.
"""

import pickle
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix,
)

MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "classifier_model.pkl"


@dataclass
class EvalMetrics:
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    confusion_matrix: list
    labels: list
    n_train: int
    n_test: int


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)),
        ("clf", LogisticRegression(max_iter=1000)),
    ])


def train_and_evaluate(texts: list[str], labels: list[str]) -> tuple[Pipeline, EvalMetrics]:
    """Train on a stratified split and return the fitted pipeline plus honest metrics.

    A held-out test split (not the training accuracy) is what gets
    reported in docs/ML_PIPELINE.md — training accuracy on a dataset
    this small would be close to 100% and would be a meaningless number.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    label_order = sorted(set(labels))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, predictions, labels=label_order, average="macro", zero_division=0
    )
    metrics = EvalMetrics(
        accuracy=round(accuracy_score(y_test, predictions), 3),
        precision_macro=round(precision, 3),
        recall_macro=round(recall, 3),
        f1_macro=round(f1, 3),
        confusion_matrix=confusion_matrix(y_test, predictions, labels=label_order).tolist(),
        labels=label_order,
        n_train=len(X_train),
        n_test=len(X_test),
    )
    return pipeline, metrics


def save_model(pipeline: Pipeline, path: Path = MODEL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(pipeline, f)


def load_model(path: Path = MODEL_PATH) -> Pipeline | None:
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def predict_category(pipeline: Pipeline, text: str) -> tuple[str, float]:
    """Return (predicted_category, confidence) where confidence is the model's own max class probability."""
    probabilities = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    best_idx = probabilities.argmax()
    return classes[best_idx], round(float(probabilities[best_idx]), 3)
