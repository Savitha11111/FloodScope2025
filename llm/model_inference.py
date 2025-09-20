"""Prithvi flood inference utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
import rasterio
import torch

from .config import RESULTS_DIR
from models.prithvi_transformers.model_loader import load_prithvi_model


@dataclass
class _ModelBundle:
    model: torch.nn.Module
    processor: object
    device: torch.device


_MODEL_CACHE: _ModelBundle | None = None


def _ensure_model() -> _ModelBundle:
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        model, processor = load_prithvi_model()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        model.eval()
        _MODEL_CACHE = _ModelBundle(model=model, processor=processor, device=device)
    return _MODEL_CACHE


def _read_rgb(image_path: str) -> Tuple[np.ndarray, dict]:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Sentinel-2 image not found: {image_path}")

    with rasterio.open(path) as src:
        if src.count < 3:
            raise ValueError("Prithvi inference expects at least three Sentinel-2 bands (B02-B04).")
        rgb = src.read([1, 2, 3])  # (3, H, W)
        profile = src.profile

    rgb = np.transpose(rgb, (1, 2, 0))  # (H, W, 3)
    rgb = rgb.astype(np.float32)
    if rgb.max() > 1.0:
        rgb /= 10000.0
    return rgb, profile


def _write_mask(mask: np.ndarray, profile: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    output_profile = profile.copy()
    output_profile.update(count=1, dtype=rasterio.uint8, nodata=0)
    with rasterio.open(destination, "w", **output_profile) as dst:
        dst.write(mask.astype(rasterio.uint8), 1)


def run_flood_detection(image_paths: Iterable[str], *, results_dir: str | os.PathLike[str] = RESULTS_DIR) -> List[Path]:
    """Run the Prithvi model on the provided Sentinel-2 chips.

    Parameters
    ----------
    image_paths:
        Iterable of Sentinel-2 GeoTIFF paths.
    results_dir:
        Directory where prediction rasters are stored.

    Returns
    -------
    List[pathlib.Path]
        Paths to the generated flood masks.
    """

    bundle = _ensure_model()
    model = bundle.model
    processor = bundle.processor
    device = bundle.device

    outputs: List[Path] = []
    for image_path in image_paths:
        rgb, profile = _read_rgb(image_path)

        processed = processor(images=rgb, return_tensors="pt")
        if "pixel_values" not in processed:
            raise RuntimeError("Prithvi processor did not return pixel_values for inference")

        pixel_values = processed["pixel_values"].to(device)

        with torch.no_grad():
            prediction = model(pixel_values=pixel_values)

        logits = getattr(prediction, "logits", None)
        if logits is None:
            raise RuntimeError(
                "Prithvi model output does not expose logits. Ensure the segmentation checkpoint is used."
            )

        mask = torch.argmax(logits, dim=1).cpu().numpy()[0].astype(np.uint8)

        output_dir = Path(results_dir)
        output_path = output_dir / f"{Path(image_path).stem}_prithvi_mask.tif"
        _write_mask(mask, profile, output_path)
        outputs.append(output_path)
        print(f"✅ Saved Prithvi flood mask to {output_path}")

    if not outputs:
        print("⚠️ No Sentinel-2 scenes supplied to Prithvi inference.")

    return outputs


__all__ = ["run_flood_detection"]
