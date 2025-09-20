"""Utility helpers for streaming downloads, checksum validation, and provenance logging."""
from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime
from typing import Iterable, Optional

import requests

CHUNK_SIZE = 1 << 20  # 1 MiB


def _ensure_directory(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def stream_download(url: str, destination: pathlib.Path, token: Optional[str] = None) -> pathlib.Path:
    """Stream a file from ``url`` to ``destination``.

    Parameters
    ----------
    url:
        HTTP(S) url to download.
    destination:
        Path where the file will be written.
    token:
        Optional bearer/API token for authenticated resources.

    Returns
    -------
    pathlib.Path
        The destination path where the file was written.
    """
    headers = {"User-Agent": "FloodScope2025/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with requests.get(url, headers=headers, stream=True, timeout=60) as response:
        response.raise_for_status()
        _ensure_directory(destination.parent)
        with destination.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    fh.write(chunk)
    return destination


def sha256_checksum(path: pathlib.Path, chunk_size: int = CHUNK_SIZE) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log_provenance(dataset_root: pathlib.Path, *, source_url: str, checksum: str, artifacts: Iterable[pathlib.Path]) -> None:
    metadata_dir = dataset_root / "metadata"
    _ensure_directory(metadata_dir)

    log_entry = {
        "source_url": source_url,
        "checksum": checksum,
        "artifacts": [str(p.relative_to(dataset_root)) for p in artifacts],
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds"),
    }

    history_file = metadata_dir / "download_log.jsonl"
    with history_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(log_entry) + "\n")


def record_license(dataset_root: pathlib.Path, license_text: str) -> None:
    metadata_dir = dataset_root / "metadata"
    _ensure_directory(metadata_dir)

    license_file = metadata_dir / "LICENSES.md"
    with license_file.open("a", encoding="utf-8") as fh:
        fh.write("\n" + license_text.strip() + "\n")


__all__ = [
    "stream_download",
    "sha256_checksum",
    "log_provenance",
    "record_license",
]
