"""Downloader for Copernicus EMS flood mapping products."""
from __future__ import annotations

import argparse
import pathlib
import shutil
import zipfile
from typing import Optional

from datasets.download_utils import log_provenance, record_license, sha256_checksum, stream_download

DEFAULT_URL = None
LICENSE_TEXT = """Copernicus Emergency Management Service (EMS) mapping products.\nUsage subject to the Copernicus EMS licence (https://emergency.copernicus.eu/mapping/ems/cite-ems-products)."""


def _extract_zip(archive_path: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(destination)
    return destination


def download_dataset(output_root: pathlib.Path, *, event_id: str, url: Optional[str], manual_archive: Optional[pathlib.Path], token: Optional[str]) -> pathlib.Path:
    raw_dir = output_root / "raw" / event_id
    interim_dir = output_root / "interim" / event_id
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
            raise ValueError("A direct download URL is required when --manual-archive is not supplied for Copernicus EMS events.")
        archive_filename = url.split("/")[-1] or f"{event_id}.zip"
        staged_archive = raw_dir / archive_filename
        stream_download(url, staged_archive, token=token)

    checksum = sha256_checksum(staged_archive)
    extracted = _extract_zip(staged_archive, interim_dir)
    source = url if url else f"manual:{manual_archive}"
    log_provenance(output_root, source_url=source, checksum=checksum, artifacts=[staged_archive, extracted])
    record_license(output_root, LICENSE_TEXT)
    return staged_archive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Copernicus EMS flood maps")
    parser.add_argument("--event-id", required=True, help="Copernicus EMSR event identifier (e.g., EMSR452)")
    parser.add_argument("--output-root", type=pathlib.Path, required=True)
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Optional direct download URL override")
    parser.add_argument("--manual-archive", type=pathlib.Path, default=None, help="Use a previously downloaded archive")
    parser.add_argument("--token", type=str, default=None, help="Optional bearer token for authenticated downloads")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    download_dataset(args.output_root, event_id=args.event_id, url=args.url, manual_archive=args.manual_archive, token=args.token)
    print(f"Copernicus EMS event {args.event_id} downloaded. Run datasets/processing/copernicus_ems.py to harmonise the products.")


if __name__ == "__main__":
    main()
