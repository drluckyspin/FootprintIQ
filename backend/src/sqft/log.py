"""Central logging for the sqft pipeline (level from SQFT_LOG_LEVEL / Settings.log_level)."""

from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False


def configure_logging(level: str | None = None) -> None:
    """Configure the `sqft` logger tree; safe to call multiple times (updates level)."""
    global _CONFIGURED
    lvl_name = (level or os.environ.get("SQFT_LOG_LEVEL") or "INFO").upper()
    numeric = getattr(logging, lvl_name, logging.INFO)

    root = logging.getLogger("sqft")
    root.setLevel(numeric)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        root.addHandler(handler)
        root.propagate = False

    # HTTP client noise: show request lines only at DEBUG
    logging.getLogger("httpx").setLevel(logging.DEBUG if numeric <= logging.DEBUG else logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _CONFIGURED = True
    root.debug("logging configured level=%s", lvl_name)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"sqft.{name}")
