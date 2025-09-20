# models/prithvi_transformers/model_loader.py

import os
from pathlib import Path

from transformers import AutoConfig, AutoModel, AutoProcessor

from llm import config as llm_config


_MODEL_ID = "ibm-nasa-geospatial/Prithvi-EO-1.0-100M"


def _candidate_paths():
    """Yield candidate local paths for the Prithvi checkpoint."""
    env_path = os.environ.get("PRITHVI_MODEL_PATH")
    if env_path:
        yield Path(env_path).expanduser()

    config_path = getattr(llm_config, "PRITHVI_MODEL_PATH", None)
    if config_path:
        yield Path(config_path).expanduser()


def _resolve_local_path():
    """Return the first existing directory that may contain local assets."""
    for path in _candidate_paths():
        if path.is_file():
            path = path.parent
        if path.is_dir():
            return str(path)
    return None


def load_prithvi_model():
    """Load the IBM-NASA Prithvi Model (Sentinel-2) using Transformers."""

    print("\n🚀 Loading IBM-NASA Prithvi Model (Sentinel-2) using Transformers...")

    local_path = _resolve_local_path()
    model_source = local_path or _MODEL_ID

    try:
        config = AutoConfig.from_pretrained(
            model_source,
            num_labels=2,
            id2label={0: "Non-Flooded", 1: "Flooded"},
            label2id={"Non-Flooded": 0, "Flooded": 1},
        )

        model = AutoModel.from_pretrained(model_source, config=config)
        processor = AutoProcessor.from_pretrained(model_source)
    except Exception as exc:
        location_msg = (
            f"local path '{local_path}'" if local_path else f"Hugging Face hub id '{_MODEL_ID}'"
        )
        raise RuntimeError(
            "Failed to load the IBM-NASA Prithvi model. "
            f"Attempted to use {location_msg}. "
            "Ensure the checkpoint exists locally or that the Hugging Face Hub is accessible."
        ) from exc

    print("✅ IBM-NASA Prithvi Model Loaded Successfully with num_labels = 2 (Binary Classification)")
    return model, processor
