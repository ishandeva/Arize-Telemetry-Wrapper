"""Opt-in logging support; importing this library never configures handlers."""

from __future__ import annotations

import logging


def configure_default_logging(level: int = logging.INFO) -> None:
    """Configure basic logging only when the application has no setup of its own."""
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
