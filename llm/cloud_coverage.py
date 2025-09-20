"""Cloud coverage estimation utilities."""
from __future__ import annotations

import numpy as np
import rasterio


DEFAULT_BRIGHTNESS_THRESHOLD = 0.3
DEFAULT_NDVI_THRESHOLD = 0.1


class CloudCoverageError(RuntimeError):
    """Raised when cloud coverage cannot be computed for a scene."""


def _normalise_band(band: np.ndarray) -> np.ndarray:
    band = band.astype(np.float32)
    max_value = np.nanmax(band)
    if max_value == 0:
        return band
    return band / max_value


def calculate_cloud_coverage(
    image_path: str,
    *,
    brightness_threshold: float = DEFAULT_BRIGHTNESS_THRESHOLD,
    ndvi_threshold: float = DEFAULT_NDVI_THRESHOLD,
) -> float:
    """Estimate the fraction of cloudy pixels in a multi-band GeoTIFF.

    The function attempts to read blue, green, red, and near-infrared bands. If the
    near-infrared band is missing (common for aerial datasets such as FloodNet), a
    fallback brightness-only heuristic is used.
    """
    try:
        with rasterio.open(image_path) as src:
            band_count = src.count
            if band_count < 3:
                raise CloudCoverageError(
                    "Cloud coverage estimation requires at least three optical bands (B02-B04)."
                )

            blue = _normalise_band(src.read(1))
            green = _normalise_band(src.read(2))
            red = _normalise_band(src.read(3))

            if band_count >= 4:
                nir = _normalise_band(src.read(4))
                ndvi = (nir - red) / (nir + red + 1e-6)
            else:
                ndvi = None

            brightness = (blue + green + red) / 3.0
            bright_mask = brightness > brightness_threshold

            if ndvi is not None:
                ndvi_mask = ndvi < ndvi_threshold
                cloud_mask = bright_mask & ndvi_mask
            else:
                cloud_mask = bright_mask

            total_pixels = cloud_mask.size
            if total_pixels == 0:
                raise CloudCoverageError("Empty raster provided for cloud coverage computation.")

            cloud_pixels = np.sum(cloud_mask)
            coverage = float(cloud_pixels / total_pixels)
            if not np.isfinite(coverage):
                raise CloudCoverageError("Computed non-finite cloud coverage value.")
            return coverage
    except CloudCoverageError:
        raise
    except Exception as exc:
        raise CloudCoverageError(f"Failed to calculate cloud coverage for {image_path}: {exc}") from exc


def cloud_percentage(image_path: str, **kwargs) -> float:
    """Return cloud coverage as a percentage (0-100)."""
    return calculate_cloud_coverage(image_path, **kwargs) * 100.0


__all__ = ["calculate_cloud_coverage", "cloud_percentage", "CloudCoverageError"]
