"""Downloader for the FloodNet dataset."""
from __future__ import annotations

import argparse
import pathlib
import shutil
import zipfile
from typing import Optional

from datasets.download_utils import log_provenance, record_license, sha256_checksum, stream_download

DEFAULT_URL = "https://floodnet.ai/data/FloodNet_Release.zip"
LICENSE_TEXT = """FloodNet Dataset\nRahnemoonfar et al. (2021)\nProvided for research use in accordance with the FloodNet terms of service."""


def _extract_zip(archive_path: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(destination)
    return destination


def download_dataset(output_root: pathlib.Path, *, url: Optional[str], manual_archive: Optional[pathlib.Path], token: Optional[str]) -> pathlib.Path:
    raw_dir = output_root / "raw"
    interim_dir = output_root / "interim"
    raw_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)

    if manual_archive:
        archive_path = manual_archive.resolve()
        if not archive_path.exists():
            raise FileNotFoundError(f"Manual archive not found: {archive_path}")
        staged_archive = raw_dir / archive_path.name
        if archive_path != staged_archive:
            shutil.copy2(archive_path, staged_archive)
    else:
        if not url:
            raise ValueError("A download URL is required when --manual-archive is not supplied.")
        archive_filename = url.split("/")[-1] or "FloodNet.zip"
        staged_archive = raw_dir / archive_filename
        stream_download(url, staged_archive, token=token)

    checksum = sha256_checksum(staged_archive)
    extracted = _extract_zip(staged_archive, interim_dir)
    log_provenance(output_root, source_url=url or f"manual:{manual_archive}", checksum=checksum, artifacts=[staged_archive, extracted])
    record_license(output_root, LICENSE_TEXT)
    return staged_archive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download the FloodNet dataset")
    parser.add_argument("--output-root", type=pathlib.Path, required=True)
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Override the default download URL")
    parser.add_argument("--manual-archive", type=pathlib.Path, default=None, help="Path to a pre-downloaded archive")
    parser.add_argument("--token", type=str, default=None, help="Optional bearer token for authenticated downloads")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    download_dataset(args.output_root, url=args.url, manual_archive=args.manual_archive, token=args.token)
    print("FloodNet download finished. Proceed with datasets/processing/floodnet.py for harmonisation.")


if __name__ == "__main__":
    main()
