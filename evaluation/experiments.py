"""Experiment orchestration for the dual-model evaluation."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

import numpy as np

from evaluation.metrics import (
    MetricResult,
    balanced_accuracy_score,
    f1_score,
    iou_score,
    precision_score,
    recall_score,
)
from services.cloud_analyzer import CloudAnalyzer


@dataclass
class EvaluationSample:
    scene_id: str
    cloud_fraction: float
    prithvi_prediction: Sequence[int]
    ai4flood_prediction: Sequence[int]
    ground_truth: Sequence[int]


def _as_boolean_mask(array: Sequence[int]) -> np.ndarray:
    return np.asarray(array, dtype=bool)


def select_model(cloud_fraction: float, threshold: float) -> str:
    return "prithvi" if cloud_fraction < threshold else "ai4flood"


def evaluate_switching_strategy(samples: Iterable[EvaluationSample], *, threshold: float, analyzer: CloudAnalyzer | None = None) -> Dict[str, object]:
    analyzer = analyzer or CloudAnalyzer(cloud_threshold=threshold)

    y_true: List[int] = []
    y_pred: List[int] = []

    model_usage = {"prithvi": 0, "ai4flood": 0}

    for sample in samples:
        model = select_model(sample.cloud_fraction, threshold)
        model_usage[model] += 1
        prediction = sample.prithvi_prediction if model == "prithvi" else sample.ai4flood_prediction
        y_true.extend(_as_boolean_mask(sample.ground_truth))
        y_pred.extend(_as_boolean_mask(prediction))

    metrics: List[MetricResult] = [
        iou_score(y_true, y_pred),
        f1_score(y_true, y_pred),
        precision_score(y_true, y_pred),
        recall_score(y_true, y_pred),
        balanced_accuracy_score(y_true, y_pred),
    ]

    return {
        "threshold": threshold,
        "metrics": {metric.name: metric.value for metric in metrics},
        "model_usage": model_usage,
    }


def _model_wins_prithvi(sample: EvaluationSample) -> bool:
    """Return ``True`` when Prithvi outperforms AI4Flood for the sample."""

    gt = _as_boolean_mask(sample.ground_truth)
    if gt.size == 0:
        return True

    prithvi_mask = _as_boolean_mask(sample.prithvi_prediction)
    ai4flood_mask = _as_boolean_mask(sample.ai4flood_prediction)

    prithvi_iou = iou_score(gt, prithvi_mask).value
    ai4flood_iou = iou_score(gt, ai4flood_mask).value

    if np.isclose(prithvi_iou, ai4flood_iou):
        # Break ties in favour of the model that predicts fewer positives to avoid
        # inflating flood detections under heavy cloud.
        prithvi_support = np.sum(prithvi_mask)
        ai4flood_support = np.sum(ai4flood_mask)
        if prithvi_support == ai4flood_support:
            return True
        return prithvi_support <= ai4flood_support
    return prithvi_iou >= ai4flood_iou


def summarise_threshold_sweep(samples: Iterable[EvaluationSample], thresholds: Sequence[float]) -> Dict[str, object]:
    analyzer = CloudAnalyzer()
    materialised_samples = list(samples)
    coverages = [sample.cloud_fraction for sample in materialised_samples]
    labels = [_model_wins_prithvi(sample) for sample in materialised_samples]
    optimisation = analyzer.optimise_threshold(coverages, labels, thresholds)
    decision_curve = analyzer.decision_curve(coverages, labels, thresholds)

    sweep_results = []
    for threshold in thresholds:
        sweep_results.append(
            evaluate_switching_strategy(materialised_samples, threshold=threshold, analyzer=analyzer)
        )

    return {
        "optimisation": optimisation,
        "decision_curve": decision_curve,
        "sweep_results": sweep_results,
    }


def export_results(results: Dict[str, object], destination: pathlib.Path) -> pathlib.Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    return destination


__all__ = [
    "EvaluationSample",
    "evaluate_switching_strategy",
    "summarise_threshold_sweep",
    "export_results",
]
