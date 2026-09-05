import pandas as pd

BASE_PANEL_COLUMNS = ["date", "ticker", "country", "market_group", "region", "return"]


def build_analysis_panel(
    returns: pd.DataFrame,
    universe: pd.DataFrame,
    gpr: pd.DataFrame,
) -> pd.DataFrame:
    """Add country metadata and daily GPR values to the ETF return panel."""
    panel = returns.merge(universe, on="ticker", how="left")
    missing_metadata = panel.loc[panel["country"].isna(), "ticker"].drop_duplicates().tolist()
    if missing_metadata:
        raise ValueError(f"Missing country metadata for tickers: {missing_metadata}")

    panel = panel.merge(gpr, on="date", how="left")
    gpr_columns = [column for column in gpr.columns if column != "date"]
    panel = panel[BASE_PANEL_COLUMNS + gpr_columns]
    return panel.sort_values(["date", "ticker"]).reset_index(drop=True)


def build_group_return_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Average country ETF returns by market group for each date."""
    summary = (
        panel.groupby(["date", "market_group"], as_index=False)
        .agg(
            average_return=("return", "mean"),
            country_count=("return", "count"),
        )
        .sort_values(["date", "market_group"])
        .reset_index(drop=True)
    )
    return summary
