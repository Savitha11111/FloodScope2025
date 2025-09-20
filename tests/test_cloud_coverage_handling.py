import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.errors import RasterioIOError
import types

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LLM_ROOT = PROJECT_ROOT / "llm"
if str(LLM_ROOT) not in sys.path:
    sys.path.insert(0, str(LLM_ROOT))

from llm import cloud_coverage

# Provide lightweight stand-ins for heavy runtime dependencies expected by main_backend.
stub_ai4g = types.ModuleType("ai4g_inference")
stub_ai4g.run_ai4g_sar_inference = lambda *args, **kwargs: None
sys.modules.setdefault("ai4g_inference", stub_ai4g)

stub_data_fetcher = types.ModuleType("data_fetcher")
stub_data_fetcher.fetch_image = lambda *args, **kwargs: ""
sys.modules.setdefault("data_fetcher", stub_data_fetcher)

stub_model_inference = types.ModuleType("model_inference")
stub_model_inference.run_flood_detection = lambda *args, **kwargs: None
sys.modules.setdefault("model_inference", stub_model_inference)

stub_preprocess = types.ModuleType("preprocess")
stub_preprocess.preprocess_image = lambda *args, **kwargs: ""
sys.modules.setdefault("preprocess", stub_preprocess)

stub_geopy = types.ModuleType("geopy")
stub_geopy_geocoders = types.ModuleType("geopy.geocoders")


class _StubNominatim:
    def __init__(self, *args, **kwargs):
        pass

    def geocode(self, *args, **kwargs):  # pragma: no cover - not used in tests
        return None


stub_geopy_geocoders.Nominatim = _StubNominatim
stub_geopy.geocoders = stub_geopy_geocoders
sys.modules.setdefault("geopy", stub_geopy)
sys.modules.setdefault("geopy.geocoders", stub_geopy_geocoders)

from llm import main_backend


def write_tiff(path: Path, band_count: int, value: int = 1000) -> None:
    data = np.full((1, 1), value, dtype=np.uint16)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=1,
        height=1,
        count=band_count,
        dtype=data.dtype,
    ) as dst:
        for band in range(1, band_count + 1):
            dst.write(data, band)


def test_calculate_cloud_coverage_missing_band_raises(tmp_path):
    image_path = tmp_path / "partial_bands.tif"
    write_tiff(image_path, band_count=2)

    with pytest.raises(IndexError):
        cloud_coverage.calculate_cloud_coverage(str(image_path))


def test_calculate_cloud_coverage_missing_file_raises(tmp_path):
    missing_path = tmp_path / "does_not_exist.tif"

    with pytest.raises(RasterioIOError):
        cloud_coverage.calculate_cloud_coverage(str(missing_path))


def test_check_cloud_coverage_reports_failure(monkeypatch, caplog):
    def boom(path):
        raise RuntimeError("band data unavailable")

    monkeypatch.setattr(main_backend, "calculate_cloud_coverage", boom)
    caplog.set_level(logging.ERROR)

    status = main_backend.check_cloud_coverage("/tmp/fake.tif")

    assert status.error == "band data unavailable"
    assert status.coverage is None
    assert status.is_clear is None
    assert "Unable to determine cloud coverage" in caplog.text


def test_prepare_optical_imagery_switches_to_radar_on_failure(tmp_path):
    base_date = datetime(2024, 1, 3)

    fetched_paths = []

    def fake_fetch(lat, lon, date, sensor="Sentinel-2"):
        fetched_paths.append((sensor, date))
        image_path = tmp_path / f"{sensor}_{date}.tif"
        write_tiff(image_path, band_count=4)
        return str(image_path)

    def fake_preprocess(path, date_str):
        return f"processed_{date_str}"

    def failing_coverage(path):
        return main_backend.CloudCoverageStatus(coverage=None, is_clear=None, error="quality check failed")

    result = main_backend.prepare_optical_imagery(
        12.0,
        77.0,
        base_date,
        fetch_fn=fake_fetch,
        preprocess_fn=fake_preprocess,
        coverage_fn=failing_coverage,
    )

    assert result.use_sentinel1 is True
    assert result.preprocessed_images == []
    assert result.fallback_reason == "quality check failed"
    assert result.fallback_date == (base_date - timedelta(days=2)).strftime("%Y-%m-%d")
    assert fetched_paths == [("Sentinel-2", (base_date - timedelta(days=2)).strftime("%Y-%m-%d"))]
