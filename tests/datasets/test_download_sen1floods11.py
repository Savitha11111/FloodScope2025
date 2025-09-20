import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import List

import requests

from datasets.download_sen1floods11 import (
    AuthenticationError,
    Credentials,
    IEEEDataPortDownloader,
)


class DummyResponse:
    def __init__(self, *, text="", headers=None, status_code=200, url="https://example.com") -> None:
        self.text = text
        self.headers = headers or {}
        self.status_code = status_code
        self.url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def iter_content(self, chunk_size=1024):
        yield b"dummy"

    def close(self) -> None:  # pragma: no cover - nothing to clean up
        pass


class DummySession:
    def __init__(self, responses: List[DummyResponse]):
        self._responses = responses
        self.cookies = requests.cookies.RequestsCookieJar()

    def get(self, url, *args, **kwargs):  # pylint: disable=unused-argument
        if not self._responses:
            raise AssertionError("No response queued for GET request")
        return self._responses.pop(0)

    def post(self, url, *args, **kwargs):  # pylint: disable=unused-argument
        return DummyResponse()


class DownloadSen1Floods11TestCase(unittest.TestCase):
    def test_requires_credentials_or_manual_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = IEEEDataPortDownloader(Path(tmpdir), Credentials())
            with self.assertRaises(AuthenticationError) as ctx:
                downloader.download()

        self.assertIn("manual", str(ctx.exception).lower())

    def test_rejects_html_response_when_not_authenticated(self) -> None:
        dataset_page = DummyResponse(
            text='<a href="/filedownload/download/123/Sen1Floods11.zip">Download</a>'
        )
        html_payload = DummyResponse(
            text="<html>login</html>", headers={"Content-Type": "text/html; charset=utf-8"}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = IEEEDataPortDownloader(
                Path(tmpdir), Credentials(username="user", password="pass")
            )
            downloader.session = DummySession([dataset_page, html_payload])

            with unittest.mock.patch.object(IEEEDataPortDownloader, "_login_with_credentials"):
                with self.assertRaises(AuthenticationError) as ctx:
                    downloader.download()

            self.assertIn("html", str(ctx.exception).lower())
            self.assertEqual(list(Path(tmpdir).iterdir()), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
