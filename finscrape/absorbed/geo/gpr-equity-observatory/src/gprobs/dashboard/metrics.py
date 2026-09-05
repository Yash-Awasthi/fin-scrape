import pandas as pd

from gprobs.data.diagnostics import summarize_country_coverage as build_country_coverage  # noqa: F401

__all__ = ["build_country_coverage", "select_key_regression_terms"]


def select_key_regression_terms(table: pd.DataFrame) -> pd.DataFrame:
    """Keep only the GPR terms that matter for the baseline interpretation."""
    terms = ["gpr_change_z", "gpr_change_z:emerging_market"]
    return table.loc[table["term"].isin(terms)].reset_index(drop=True)
