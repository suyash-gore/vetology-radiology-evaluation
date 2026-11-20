"""Entry point: ``python -m week_07`` (with ``src`` on ``PYTHONPATH``)."""
import logging

from week_07.cli import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

raise SystemExit(main())
