import pandas as pd

from gprobs.reporting.formatting import format_basis_points, format_p_value, format_percent, format_score


def format_estimate(row: pd.Series) -> str:
    """Format estimate values using the row's structured unit."""
    unit = row.get("unit")
    if unit == "score":
        return format_score(row["estimate"])
    if unit == "basis_points":
        return format_basis_points(row["estimate"])
    if unit == "percent":
        return format_percent(row["estimate"])
    raise ValueError(f"Unknown estimate unit: {unit}")


def _method_row(evidence: pd.DataFrame, method: str) -> pd.Series:
    rows = evidence.loc[evidence["method"] == method]
    if rows.empty:
        raise ValueError(f"Evidence summary is missing method: {method}")
    return rows.iloc[0]


def _sample_row(
    sample_robustness: pd.DataFrame,
    scenario: str,
    term: str,
) -> pd.Series:
    mask = (
        (sample_robustness["scenario"] == scenario)
        & (sample_robustness["term"] == term)
    )
    rows = sample_robustness.loc[mask]
    if rows.empty:
        raise ValueError(f"Sample robustness is missing {term} for {scenario}.")
    return rows.iloc[0]


def _evidence_table(rows: list[pd.Series]) -> list[str]:
    lines = [
        "| Method | Estimate | p-value | Inference |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['method']} | {format_estimate(row)} | "
            f"{format_p_value(row['p_value'])} | {row['inference']} |"
        )
    return lines


def build_results_brief(
    evidence_summary: pd.DataFrame,
    sample_robustness: pd.DataFrame,
) -> str:
    """Build a concise Markdown brief from generated model outputs."""
    controlled = _method_row(evidence_summary, "Controlled panel regression")
    interaction = _method_row(evidence_summary, "Controlled emerging interaction")
    date_fe_interaction = _method_row(
        evidence_summary,
        "Date fixed-effects emerging interaction",
    )
    quantile = _method_row(evidence_summary, "Tail-risk quantile regression")
    local_developed = _method_row(evidence_summary, "Local projection developed")
    local_emerging = _method_row(evidence_summary, "Local projection emerging")
    drawdown = _method_row(evidence_summary, "Drawdown classifier")

    robustness_scenario = "Excluding COVID and Russia windows"
    robust_gpr = _sample_row(sample_robustness, robustness_scenario, "gpr_change_z")
    robust_interaction = _sample_row(
        sample_robustness,
        robustness_scenario,
        "gpr_change_z:emerging_market",
    )

    lines = [
        "# GPR Equity Observatory Results Brief",
        "",
        "## Main Takeaway",
        "",
        "The controlled panel regression now estimates responses to daily GPR jumps. "
        "The clean H1 test is the date fixed-effects emerging-market interaction, "
        "which absorbs common global shocks and reports the within-date EM differential.",
        "The older controlled interaction alone is not strong evidence of a "
        "reliably larger emerging-market response.",
        "",
        "## Key Evidence",
        "",
        *_evidence_table(
            [
                controlled,
                interaction,
                date_fe_interaction,
                quantile,
                local_developed,
                local_emerging,
                drawdown,
            ]
        ),
        "",
        "Local projection rows are market-model abnormal return responses, not raw cumulative ETF returns.",
        "Prediction Lab treats the drawdown model as an out-of-sample risk-classification experiment, "
        "not as a trading signal.",
        "",
        "## Sample Robustness",
        "",
        f"Under `{robustness_scenario}`, the controlled one-SD GPR-jump coefficient is "
        f"{format_basis_points(robust_gpr['estimate'])} with p-value "
        f"{format_p_value(robust_gpr['p_value'])}. The emerging interaction is "
        f"{format_basis_points(robust_interaction['estimate'])} with p-value "
        f"{format_p_value(robust_interaction['p_value'])}.",
        "",
        "That means the main controlled GPR-jump coefficient is not only a COVID "
        "or Russia-Ukraine result. But the emerging-market asymmetry claim remains "
        "weak in the current specification.",
        "",
        "## How To Explain This",
        "",
        "- This is an empirical risk-response project, not a trading system.",
        "- ETF returns are USD returns, so they include currency exposure.",
        "- GPR jumps are not randomized events, so the results are associations.",
        "- The date fixed-effects specification identifies the emerging-market "
        "differential, not a separate global GPR-jump coefficient.",
        "- The best current conclusion is cautious: GPR jumps are linked to equity risk, "
        "but emerging-market asymmetry is not yet a strong finding.",
        "",
    ]
    return "\n".join(lines)
