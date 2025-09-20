"""Downloader for the Sen1Floods11 benchmark dataset."""
from __future__ import annotations

import argparse
import pathlib
import shutil
import tarfile
import zipfile
from typing import Optional

from datasets.download_utils import log_provenance, record_license, sha256_checksum, stream_download

# The IEEE DataPort landing page requires an authenticated browser session and
# does not expose a stable direct download URL. The downloader therefore
# defaults to ``None`` and insists on either a user-supplied asset link or a
# manually downloaded archive so that we never persist the HTML landing page by
# accident.
DEFAULT_URL: Optional[str] = None
LICENSE_TEXT = """Sen1Floods11 \nBonafilia et al. (2020)\nLicensed for research use under the IEEE DataPort terms of use."""


def _extract_archive(archive_path: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    destination.mkdir(parents=True, exist_ok=True)
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(destination)
    elif archive_path.suffixes[-2:] == [".tar", ".gz"] or archive_path.suffix == ".tgz":
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extractall(destination)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
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
            raise ValueError(
                "Sen1Floods11 requires either --manual-archive pointing to the "
                "official download or --url set to a direct asset link obtained "
                "after logging into IEEE DataPort."
            )
        if url.rstrip("/") == "https://ieee-dataport.org/documents/sen1floods11":
            raise ValueError(
                "The IEEE DataPort landing page cannot be downloaded directly. "
                "Please log in, copy the actual archive link (usually ending in "
                "'.zip'), or download the file manually and pass it via --manual-archive."
            )
        archive_filename = url.split("/")[-1] or "sen1floods11.zip"
        staged_archive = raw_dir / archive_filename
        stream_download(url, staged_archive, token=token)

    checksum = sha256_checksum(staged_archive)
    extracted = _extract_archive(staged_archive, interim_dir)
    log_provenance(output_root, source_url=url or f"manual:{manual_archive}", checksum=checksum, artifacts=[staged_archive, extracted])
    record_license(output_root, LICENSE_TEXT)
    return staged_archive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download the Sen1Floods11 dataset")
    parser.add_argument("--output-root", type=pathlib.Path, required=True, help="Directory where the dataset should be stored")
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_URL,
        help=(
            "Direct Sen1Floods11 asset URL obtained after logging into IEEE DataPort. "
            "Leave unset when supplying --manual-archive."
        ),
    )
    parser.add_argument(
        "--manual-archive",
        type=pathlib.Path,
        default=None,
        help="Path to a pre-downloaded Sen1Floods11 archive",
    )
    parser.add_argument("--token", type=str, default=None, help="Optional API token for authenticated downloads")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    download_dataset(args.output_root, url=args.url, manual_archive=args.manual_archive, token=args.token)
    print("Sen1Floods11 download finished. Proceed with datasets/processing/sen1floods11.py to harmonise the chips.")


if __name__ == "__main__":
    main()
