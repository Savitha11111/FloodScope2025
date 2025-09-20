"""Tests for the Prithvi model loader."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.prithvi_transformers import model_loader


@pytest.fixture()
def local_checkpoint_dir(tmp_path: Path) -> Path:
    """Create a minimal local checkpoint directory structure."""

    model_dir = tmp_path / "model"
    processor_dir = tmp_path / "processor"
    model_dir.mkdir()
    processor_dir.mkdir()

    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    (model_dir / "pytorch_model.bin").write_bytes(b"")
    (processor_dir / "preprocessor_config.json").write_text("{}", encoding="utf-8")

    return tmp_path


def test_load_prithvi_model_prefers_local_checkpoint(monkeypatch, local_checkpoint_dir: Path):
    """Ensure that a local checkpoint is used without attempting a network load."""

    monkeypatch.setenv("PRITHVI_MODEL_PATH", str(local_checkpoint_dir))

    model_stub = object()
    processor_stub = object()

    with (
        mock.patch(
            "models.prithvi_transformers.model_loader.AutoModelForSemanticSegmentation.from_pretrained",
            return_value=model_stub,
        ) as mock_model,
        mock.patch(
            "models.prithvi_transformers.model_loader.AutoProcessor.from_pretrained",
            return_value=processor_stub,
        ) as mock_processor,
        mock.patch(
            "models.prithvi_transformers.model_loader.AutoConfig.from_pretrained",
        ) as mock_config,
    ):
        model, processor = model_loader.load_prithvi_model()

    model_dir = local_checkpoint_dir / "model"
    processor_dir = local_checkpoint_dir / "processor"

    assert model is model_stub
    assert processor is processor_stub
    mock_model.assert_called_once_with(str(model_dir))
    mock_processor.assert_called_once_with(str(processor_dir))
    mock_config.assert_not_called()
