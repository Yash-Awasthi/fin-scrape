import pandas as pd


def require_columns(df: pd.DataFrame, required: list[str], label: str = "Data") -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def coerce_shock_to_int(value) -> int:
    if isinstance(value, str):
        return int(value.strip().lower() == "true")
    return int(bool(value))
