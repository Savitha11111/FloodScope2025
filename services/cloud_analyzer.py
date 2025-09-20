"""Data-driven cloud analysis and threshold optimisation."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import rasterio

from llm.cloud_coverage import CloudCoverageError, calculate_cloud_coverage
from llm.config import CLOUD_COVERAGE_THRESHOLD


@dataclass
class CloudAnalysisResult:
    cloud_fraction: float
    best_sensor: str
    sentinel1_quality: float
    sentinel2_quality: float
    reasoning: str
    recommendation_confidence: float


class CloudAnalyzer:
    """Analyse Sentinel-2 scenes and derive optimal switching thresholds."""

    def __init__(self, cloud_threshold: Optional[float] = None) -> None:
        self.cloud_threshold = cloud_threshold if cloud_threshold is not None else CLOUD_COVERAGE_THRESHOLD

    # ------------------------------------------------------------------
    # Scene analysis
    # ------------------------------------------------------------------
    def analyze_cloud_cover(self, satellite_data: Dict[str, Dict[str, object]]) -> Dict[str, object]:
        """Analyse satellite data bundle and recommend the best sensor.

        Parameters
        ----------
        satellite_data:
            Dictionary containing optional ``sentinel2`` and ``sentinel1`` entries.
            ``sentinel2`` may include ``path`` or ``image_path`` keys pointing to a
            GeoTIFF on disk. If ``cloud_percentage`` is already provided the value
            is reused.
        """
        sentinel2_info = satellite_data.get("sentinel2", {}) if satellite_data else {}
        sentinel1_info = satellite_data.get("sentinel1", {}) if satellite_data else {}

        coverage = self._resolve_cloud_fraction(sentinel2_info)
        sentinel1_quality = self._sentinel1_quality(sentinel1_info)
        sentinel2_quality = self._sentinel2_quality(coverage, sentinel2_info)

        use_prithvi = coverage < self.cloud_threshold
        best_sensor = "Sentinel-2" if use_prithvi else "Sentinel-1"

        reasoning = self._reason(best_sensor, coverage, sentinel1_quality, sentinel2_quality)
        confidence = abs(sentinel1_quality - sentinel2_quality)

        result = {
            "cloud_cover_percentage": coverage * 100.0,
            "sentinel1_quality": sentinel1_quality,
            "sentinel2_quality": sentinel2_quality,
            "best_sensor": best_sensor,
            "cloud_threshold_exceeded": coverage >= self.cloud_threshold,
            "reasoning": reasoning,
            "recommendation_confidence": confidence,
        }
        return result

    def _resolve_cloud_fraction(self, sentinel2_info: Dict[str, object]) -> float:
        if not sentinel2_info:
            return 1.0
        if "cloud_percentage" in sentinel2_info:
            return float(sentinel2_info["cloud_percentage"]) / 100.0
        if "cloud_fraction" in sentinel2_info:
            return float(sentinel2_info["cloud_fraction"])

        image_path = sentinel2_info.get("path") or sentinel2_info.get("image_path") or sentinel2_info.get("data")
        if isinstance(image_path, str):
            try:
                return calculate_cloud_coverage(image_path)
            except CloudCoverageError as exc:
                raise CloudCoverageError(
                    f"Failed to derive cloud fraction for Sentinel-2 scene '{image_path}': {exc}"
                ) from exc
        raise ValueError("Sentinel-2 information must include a file path or cloud coverage value")

    @staticmethod
    def _sentinel1_quality(info: Dict[str, object]) -> float:
        if not info:
            return 0.0
        quality = 0.0
        if info.get("data") or info.get("path"):
            quality += 0.5
        if info.get("polarization") in {"DV", "VH-VV"}:
            quality += 0.25
        if info.get("acquisition_mode") in {"IW", "EW"}:
            quality += 0.15
        if info.get("preprocessed"):
            quality += 0.1
        return min(1.0, quality)

    def _sentinel2_quality(self, coverage: float, info: Dict[str, object]) -> float:
        if not info:
            return 0.0
        availability = 0.8 if info.get("path") or info.get("data") else 0.0
        weather_independence = max(0.0, 1.0 - coverage)
        visibility = weather_independence
        quality = availability * 0.3 + visibility * 0.7
        return float(max(0.0, min(1.0, quality)))

    @staticmethod
    def _reason(best_sensor: str, coverage: float, s1_quality: float, s2_quality: float) -> str:
        coverage_pct = coverage * 100.0
        if best_sensor == "Sentinel-1":
            if coverage_pct > 70:
                return f"Sentinel-1 selected because optical imagery is highly obscured ({coverage_pct:.1f}% clouds)."
            if s2_quality < 0.2:
                return "Sentinel-1 selected due to missing or low-quality optical data."
            return f"Sentinel-1 offers more reliable coverage at {coverage_pct:.1f}% cloudiness."
        if coverage_pct < 20:
            return f"Sentinel-2 selected with clear conditions ({coverage_pct:.1f}% clouds)."
        return f"Sentinel-2 selected—cloud cover {coverage_pct:.1f}% remains below the configured threshold."

    # ------------------------------------------------------------------
    # Threshold optimisation utilities
    # ------------------------------------------------------------------
    def optimise_threshold(self, coverages: Sequence[float], labels: Sequence[bool], thresholds: Optional[Sequence[float]] = None) -> Dict[str, object]:
        """Compute ROC statistics and the optimal cloud threshold.

        ``labels`` should be ``True`` when Sentinel-2 (Prithvi) is the correct
        choice for the scene (i.e., low cloud cover).
        """
        if len(coverages) != len(labels):
            raise ValueError("Coverage values and labels must have the same length")
        coverages_array = np.asarray(coverages, dtype=np.float32)
        labels_array = np.asarray(labels, dtype=bool)

        if thresholds is None:
            thresholds = np.linspace(0.05, 0.9, 18)
        else:
            thresholds = np.asarray(thresholds, dtype=np.float32)

        roc_points: List[Dict[str, float]] = []
        best_threshold = self.cloud_threshold
        best_j = -math.inf
        for threshold in thresholds:
            predicted_prithvi = coverages_array < threshold
            tp = np.sum(predicted_prithvi & labels_array)
            tn = np.sum(~predicted_prithvi & ~labels_array)
            fp = np.sum(predicted_prithvi & ~labels_array)
            fn = np.sum(~predicted_prithvi & labels_array)

            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            roc_points.append({"threshold": float(threshold), "tpr": float(tpr), "fpr": float(fpr)})

            j_stat = tpr - fpr
            if j_stat > best_j:
                best_j = j_stat
                best_threshold = float(threshold)

        auc = self._auc_from_roc(roc_points)
        return {
            "best_threshold": best_threshold,
            "roc": roc_points,
            "auc": auc,
            "youden_j": best_j,
        }

    @staticmethod
    def _auc_from_roc(points: List[Dict[str, float]]) -> float:
        if not points:
            return 0.0
        sorted_points = sorted(points, key=lambda p: p["fpr"])
        xs = [0.0] + [p["fpr"] for p in sorted_points] + [1.0]
        ys = [0.0] + [p["tpr"] for p in sorted_points] + [1.0]
        auc = 0.0
        for i in range(1, len(xs)):
            auc += (xs[i] - xs[i - 1]) * (ys[i] + ys[i - 1]) / 2.0
        return float(max(0.0, min(1.0, auc)))

    def decision_curve(self, coverages: Sequence[float], labels: Sequence[bool], thresholds: Optional[Sequence[float]] = None) -> List[Dict[str, float]]:
        """Generate decision-impact metrics for a range of thresholds."""
        if thresholds is None:
            thresholds = np.linspace(0.1, 0.5, 9)
        else:
            thresholds = np.asarray(thresholds, dtype=np.float32)

        coverages_array = np.asarray(coverages, dtype=np.float32)
        labels_array = np.asarray(labels, dtype=bool)
        total = len(labels_array)
        if total == 0:
            return []

        results: List[Dict[str, float]] = []
        for threshold in thresholds:
            prithvi_selected = coverages_array < threshold
            ai4flood_selected = ~prithvi_selected

            correct = np.sum((prithvi_selected & labels_array) | (ai4flood_selected & ~labels_array))
            accuracy = correct / total
            prithvi_rate = np.sum(prithvi_selected) / total
            ai4flood_rate = np.sum(ai4flood_selected) / total

            results.append({
                "threshold": float(threshold),
                "accuracy": float(accuracy),
                "prithvi_rate": float(prithvi_rate),
                "ai4flood_rate": float(ai4flood_rate),
            })
        return results

    # ------------------------------------------------------------------
    # Cloud mask generation
    # ------------------------------------------------------------------
    def get_cloud_mask(self, image_path: str, *, brightness_threshold: float = 0.3, ndvi_threshold: float = 0.1) -> Optional[np.ndarray]:
        """Return a binary cloud mask derived from a Sentinel-2 GeoTIFF."""
        try:
            with rasterio.open(image_path) as src:
                band_count = src.count
                if band_count < 3:
                    return None
                blue = self._normalise(src.read(1))
                green = self._normalise(src.read(2))
                red = self._normalise(src.read(3))
                if band_count >= 4:
                    nir = self._normalise(src.read(4))
                    ndvi = (nir - red) / (nir + red + 1e-6)
                    ndvi_mask = ndvi < ndvi_threshold
                else:
                    ndvi_mask = np.ones_like(red, dtype=bool)
                brightness = (blue + green + red) / 3.0
                brightness_mask = brightness > brightness_threshold
                return (brightness_mask & ndvi_mask).astype(np.uint8)
        except Exception:
            return None

    @staticmethod
    def _normalise(band: np.ndarray) -> np.ndarray:
        band = band.astype(np.float32)
        max_value = np.nanmax(band)
        if max_value == 0:
            return band
        return band / max_value


__all__ = ["CloudAnalyzer", "CloudAnalysisResult"]
