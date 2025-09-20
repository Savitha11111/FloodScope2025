import numpy as np
import pytest
import rasterio
import torch
from rasterio.transform import from_origin

from backend.model_inference import run_flood_detection


class DummyProcessor:
    def __call__(self, *, images, return_tensors="pt"):
        array = np.asarray(images, dtype=np.float32)
        if array.ndim == 3:
            array = array[np.newaxis, ...]
        pixel_values = torch.from_numpy(np.transpose(array, (0, 3, 1, 2)))
        return {"pixel_values": pixel_values}


class DummyModel(torch.nn.Module):
    def forward(self, pixel_values):  # pragma: no cover - exercised via tests
        batch, _, height, width = pixel_values.shape
        logits = torch.zeros((batch, 2, height, width), dtype=torch.float32)
        logits[:, 1] = 1.0
        return type("Output", (), {"logits": logits})()


@pytest.fixture(autouse=True)
def patch_model_loader(monkeypatch):
    from llm import model_inference as inference_module

    def fake_loader():
        return DummyModel(), DummyProcessor()

    monkeypatch.setattr("models.prithvi_transformers.model_loader.load_prithvi_model", fake_loader)
    monkeypatch.setattr("llm.model_inference.load_prithvi_model", fake_loader)
    inference_module._MODEL_CACHE = None
    yield
    inference_module._MODEL_CACHE = None


def _write_test_geotiff(path, *, bands=3):
    data = np.random.rand(bands, 16, 16).astype(np.float32)
    profile = {
        "driver": "GTiff",
        "height": 16,
        "width": 16,
        "count": bands,
        "dtype": rasterio.float32,
        "transform": from_origin(0, 0, 10, 10),
        "crs": "EPSG:4326",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data)


def test_run_flood_detection_creates_mask(tmp_path, monkeypatch):
    image_path = tmp_path / "scene.tif"
    _write_test_geotiff(image_path)

    results_dir = tmp_path / "results"
    outputs = run_flood_detection([str(image_path)], results_dir=results_dir)

    assert len(outputs) == 1
    assert outputs[0].exists()

    with rasterio.open(outputs[0]) as src:
        data = src.read(1)
        assert data.shape == (16, 16)
        assert np.all((data == 0) | (data == 1))


def test_run_flood_detection_requires_three_bands(tmp_path):
    image_path = tmp_path / "invalid.tif"
    _write_test_geotiff(image_path, bands=2)

    with pytest.raises(ValueError):
        run_flood_detection([str(image_path)], results_dir=tmp_path / "results")


def test_run_flood_detection_handles_missing_images(tmp_path):
    missing_path = tmp_path / "missing.tif"
    with pytest.raises(FileNotFoundError):
        run_flood_detection([str(missing_path)], results_dir=tmp_path / "results")
