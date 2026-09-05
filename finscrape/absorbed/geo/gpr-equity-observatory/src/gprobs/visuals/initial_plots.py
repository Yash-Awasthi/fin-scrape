from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def build_group_cumulative_returns(group_summary: pd.DataFrame) -> pd.DataFrame:
    """Build cumulative average log returns for developed and emerging groups."""
    wide = group_summary.pivot(
        index="date",
        columns="market_group",
        values="average_return",
    )
    wide = wide.sort_index().cumsum().reset_index()
    wide.columns.name = None
    return wide


def plot_gpr_and_group_returns(
    gpr: pd.DataFrame,
    group_summary: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """Plot daily GPR and cumulative average ETF returns by market group."""
    cumulative_returns = build_group_cumulative_returns(group_summary)
    gpr = gpr.loc[gpr["date"] >= cumulative_returns["date"].min()]

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    axes[0].plot(gpr["date"], gpr["gpr"], color="#1f4e79", linewidth=1)
    axes[0].set_title("Daily Geopolitical Risk Index")
    axes[0].set_ylabel("GPR")

    for column, color in [("developed", "#2f7d32"), ("emerging", "#b23a2e")]:
        if column in cumulative_returns.columns:
            axes[1].plot(
                cumulative_returns["date"],
                cumulative_returns[column],
                label=column.title(),
                linewidth=1.2,
                color=color,
            )

    axes[1].set_title("Cumulative Average ETF Log Returns")
    axes[1].set_ylabel("Cumulative log return")
    axes[1].legend()

    for axis in axes:
        axis.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
