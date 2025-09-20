"""Core evaluation metrics used in the dual-model study."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass
class MetricResult:
    name: str
    value: float
    support: int


def confusion_matrix(y_true: Sequence[int], y_pred: Sequence[int]) -> tuple[int, int, int, int]:
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)
    tp = int(np.sum(y_true & y_pred))
    tn = int(np.sum(~y_true & ~y_pred))
    fp = int(np.sum(~y_true & y_pred))
    fn = int(np.sum(y_true & ~y_pred))
    return tp, fp, tn, fn


def iou_score(y_true: Sequence[int], y_pred: Sequence[int]) -> MetricResult:
    tp, fp, tn, fn = confusion_matrix(y_true, y_pred)
    denom = tp + fp + fn
    score = tp / denom if denom > 0 else 0.0
    return MetricResult("IoU", float(score), int(tp + fp + fn + tn))


def f1_score(y_true: Sequence[int], y_pred: Sequence[int]) -> MetricResult:
    tp, fp, tn, fn = confusion_matrix(y_true, y_pred)
    denom = 2 * tp + fp + fn
    score = (2 * tp) / denom if denom > 0 else 0.0
    return MetricResult("F1", float(score), int(tp + fp + tn + fn))


def precision_score(y_true: Sequence[int], y_pred: Sequence[int]) -> MetricResult:
    tp, fp, tn, fn = confusion_matrix(y_true, y_pred)
    denom = tp + fp
    score = tp / denom if denom > 0 else 0.0
    return MetricResult("Precision", float(score), int(tp + fp + tn + fn))


def recall_score(y_true: Sequence[int], y_pred: Sequence[int]) -> MetricResult:
    tp, fp, tn, fn = confusion_matrix(y_true, y_pred)
    denom = tp + fn
    score = tp / denom if denom > 0 else 0.0
    return MetricResult("Recall", float(score), int(tp + fp + tn + fn))


def balanced_accuracy_score(y_true: Sequence[int], y_pred: Sequence[int]) -> MetricResult:
    tp, fp, tn, fn = confusion_matrix(y_true, y_pred)
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    score = (tpr + tnr) / 2.0
    return MetricResult("BalancedAccuracy", float(score), int(tp + fp + tn + fn))


def bootstrap_metric(metric_fn, y_true: Sequence[int], y_pred: Sequence[int], *, iterations: int = 1000, seed: int = 42) -> dict:
    """Estimate metric confidence intervals via bootstrap resampling."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)
    if n == 0:
        raise ValueError("Cannot bootstrap metrics with empty inputs")

    samples = []
    for _ in range(iterations):
        indices = rng.integers(0, n, size=n)
        res = metric_fn(y_true[indices], y_pred[indices])
        samples.append(res.value)

    lower = float(np.percentile(samples, 2.5))
    upper = float(np.percentile(samples, 97.5))
    return {
        "metric": metric_fn.__name__,
        "estimate": float(np.mean(samples)),
        "ci95": (lower, upper),
    }


__all__ = [
    "MetricResult",
    "confusion_matrix",
    "iou_score",
    "f1_score",
    "precision_score",
    "recall_score",
    "balanced_accuracy_score",
    "bootstrap_metric",
]
