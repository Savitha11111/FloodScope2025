"""Helpers for preparing scene-level evaluation signals for threshold optimisation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from .experiments import optimise_threshold


@dataclass
class ScenePreferenceSummary:
    """Holds scene-level comparison metrics between two models.

    Attributes
    ----------
    score_deltas:
        The per-scene difference between the IoU (or any other quality metric)
        achieved by model A minus model B. Positive values therefore indicate a
        preference towards model A.
    labels:
        Binary array where 1 denotes that model A achieved a strictly higher
        IoU than model B for the scene.
    model_a_iou:
        IoU scores for model A for each scene.
    model_b_iou:
        IoU scores for model B for each scene.
    scene_ids:
        Optional identifiers describing the scenes in the same order as the
        arrays above. When omitted, scenes are implicitly indexed.
    """

    score_deltas: np.ndarray
    labels: np.ndarray
    model_a_iou: np.ndarray
    model_b_iou: np.ndarray
    scene_ids: Tuple[str, ...] | None = None

    def as_threshold_inputs(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return the values expected by :func:`optimise_threshold`.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            A tuple containing the score deltas and the binary labels.
        """

        return self.score_deltas, self.labels


def _ensure_bool_array(mask: np.ndarray) -> np.ndarray:
    arr = np.asarray(mask)
    if arr.dtype != np.bool_:
        arr = arr.astype(bool)
    if arr.ndim == 0:
        raise ValueError("Masks must be at least one-dimensional arrays.")
    return arr


def _compute_iou(ground_truth: np.ndarray, prediction: np.ndarray) -> float:
    gt = _ensure_bool_array(ground_truth)
    pred = _ensure_bool_array(prediction)
    intersection = np.logical_and(gt, pred).sum(dtype=float)
    union = np.logical_or(gt, pred).sum(dtype=float)
    if union == 0:
        # Both masks empty -> perfect IoU, only prediction populated -> zero IoU.
        return 1.0 if intersection == 0 else 0.0
    return float(intersection / union)


def compute_scene_preferences(
    ground_truth_masks: Sequence[np.ndarray],
    model_a_masks: Sequence[np.ndarray],
    model_b_masks: Sequence[np.ndarray],
    *,
    scene_ids: Iterable[str] | None = None,
    tie_strategy: str = "negative",
) -> ScenePreferenceSummary:
    """Compute scene-level IoU comparisons for two competing models.

    Parameters
    ----------
    ground_truth_masks:
        Sequence of ground-truth flood masks.
    model_a_masks, model_b_masks:
        Predicted masks for the two models under comparison. The sequences must
        be aligned with ``ground_truth_masks``.
    scene_ids:
        Optional identifiers for each scene. When not provided the scenes are
        implicitly indexed.
    tie_strategy:
        Specifies how to label scenes where both models achieve exactly the same
        IoU. Accepted values are ``"negative"`` (default, mark as model B
        winning), ``"positive"`` (mark as model A winning) or ``"skip`` to drop
        the scene from the results.

    Returns
    -------
    ScenePreferenceSummary
        An object holding the IoU scores, their difference and the resulting
        binary labels indicating which model performed better.
    """

    gt_masks = list(ground_truth_masks)
    model_a = list(model_a_masks)
    model_b = list(model_b_masks)

    if not (len(gt_masks) == len(model_a) == len(model_b)):
        raise ValueError("All mask collections must have the same length.")

    if scene_ids is not None:
        scene_id_list = tuple(scene_ids)
        if len(scene_id_list) != len(gt_masks):
            raise ValueError("scene_ids must align with the provided masks.")
    else:
        scene_id_list = None

    score_deltas: List[float] = []
    labels: List[int] = []
    model_a_iou: List[float] = []
    model_b_iou: List[float] = []
    retained_scene_ids: List[str] = []

    for idx, (gt, pred_a, pred_b) in enumerate(zip(gt_masks, model_a, model_b)):
        iou_a = _compute_iou(gt, pred_a)
        iou_b = _compute_iou(gt, pred_b)
        delta = iou_a - iou_b

        if delta > 0:
            label = 1
        elif delta < 0:
            label = 0
        else:
            if tie_strategy == "negative":
                label = 0
            elif tie_strategy == "positive":
                label = 1
            elif tie_strategy == "skip":
                continue
            else:
                raise ValueError(
                    "tie_strategy must be 'negative', 'positive' or 'skip'."
                )

        score_deltas.append(delta)
        labels.append(label)
        model_a_iou.append(iou_a)
        model_b_iou.append(iou_b)
        if scene_id_list is not None:
            retained_scene_ids.append(scene_id_list[idx])

    summary = ScenePreferenceSummary(
        score_deltas=np.asarray(score_deltas, dtype=float),
        labels=np.asarray(labels, dtype=int),
        model_a_iou=np.asarray(model_a_iou, dtype=float),
        model_b_iou=np.asarray(model_b_iou, dtype=float),
        scene_ids=tuple(retained_scene_ids) if scene_id_list is not None else None,
    )
    return summary


def optimise_threshold_from_masks(
    ground_truth_masks: Sequence[np.ndarray],
    model_a_masks: Sequence[np.ndarray],
    model_b_masks: Sequence[np.ndarray],
    **optimisation_kwargs,
):
    """Convenience wrapper combining :func:`compute_scene_preferences` and
    :func:`optimise_threshold`.

    Parameters
    ----------
    ground_truth_masks, model_a_masks, model_b_masks:
        See :func:`compute_scene_preferences`.
    optimisation_kwargs:
        Additional arguments forwarded to :func:`optimise_threshold` such as the
        optimisation objective.

    Returns
    -------
    ThresholdOptimisationResult
        The outcome of the threshold optimisation using the per-scene IoU
        differences as the predictive signal and the computed labels.
    """

    summary = compute_scene_preferences(ground_truth_masks, model_a_masks, model_b_masks)
    scores, labels = summary.as_threshold_inputs()
    return optimise_threshold(scores, labels, **optimisation_kwargs)
