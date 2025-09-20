# models/prithvi_transformers/model_loader.py

"""Utilities for loading the IBM-NASA Prithvi model and processor."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from transformers import AutoConfig, AutoModelForSemanticSegmentation, AutoProcessor


_DEFAULT_MODEL_ID = "ibm-nasa-geospatial/Prithvi-EO-1.0-100M"
_ENV_VAR = "PRITHVI_MODEL_PATH"
_MODEL_SUBDIR = "model"
_PROCESSOR_SUBDIR = "processor"
_REQUIRED_MODEL_FILES = ("config.json",)
_REQUIRED_PROCESSOR_FILES = ("preprocessor_config.json",)
_MODEL_WEIGHT_FILES = ("pytorch_model.bin", "model.safetensors")


def _describe_expected_layout(root: Path) -> str:
    """Return a human-readable description of the expected checkpoint layout."""

    model_dir = root / _MODEL_SUBDIR
    processor_dir = root / _PROCESSOR_SUBDIR
    weight_options = " or ".join(_MODEL_WEIGHT_FILES)
    return (
        "Expected `{env}` to point to a directory structured as:\n"
        "  {root}/model/config.json\n"
        "  {root}/model/{{{weight_options}}}\n"
        "  {root}/processor/preprocessor_config.json"
    ).format(env=_ENV_VAR, root=root, weight_options=weight_options)


def _validate_local_checkpoint(root: Path) -> Tuple[Path, Path]:
    """Validate that the checkpoint directory contains the expected files."""

    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(
            f"`{_ENV_VAR}` is set to {root!s}, but that directory does not exist. "
            + _describe_expected_layout(root)
        )

    model_dir = root / _MODEL_SUBDIR
    processor_dir = root / _PROCESSOR_SUBDIR

    missing_paths = []

    if not model_dir.is_dir():
        missing_paths.append(f"{model_dir}/")
    else:
        for filename in _REQUIRED_MODEL_FILES:
            if not (model_dir / filename).is_file():
                missing_paths.append(str(model_dir / filename))
        if not any((model_dir / weight).is_file() for weight in _MODEL_WEIGHT_FILES):
            missing_paths.append(
                " or ".join(str(model_dir / weight) for weight in _MODEL_WEIGHT_FILES)
            )

    if not processor_dir.is_dir():
        missing_paths.append(f"{processor_dir}/")
    else:
        for filename in _REQUIRED_PROCESSOR_FILES:
            if not (processor_dir / filename).is_file():
                missing_paths.append(str(processor_dir / filename))

    if missing_paths:
        message = (
            "Unable to load local Prithvi checkpoint because the following expected "
            f"paths were not found: {', '.join(missing_paths)}. "
        ) + _describe_expected_layout(root)
        raise ValueError(message)

    return model_dir, processor_dir


def load_prithvi_model():
    """Load the IBM-NASA Prithvi model and processor."""

    print("\n🚀 Loading IBM-NASA Prithvi Model (Sentinel-2) using Transformers...")

    local_root = os.environ.get(_ENV_VAR)
    if local_root:
        root_path = Path(local_root)
        model_dir, processor_dir = _validate_local_checkpoint(root_path)
        model = AutoModelForSemanticSegmentation.from_pretrained(str(model_dir))
        processor = AutoProcessor.from_pretrained(str(processor_dir))
        print(
            "✅ IBM-NASA Prithvi Model Loaded Successfully from local checkpoint with "
            "num_labels = 2 (Binary Classification)"
        )
        return model, processor

    config = AutoConfig.from_pretrained(
        _DEFAULT_MODEL_ID,
        num_labels=2,
        id2label={0: "Non-Flooded", 1: "Flooded"},
        label2id={"Non-Flooded": 0, "Flooded": 1},
    )

    model = AutoModelForSemanticSegmentation.from_pretrained(_DEFAULT_MODEL_ID, config=config)
    processor = AutoProcessor.from_pretrained(_DEFAULT_MODEL_ID)

    print(
        "✅ IBM-NASA Prithvi Model Loaded Successfully from Hugging Face Hub with "
        "num_labels = 2 (Binary Classification)"
    )
    return model, processor
