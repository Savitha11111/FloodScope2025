"""Minimal AI4Flood model loader used for inference."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import torch
from torch import nn


class _DoubleConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover - thin wrapper
        return self.net(x)


class SimpleUNet(nn.Module):
    """Compact UNet-style architecture compatible with AI4Flood checkpoints."""

    def __init__(self, in_channels: int, n_classes: int) -> None:
        super().__init__()
        self.enc1 = _DoubleConv(in_channels, 32)
        self.enc2 = _DoubleConv(32, 64)
        self.enc3 = _DoubleConv(64, 128)
        self.pool = nn.MaxPool2d(2)

        self.dec3 = _DoubleConv(128 + 64, 64)
        self.dec2 = _DoubleConv(64 + 32, 32)
        self.dec1 = nn.Conv2d(32, n_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover - architecture wrapper
        x1 = self.enc1(x)
        x2 = self.enc2(self.pool(x1))
        x3 = self.enc3(self.pool(x2))

        up2 = torch.nn.functional.interpolate(x3, scale_factor=2, mode="bilinear", align_corners=False)
        up2 = torch.cat([up2, x2], dim=1)
        up2 = self.dec3(up2)

        up1 = torch.nn.functional.interpolate(up2, scale_factor=2, mode="bilinear", align_corners=False)
        up1 = torch.cat([up1, x1], dim=1)
        up1 = self.dec2(up1)

        return self.dec1(up1)


def _resolve_state_dict(checkpoint_path: Path, device: torch.device) -> Tuple[dict, Path]:
    data = torch.load(checkpoint_path, map_location=device)
    if isinstance(data, dict):
        if "state_dict" in data:
            return data["state_dict"], checkpoint_path
        return data, checkpoint_path
    raise RuntimeError(f"Unsupported checkpoint format for {checkpoint_path}")


def load_model(
    checkpoint: str | Path,
    device: torch.device,
    *,
    in_channels: int = 2,
    n_classes: int = 2,
) -> nn.Module:
    """Load the AI4Flood segmentation network.

    Parameters
    ----------
    checkpoint:
        Path to the `.ckpt` file published by Microsoft AI4G.
    device:
        Torch device where the model will be instantiated.
    in_channels / n_classes:
        Model configuration parameters.
    """

    checkpoint_path = Path(checkpoint)
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            "AI4Flood checkpoint not found. Download the official weights from "
            "https://github.com/microsoft/ai4g-floods and place them at "
            f"{checkpoint_path}."
        )

    model = SimpleUNet(in_channels, n_classes)
    state_dict, _ = _resolve_state_dict(checkpoint_path, device)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        print(f"⚠️ Missing parameters when loading AI4Flood checkpoint: {sorted(missing)}")
    if unexpected:
        print(f"⚠️ Unexpected parameters when loading AI4Flood checkpoint: {sorted(unexpected)}")

    return model.to(device)


__all__ = ["load_model", "SimpleUNet"]
