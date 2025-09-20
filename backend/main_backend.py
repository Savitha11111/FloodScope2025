"""Compatibility entry point to preserve legacy script paths."""

from llm.main_backend import main


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    main()
