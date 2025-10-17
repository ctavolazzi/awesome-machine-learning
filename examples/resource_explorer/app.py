"""Command-line entry point for the resource explorer example project."""
from __future__ import annotations

import logging
import sys
from typing import Sequence

from . import dashboard, resource_loader, visualize

LOGGER = logging.getLogger(__name__)


def _configure_logging(verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


def _split_verbose_flag(argv: Sequence[str] | None) -> tuple[list[str], bool]:
    if not argv:
        return [], False

    verbose = False
    cleaned: list[str] = []
    for token in argv:
        if token == "--verbose":
            verbose = True
            continue
        cleaned.append(token)
    return cleaned, verbose


def main(argv: Sequence[str] | None = None) -> int:
    """Route to the appropriate sub-command (browse, dashboard, chart)."""

    raw_args = list(argv) if argv is not None else sys.argv[1:]
    cleaned_args, verbose = _split_verbose_flag(raw_args)
    _configure_logging(verbose)

    if not cleaned_args:
        LOGGER.info("Defaulting to browse mode")
        return resource_loader.main([])

    command, *remaining = cleaned_args

    if command == "browse":
        LOGGER.info("Running browse subcommand")
        return resource_loader.main(remaining)
    if command == "dashboard":
        LOGGER.info("Running dashboard subcommand")
        return dashboard.main(remaining)
    if command == "chart":
        LOGGER.info("Running chart subcommand")
        return visualize.main(remaining)

    # No explicit sub-command; treat the entire argument list as browse options.
    LOGGER.info("No recognized subcommand; invoking browse mode")
    return resource_loader.main(cleaned_args)


if __name__ == "__main__":  # pragma: no cover - manual invocation entry point
    raise SystemExit(main())
