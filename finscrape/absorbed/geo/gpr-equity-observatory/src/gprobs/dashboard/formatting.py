import pandas as pd

from gprobs.reporting import formatting as reporting_formatting


def format_percent(value: float) -> str:
    return reporting_formatting.format_percent(value, digits=1)


def format_basis_points(value: float) -> str:
    return reporting_formatting.format_basis_points(value)


def format_p_value(value: float) -> str:
    return reporting_formatting.format_p_value(value)


def format_metric(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{float(value):.3g}"


def classify_evidence_strength(row: pd.Series) -> str:
    """Return a cautious display label for dashboard evidence summaries."""
    inference = str(row.get("inference", "")).lower()
    p_value = pd.to_numeric(row.get("p_value"), errors="coerce")
    if "exploratory" in inference or pd.isna(p_value):
        return "Exploratory"
    if "mixed" in inference:
        return "Mixed"
    if p_value <= 0.10:
        return "Useful signal"
    if p_value <= 0.50:
        return "Mixed"
    return "Weak"


def format_evidence_direction(estimate: float) -> str:
    if estimate > 0:
        return "Positive"
    if estimate < 0:
        return "Negative"
    return "Near zero"


def format_evidence_estimate(estimate: float, unit: str) -> str:
    if unit == "basis_points":
        return format_basis_points(estimate)
    if unit == "percent":
        return format_percent(estimate)
    if unit == "score":
        return reporting_formatting.format_score(estimate)
    raise ValueError(f"Unknown estimate unit: {unit}")
