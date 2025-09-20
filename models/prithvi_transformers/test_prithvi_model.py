"""Integration smoke test for the Prithvi loader."""

import os
import pytest


if not os.getenv("PRITHVI_INTEGRATION_TESTS"):
    pytest.skip(
        "Set PRITHVI_INTEGRATION_TESTS=1 to run the heavyweight Prithvi integration test.",
        allow_module_level=True,
    )

from model_loader import load_prithvi_model


def test_prithvi_loader_downloads_checkpoint():
    model, processor = load_prithvi_model()
    assert model is not None
    assert processor is not None
