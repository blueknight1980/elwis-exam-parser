"""Logging setup for the command-line interface."""

from __future__ import annotations

import logging


def configure_logging(*, verbose: bool, quiet: bool) -> None:
    """Configure the ``elwis_parser`` logger for one process."""
    if verbose and quiet:
        level = logging.INFO
    elif verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )
