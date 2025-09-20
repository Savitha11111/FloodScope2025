"""Compatibility shims exposing the legacy backend namespace."""

from llm.main_backend import main as run_cli  # noqa: F401

__all__ = ["run_cli"]
