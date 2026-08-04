"""Shared logging helpers for avantgarde-vvd scripts."""
from __future__ import annotations

import logging
import os
import sys


# Softer labels than raw DEBUG / INFO / WARNING / ERROR
_FRIENDLY_LEVELS = {
    logging.DEBUG: "detail",
    logging.INFO: "info",
    logging.WARNING: "note",
    logging.ERROR: "problem",
    logging.CRITICAL: "problem",
}


class FriendlyFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = record.levelname
        record.levelname = _FRIENDLY_LEVELS.get(record.levelno, original.lower())
        try:
            return super().format(record)
        finally:
            record.levelname = original


def setup_logging(name: str = "avantgarde-vvd", verbose: bool = False) -> logging.Logger:
    """Configure a console logger. Default = INFO; pass verbose=True for DETAIL."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # Prefer UTF-8 on Windows consoles so messages don't crash on symbols.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        FriendlyFormatter(
            fmt="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


def set_verbose(logger: logging.Logger, verbose: bool) -> None:
    """Turn detail (DEBUG) logging on or off after setup."""
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def log_path(logger: logging.Logger, label: str, path: str, level: int = logging.DEBUG) -> None:
    """Describe a path in plain English (exists / size / missing)."""
    if os.path.isfile(path):
        size = os.path.getsize(path)
        logger.log(
            level,
            "%s found at %s (%s bytes).",
            label.capitalize() if label[:1].islower() else label,
            path,
            f"{size:,}",
        )
    elif os.path.isdir(path):
        n = len(os.listdir(path))
        logger.log(
            level,
            "%s is the folder %s (%d item%s inside).",
            label.capitalize() if label[:1].islower() else label,
            path,
            n,
            "" if n == 1 else "s",
        )
    else:
        logger.log(level, "%s is not there yet: %s", label, path)
