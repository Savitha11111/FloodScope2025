import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from llm.cloud_coverage import CloudCoverageError, calculate_cloud_coverage
from llm.main_backend import check_cloud_coverage


def _write_geotiff(path, data):
    bands, height, width = data.shape
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": bands,
        "dtype": rasterio.float32,
        "transform": from_origin(0, 0, 10, 10),
        "crs": "EPSG:4326",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype(np.float32))


def test_calculate_cloud_coverage_returns_fraction(tmp_path):
    path = tmp_path / "cloudy.tif"
    base = np.zeros((4, 8, 8), dtype=np.float32)
    base[0, :4, :4] = 1.0  # blue
    base[1, :4, :4] = 1.0  # green
    base[2, :4, :4] = 1.0  # red
    base[3, :, :] = 0.2    # nir low so NDVI < threshold
    _write_geotiff(path, base)

    coverage = calculate_cloud_coverage(str(path))
    assert pytest.approx(coverage, rel=1e-3) == 0.25


def test_calculate_cloud_coverage_requires_three_bands(tmp_path):
    path = tmp_path / "invalid.tif"
    data = np.zeros((2, 8, 8), dtype=np.float32)
    _write_geotiff(path, data)

    with pytest.raises(CloudCoverageError):
        calculate_cloud_coverage(str(path))


def test_check_cloud_coverage_falls_back_on_error():
    def failing(_):
        raise CloudCoverageError("broken")

    is_clear, coverage = check_cloud_coverage("dummy", coverage_fn=failing, verbose=False)
    assert is_clear is False
    assert np.isnan(coverage)
