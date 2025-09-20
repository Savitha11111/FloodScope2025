"""Utilities for evaluating model comparisons and threshold selection."""

from .experiments import optimise_threshold, summarise_threshold_sweep
from .data_loader import (
    ScenePreferenceSummary,
    compute_scene_preferences,
    optimise_threshold_from_masks,
)

__all__ = [
    "optimise_threshold",
    "summarise_threshold_sweep",
    "ScenePreferenceSummary",
    "compute_scene_preferences",
    "optimise_threshold_from_masks",
]
