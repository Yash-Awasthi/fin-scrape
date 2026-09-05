import pandas as pd

from gprobs.analysis.panel_regression import (
    prepare_panel_regression_data,
    run_controlled_panel_regression,
    tidy_regression_results,
)

KEY_TERMS = ["gpr_change_z", "gpr_change_z:emerging_market"]
SAMPLE_ROBUSTNESS_COLUMNS = [
    "scenario",
    "term",
    "estimate",
    "std_error",
    "t_stat",
    "p_value",
    "observation_count",
    "gpr_change_mean",
    "gpr_change_std",
]
DEFAULT_SCENARIOS = {
    "Full controlled sample": [],
    "Excluding COVID crash": [("2020-02-15", "2020-04-30")],
    "Excluding Russia invasion window": [("2022-02-01", "2022-04-30")],
    "Excluding COVID and Russia windows": [
        ("2020-02-15", "2020-04-30"),
        ("2022-02-01", "2022-04-30"),
    ],
}


def filter_excluded_periods(
    panel: pd.DataFrame,
    excluded_periods: list[tuple[str, str]],
) -> pd.DataFrame:
    """Remove inclusive date windows from a panel."""
    filtered = panel.copy()
    filtered["date"] = pd.to_datetime(filtered["date"])

    keep = pd.Series(True, index=filtered.index)
    for start_date, end_date in excluded_periods:
        in_period = filtered["date"].between(
            pd.Timestamp(start_date),
            pd.Timestamp(end_date),
            inclusive="both",
        )
        keep = keep & ~in_period

    return filtered.loc[keep].reset_index(drop=True)


def _extract_key_terms(
    table: pd.DataFrame,
    scenario: str,
    observation_count: int,
    gpr_change_mean: float,
    gpr_change_std: float,
) -> pd.DataFrame:
    key_terms = table.loc[table["term"].isin(KEY_TERMS)].copy()
    key_terms["term"] = pd.Categorical(
        key_terms["term"],
        categories=KEY_TERMS,
        ordered=True,
    )
    key_terms = key_terms.sort_values("term").reset_index(drop=True)
    key_terms.insert(0, "scenario", scenario)
    key_terms["observation_count"] = observation_count
    key_terms["gpr_change_mean"] = gpr_change_mean
    key_terms["gpr_change_std"] = gpr_change_std
    return key_terms[SAMPLE_ROBUSTNESS_COLUMNS]


def build_sample_robustness_table(
    panel: pd.DataFrame,
    scenarios: dict[str, list[tuple[str, str]]] | None = None,
    cluster_by_ticker: bool = True,
) -> pd.DataFrame:
    """Rerun the controlled panel model after excluding named date windows."""
    scenarios = scenarios or DEFAULT_SCENARIOS
    full_prepared = prepare_panel_regression_data(panel, include_controls=True)
    gpr_change_mean = float(full_prepared["gpr_change"].mean())
    gpr_change_std = float(full_prepared["gpr_change"].std(ddof=0))
    frames = []

    for scenario, excluded_periods in scenarios.items():
        sample = filter_excluded_periods(panel, excluded_periods)
        prepared = prepare_panel_regression_data(
            sample,
            include_controls=True,
            gpr_change_mean=gpr_change_mean,
            gpr_change_std=gpr_change_std,
        )
        result = run_controlled_panel_regression(
            sample,
            cluster_by_ticker=cluster_by_ticker,
            gpr_change_mean=gpr_change_mean,
            gpr_change_std=gpr_change_std,
        )
        table = tidy_regression_results(result)
        frames.append(
            _extract_key_terms(
                table,
                scenario,
                len(prepared),
                gpr_change_mean,
                gpr_change_std,
            )
        )

    if not frames:
        return pd.DataFrame(columns=SAMPLE_ROBUSTNESS_COLUMNS)

    return pd.concat(frames, ignore_index=True)
