"""Shared logging helpers for avantgarde-vvd scripts."""
from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logging(name: str = "avantgarde-vvd", verbose: bool = True) -> logging.Logger:
    """Configure a console logger. Verbose (default) = DEBUG, else INFO."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s  %(levelname)-7s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


def log_path(logger: logging.Logger, label: str, path: str, level: int = logging.DEBUG) -> None:
    """Log whether a path exists and its size."""
    import os

    if os.path.isfile(path):
        size = os.path.getsize(path)
        logger.log(level, "%s: %s  (%s bytes)", label, path, f"{size:,}")
    elif os.path.isdir(path):
        n = len(os.listdir(path))
        logger.log(level, "%s: %s  (directory, %d entries)", label, path, n)
    else:
        logger.log(level, "%s: %s  (MISSING)", label, path)
