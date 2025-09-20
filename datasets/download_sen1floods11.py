"""Utility to download the Sen1Floods11 archive from IEEE DataPort."""
from __future__ import annotations

import argparse
import getpass
import logging
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://ieee-dataport.org"
LOGIN_URL = urljoin(BASE_URL, "/user/login")
DATASET_PAGE_URL = urljoin(BASE_URL, "/documents/sen1floods11")
DEFAULT_FILENAME = "Sen1Floods11.zip"
MANUAL_INSTRUCTIONS = (
    "Download Sen1Floods11.zip manually from IEEE DataPort after logging in and "
    "provide the path via --manual-archive. See https://ieee-dataport.org/documents/sen1floods11."
)


class AuthenticationError(RuntimeError):
    """Raised when authentication with IEEE DataPort fails."""


@dataclass
class Credentials:
    """Authentication credentials for IEEE DataPort."""

    username: Optional[str] = None
    password: Optional[str] = None
    session_cookie: Optional[str] = None

    def provided(self) -> bool:
        return bool(self.session_cookie or (self.username and self.password))


class IEEEDataPortDownloader:
    """Downloader for the Sen1Floods11 dataset."""

    def __init__(
        self,
        output_dir: Path,
        credentials: Credentials,
        manual_archive: Optional[Path] = None,
        overwrite: bool = False,
        timeout: int = 30,
    ) -> None:
        self.output_dir = output_dir
        self.credentials = credentials
        self.manual_archive = manual_archive
        self.overwrite = overwrite
        self.timeout = timeout
        self.session = requests.Session()

    def download(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.manual_archive:
            return self._handle_manual_archive()

        if not self.credentials.provided():
            raise AuthenticationError(
                "No IEEE DataPort credentials supplied. "
                f"{MANUAL_INSTRUCTIONS}"
            )

        self._authenticate()
        download_url = self._resolve_download_url()
        archive_name = self._guess_archive_name(download_url)
        destination = self.output_dir / archive_name

        if destination.exists() and not self.overwrite:
            LOGGER.info("Archive %s already exists, skipping download", destination)
            return destination

        self._download_archive(download_url, destination)
        return destination

    # ------------------------------------------------------------------
    # Authentication and URL resolution helpers
    def _authenticate(self) -> None:
        if self.credentials.session_cookie:
            LOGGER.debug("Using existing IEEE DataPort session cookie")
            self._set_session_cookie(self.credentials.session_cookie)
            return

        if self.credentials.username and self.credentials.password:
            self._login_with_credentials()
            return

        raise AuthenticationError(
            "Insufficient credentials. Provide username/password or a session cookie."
        )

    def _login_with_credentials(self) -> None:
        LOGGER.info("Logging into IEEE DataPort as %s", self.credentials.username)
        login_page = self.session.get(LOGIN_URL, timeout=self.timeout)
        login_page.raise_for_status()

        form_data = self._extract_login_form(login_page.text)
        if not form_data:
            raise AuthenticationError(
                "Could not find login form on IEEE DataPort login page. "
                f"{MANUAL_INSTRUCTIONS}"
            )

        form_data.update(
            {
                "name": self.credentials.username,
                "pass": self.credentials.password,
            }
        )

        response = self.session.post(LOGIN_URL, data=form_data, timeout=self.timeout)
        response.raise_for_status()

        # Successful login redirects away from the login page. If we still
        # see the login form we probably failed.
        if "user/login" in response.url:
            raise AuthenticationError(
                "IEEE DataPort login failed. Verify credentials or use --session-cookie."
            )

    def _set_session_cookie(self, cookie_spec: str) -> None:
        value = cookie_spec.strip()
        if "=" in value:
            name, cookie_value = value.split("=", 1)
        else:
            name, cookie_value = "SESS", value

        domain = urlparse(BASE_URL).hostname
        if not domain:
            raise AuthenticationError("Could not determine IEEE DataPort cookie domain")

        self.session.cookies.set(name.strip(), cookie_value.strip(), domain=domain, path="/")

    def _extract_login_form(self, html: str) -> Optional[dict[str, str]]:
        token_pattern = re.compile(
            r'<input[^>]+name="(form_build_id|form_id|form_token)"[^>]+value="([^"]+)"',
            re.IGNORECASE,
        )

        form_data: dict[str, str] = {"op": "Log in"}
        for match in token_pattern.finditer(html):
            name, value = match.groups()
            form_data[name] = value

        if "form_id" not in form_data:
            return None
        return form_data

    def _resolve_download_url(self) -> str:
        LOGGER.info("Resolving Sen1Floods11 download URL")
        response = self.session.get(DATASET_PAGE_URL, timeout=self.timeout)
        response.raise_for_status()

        match = re.search(r'href="(/filedownload/[^\"]+Sen1Floods11[^\"]+)"', response.text)
        if not match:
            raise AuthenticationError(
                "Could not locate the Sen1Floods11 download link. "
                "Ensure that your session is authenticated."
            )

        relative_url = match.group(1)
        return urljoin(BASE_URL, relative_url)

    def _guess_archive_name(self, download_url: str) -> str:
        parsed = urlparse(download_url)
        filename = os.path.basename(parsed.path)
        if filename:
            return filename
        return DEFAULT_FILENAME

    # ------------------------------------------------------------------
    # Download helpers
    def _download_archive(self, url: str, destination: Path) -> None:
        LOGGER.info("Downloading Sen1Floods11 from %s", url)
        response = self.session.get(url, stream=True, timeout=self.timeout)
        try:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                raise AuthenticationError(
                    "Received HTML instead of the dataset archive. "
                    "Authentication likely failed."
                )

            with destination.open("wb") as file_obj:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file_obj.write(chunk)
        finally:
            response.close()

    def _handle_manual_archive(self) -> Path:
        source = self.manual_archive
        if not source or not source.exists():
            raise FileNotFoundError(
                f"Manual archive {source} does not exist. {MANUAL_INSTRUCTIONS}"
            )

        destination = self.output_dir / source.name
        if destination.exists() and not self.overwrite:
            LOGGER.info("Archive %s already exists, skipping copy", destination)
            return destination

        LOGGER.info("Copying manual archive from %s to %s", source, destination)
        shutil.copyfile(source, destination)
        return destination


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Directory to place the downloaded archive")
    parser.add_argument("--username", help="IEEE DataPort username")
    parser.add_argument("--password", help="IEEE DataPort password")
    parser.add_argument(
        "--session-cookie",
        help="Existing IEEE DataPort session cookie value (e.g. the SESS... cookie)",
    )
    parser.add_argument(
        "--manual-archive",
        type=Path,
        help="Path to a manually downloaded Sen1Floods11 archive",
    )
    parser.add_argument(
        "--prompt-password",
        action="store_true",
        help="Prompt for the password instead of supplying --password",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the archive if it already exists",
    )
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args(argv)

    password = args.password
    if args.prompt_password and not password:
        password = getpass.getpass("IEEE DataPort password: ")

    credentials = Credentials(
        username=args.username,
        password=password,
        session_cookie=args.session_cookie,
    )

    downloader = IEEEDataPortDownloader(
        output_dir=args.output,
        credentials=credentials,
        manual_archive=args.manual_archive,
        overwrite=args.overwrite,
        timeout=args.timeout,
    )

    try:
        destination = downloader.download()
    except AuthenticationError as exc:
        LOGGER.error("%s", exc)
        LOGGER.error(MANUAL_INSTRUCTIONS)
        return 1
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.error("Download failed: %s", exc)
        return 1

    LOGGER.info("Archive stored at %s", destination)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
