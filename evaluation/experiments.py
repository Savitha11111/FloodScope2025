"""Threshold sweep helpers for evaluating model preference scores."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np


@dataclass
class ThresholdMetrics:
    """Metrics captured for a single threshold decision."""

    threshold: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    true_positive_rate: float
    false_positive_rate: float
    precision: float
    recall: float
    accuracy: float
    f1_score: float


@dataclass
class ThresholdSweepSummary:
    """Aggregate metrics computed across a threshold sweep."""

    metrics: List[ThresholdMetrics]
    roc_fpr: np.ndarray
    roc_tpr: np.ndarray
    roc_thresholds: np.ndarray
    auc: float


@dataclass
class ThresholdOptimisationResult:
    """Holds the outcome of a threshold optimisation run."""

    summary: ThresholdSweepSummary
    best_threshold: float
    criterion: str
    best_metrics: ThresholdMetrics


def _prepare_arrays(
    scores: Sequence[float],
    labels: Sequence[int] | Sequence[bool],
) -> tuple[np.ndarray, np.ndarray]:
    score_arr = np.asarray(scores, dtype=float)
    label_arr = np.asarray(labels)
    if score_arr.ndim != 1 or label_arr.ndim != 1:
        raise ValueError("scores and labels must be one-dimensional arrays")
    if score_arr.size != label_arr.size:
        raise ValueError("scores and labels must have the same length")
    if score_arr.size == 0:
        raise ValueError("scores and labels must not be empty")
    label_arr = label_arr.astype(int)
    if not np.isin(label_arr, [0, 1]).all():
        raise ValueError("labels must be binary values (0 or 1)")
    return score_arr, label_arr


def summarise_threshold_sweep(
    scores: Sequence[float],
    *,
    labels: Sequence[int] | Sequence[bool],
    thresholds: Sequence[float] | None = None,
) -> ThresholdSweepSummary:
    """Evaluate classification quality for a set of score thresholds.

    Parameters
    ----------
    scores:
        Per-scene score deltas indicating how strongly model A outperforms model
        B. Positive values favour model A.
    labels:
        Binary indicators containing the *true* outcome for each scene (1 when
        model A actually achieves the higher IoU, 0 otherwise).
    thresholds:
        Optional explicit list of thresholds to evaluate. When omitted, the
        function will examine all unique score values and include ``-inf`` and
        ``inf`` to cover degenerate cases.
    """

    score_arr, label_arr = _prepare_arrays(scores, labels)

    if thresholds is None:
        unique_thresholds = np.unique(score_arr)
    else:
        unique_thresholds = np.asarray(list(thresholds), dtype=float)
        if unique_thresholds.ndim != 1:
            raise ValueError("thresholds must be a one-dimensional sequence")
    sweep_thresholds = np.concatenate(([-np.inf], unique_thresholds, [np.inf]))

    positives = label_arr.sum()
    negatives = label_arr.size - positives

    metrics: List[ThresholdMetrics] = []
    for threshold in sweep_thresholds:
        predictions = score_arr >= threshold
        tp = int(np.logical_and(predictions, label_arr == 1).sum())
        fp = int(np.logical_and(predictions, label_arr == 0).sum())
        tn = int(np.logical_and(~predictions, label_arr == 0).sum())
        fn = int(np.logical_and(~predictions, label_arr == 1).sum())

        tpr = tp / positives if positives else 0.0
        fpr = fp / negatives if negatives else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tpr
        accuracy = (tp + tn) / label_arr.size if label_arr.size else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        metrics.append(
            ThresholdMetrics(
                threshold=float(threshold),
                true_positives=tp,
                false_positives=fp,
                true_negatives=tn,
                false_negatives=fn,
                true_positive_rate=float(tpr),
                false_positive_rate=float(fpr),
                precision=float(precision),
                recall=float(recall),
                accuracy=float(accuracy),
                f1_score=float(f1),
            )
        )

    roc_fpr, roc_tpr, roc_thresholds, auc = _compute_roc_auc(label_arr, score_arr)

    return ThresholdSweepSummary(
        metrics=metrics,
        roc_fpr=roc_fpr,
        roc_tpr=roc_tpr,
        roc_thresholds=roc_thresholds,
        auc=auc,
    )


def _metric_for_objective(metric: ThresholdMetrics, objective: str) -> float:
    if objective == "youden":
        return metric.true_positive_rate - metric.false_positive_rate
    if objective == "f1":
        return metric.f1_score
    if objective == "accuracy":
        return metric.accuracy
    raise ValueError(
        "Unknown objective '%s'. Expected one of {'youden', 'f1', 'accuracy'}."
        % objective
    )


def optimise_threshold(
    scores: Sequence[float],
    labels: Sequence[int] | Sequence[bool],
    *,
    thresholds: Sequence[float] | None = None,
    objective: str = "youden",
) -> ThresholdOptimisationResult:
    """Determine the optimal threshold separating model preference outcomes."""

    summary = summarise_threshold_sweep(scores, labels=labels, thresholds=thresholds)

    objective_values = np.array([
        _metric_for_objective(metric, objective) for metric in summary.metrics
    ])
    if np.all(np.isnan(objective_values)):
        raise ValueError("Objective produced NaN across all thresholds.")

    max_value = np.nanmax(objective_values)
    candidate_indices = np.flatnonzero(np.isclose(objective_values, max_value, equal_nan=False))
    if candidate_indices.size == 0:
        candidate_indices = np.array([int(np.nanargmax(objective_values))])

    def sort_key(idx: int) -> tuple[float, float]:
        threshold = summary.metrics[idx].threshold
        return (-objective_values[idx], abs(threshold))

    best_index = int(sorted(candidate_indices, key=sort_key)[0])
    best_metric = summary.metrics[best_index]

    return ThresholdOptimisationResult(
        summary=summary,
        best_threshold=best_metric.threshold,
        criterion=objective,
        best_metrics=best_metric,
    )


def _compute_roc_auc(labels: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Compute ROC coordinates and AUC without relying on scikit-learn.

    The implementation mirrors the behaviour of :func:`sklearn.metrics.roc_curve`
    and :func:`sklearn.metrics.roc_auc_score` but avoids introducing a heavy
    dependency into the evaluation tooling.
    """

    labels = labels.astype(int)
    if labels.ndim != 1 or scores.ndim != 1:
        raise ValueError("labels and scores must be one-dimensional arrays")
    if labels.size != scores.size:
        raise ValueError("labels and scores must be aligned")

    positives = labels.sum()
    negatives = labels.size - positives
    if positives == 0 or negatives == 0:
        # ROC is undefined when only one class is present.
        return (
            np.array([0.0, 1.0], dtype=float),
            np.array([0.0, 1.0], dtype=float),
            np.array([np.inf, -np.inf], dtype=float),
            float("nan"),
        )

    order = np.argsort(scores, kind="mergesort")[::-1]
    sorted_scores = scores[order]
    sorted_labels = labels[order]

    distinct_indices = np.where(np.diff(sorted_scores))[0]
    threshold_idxs = np.r_[distinct_indices, sorted_labels.size - 1]

    tps = np.cumsum(sorted_labels)[threshold_idxs]
    fps = (1 + threshold_idxs) - tps

    tps = np.r_[0, tps]
    fps = np.r_[0, fps]
    thresholds = np.r_[np.inf, sorted_scores[threshold_idxs]]

    tpr = tps / positives
    fpr = fps / negatives

    auc = float(np.trapezoid(tpr, fpr))

    return fpr, tpr, thresholds, auc
