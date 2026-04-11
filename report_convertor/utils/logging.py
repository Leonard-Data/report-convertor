"""Logging helpers for the CLI and future GUI diagnostics."""

from __future__ import annotations

import logging


def configure_logging(debug: bool = False) -> None:
    """Configure process-wide logging.

    Args:
        debug: When true, enable debug-level output.
    """

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
