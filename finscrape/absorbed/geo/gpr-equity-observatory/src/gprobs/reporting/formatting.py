import pandas as pd


def _is_missing(value: float | None) -> bool:
    return value is None or bool(pd.isna(value))


def format_percent(value: float | None, digits: int = 3) -> str:
    """Format a decimal return or coefficient as percentage text."""
    if _is_missing(value):
        return "n/a"
    return f"{float(value) * 100:.{digits}f}%"


def format_basis_points(value: float | None, digits: int = 1) -> str:
    """Format a decimal return or coefficient as basis points."""
    if _is_missing(value):
        return "n/a"
    return f"{float(value) * 10_000:.{digits}f} bps"


def format_p_value(value: float | None) -> str:
    """Format p-values without false precision."""
    if _is_missing(value):
        return "n/a"
    if float(value) < 0.001:
        return "<0.001"
    return f"{float(value):.3f}"


def format_score(value: float | None) -> str:
    if _is_missing(value):
        return "n/a"
    return f"{float(value):.3f}"
