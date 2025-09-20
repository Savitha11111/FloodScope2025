import numpy as np
import pytest

from evaluation.data_loader import compute_scene_preferences, optimise_threshold_from_masks
from evaluation.experiments import optimise_threshold


def _mask_from_indices(indices, shape=(2, 2)):
    mask = np.zeros(shape, dtype=bool)
    if indices:
        rows, cols = np.unravel_index(indices, shape)
        mask[rows, cols] = True
    return mask


def _generate_dataset(num_positive: int, num_negative: int):
    """Create synthetic masks where model A wins ``num_positive`` scenes."""

    gt = _mask_from_indices([0, 1])
    gt_alt = _mask_from_indices([0, 3])

    gt_masks = []
    model_a_masks = []
    model_b_masks = []

    # Scenes where model A clearly outperforms model B
    for i in range(num_positive):
        base_gt = gt if i % 2 == 0 else gt_alt
        model_a = base_gt.copy()
        worse_pixel = 0 if i % 2 == 0 else 3
        model_b = _mask_from_indices([worse_pixel])
        gt_masks.append(base_gt)
        model_a_masks.append(model_a)
        model_b_masks.append(model_b)

    # Scenes where model B outperforms model A
    for i in range(num_negative):
        base_gt = gt if i % 2 == 0 else gt_alt
        model_b = base_gt.copy()
        worse_pixel = 2 if i % 2 == 0 else 1
        model_a = _mask_from_indices([worse_pixel])
        gt_masks.append(base_gt)
        model_a_masks.append(model_a)
        model_b_masks.append(model_b)

    return gt_masks, model_a_masks, model_b_masks


@pytest.mark.parametrize("positive_scenes, negative_scenes", [(5, 3), (3, 5)])
def test_compute_scene_preferences_label_balance(positive_scenes, negative_scenes):
    gt_masks, model_a_masks, model_b_masks = _generate_dataset(positive_scenes, negative_scenes)
    summary = compute_scene_preferences(gt_masks, model_a_masks, model_b_masks)

    assert summary.labels.shape == summary.score_deltas.shape
    assert summary.labels.sum() == positive_scenes
    assert np.all(summary.labels[:positive_scenes] == 1)
    assert np.all(summary.labels[positive_scenes:] == 0)


def test_threshold_optimisation_reflects_label_distribution():
    gt_masks, model_a_masks, model_b_masks = _generate_dataset(6, 2)
    summary_a = compute_scene_preferences(gt_masks, model_a_masks, model_b_masks)

    # Invert the predictions to simulate model B being better most of the time
    summary_b = compute_scene_preferences(gt_masks, model_b_masks, model_a_masks)

    # Simulated analyser scores that are identical for both scenarios.
    analyser_scores = np.linspace(-1.0, 1.0, summary_a.labels.size)

    result_a = optimise_threshold(analyser_scores, summary_a.labels)
    result_b = optimise_threshold(analyser_scores, summary_b.labels)

    assert summary_a.labels.sum() != summary_b.labels.sum(), "Label distributions should differ"
    assert result_a.summary.auc < 0.2
    assert result_b.summary.auc > 0.8
    assert result_a.best_threshold < result_b.best_threshold


def test_pipeline_wrapper_matches_direct_invocation():
    gt_masks, model_a_masks, model_b_masks = _generate_dataset(4, 4)
    direct_summary = compute_scene_preferences(gt_masks, model_a_masks, model_b_masks)
    direct_result = optimise_threshold(direct_summary.score_deltas, direct_summary.labels)

    pipeline_result = optimise_threshold_from_masks(gt_masks, model_a_masks, model_b_masks)

    assert np.isclose(direct_result.best_threshold, pipeline_result.best_threshold)
    assert pytest.approx(direct_result.summary.auc) == pipeline_result.summary.auc
