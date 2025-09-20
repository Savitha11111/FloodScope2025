"""Utility routines for AI4Flood SAR preprocessing."""
from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import numpy as np


def db_scale(image: np.ndarray, *, eps: float = 1e-6) -> np.ndarray:
    """Convert SAR backscatter to the decibel scale."""

    image = np.asarray(image, dtype=np.float32)
    return 10.0 * np.log10(np.clip(image, eps, None))


def pad_to_nearest(image: np.ndarray, block_size: int, fill_values: Sequence[float]) -> np.ndarray:
    """Pad ``image`` to the next multiple of ``block_size`` for tiling."""

    height, width = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    pad_h = (block_size - height % block_size) % block_size
    pad_w = (block_size - width % block_size) % block_size

    if pad_h == 0 and pad_w == 0:
        return image

    padded_shape = (height + pad_h, width + pad_w, channels)
    padded = np.zeros(padded_shape, dtype=image.dtype)

    fill_array = np.asarray(fill_values, dtype=image.dtype)
    if fill_array.size == 0:
        fill_array = np.zeros((channels,), dtype=image.dtype)
    if fill_array.size == 1:
        fill_array = np.repeat(fill_array, channels)

    for idx in range(channels):
        padded[..., idx] = fill_array[min(idx, fill_array.size - 1)]

    padded[:height, :width, ...] = image.reshape(height, width, channels)
    return padded


def create_patches(image: np.ndarray, patch_size: Tuple[int, int], stride: int) -> List[np.ndarray]:
    """Create channel-first patches from ``image``."""

    height, width = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    patch_h, patch_w = patch_size

    patches: List[np.ndarray] = []
    for y in range(0, height - patch_h + 1, stride):
        for x in range(0, width - patch_w + 1, stride):
            patch = image[y : y + patch_h, x : x + patch_w]
            patch = patch.reshape(patch_h, patch_w, channels)
            patch = np.transpose(patch, (2, 0, 1))
            patches.append(patch.astype(np.float32))
    return patches


def reconstruct_image_from_patches(
    patches: Iterable[np.ndarray],
    image_shape: Tuple[int, int],
    patch_size: Tuple[int, int],
    stride: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Reconstruct an image from overlapping patches using simple averaging."""

    height, width = image_shape
    patch_h, patch_w = patch_size
    accumulator = np.zeros((height, width), dtype=np.float32)
    counter = np.zeros((height, width), dtype=np.float32)

    idx = 0
    patches_list = list(patches)
    for y in range(0, height - patch_h + 1, stride):
        for x in range(0, width - patch_w + 1, stride):
            patch = np.asarray(patches_list[idx])
            if patch.ndim == 3:
                patch = patch[0]
            accumulator[y : y + patch_h, x : x + patch_w] += patch
            counter[y : y + patch_h, x : x + patch_w] += 1
            idx += 1

    np.divide(accumulator, counter, out=accumulator, where=counter > 0)
    return accumulator, counter


__all__ = [
    "db_scale",
    "pad_to_nearest",
    "create_patches",
    "reconstruct_image_from_patches",
]
