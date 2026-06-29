"""Demo seed: load a curated historical window so the dashboard is full of signal on
first launch (PLAN.md Phase 11). Run with `make seed` or `python -m server.seed`."""

from server.seed.loader import seed

__all__ = ["seed"]
