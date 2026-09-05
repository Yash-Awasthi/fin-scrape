import pandas as pd
import plotly.express as px


def build_gpr_shock_timeline(gpr: pd.DataFrame):
    timeline = gpr.sort_values("date")
    top_shocks = gpr.sort_values("gpr_change", ascending=False).head(25)
    fig = px.line(timeline, x="date", y="gpr", title="GPR Index With Top Shock Dates")
    fig.add_scatter(
        x=top_shocks["date"],
        y=top_shocks["gpr"],
        mode="markers",
        name="Top GPR changes",
        customdata=top_shocks[["gpr_change", "event"]],
        hovertemplate=(
            "Date=%{x}<br>GPR=%{y}<br>GPR change=%{customdata[0]}"
            "<br>Event=%{customdata[1]}<extra></extra>"
        ),
    )
    return fig


def build_prediction_calibration_chart(drawdown_calibration: pd.DataFrame):
    fig = px.line(
        drawdown_calibration,
        x="probability_decile",
        y="realized_event_rate",
        color="model_name",
        markers=True,
        title="Realized Drawdown Rate by Predicted-Risk Decile",
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def build_prediction_lift_chart(drawdown_lift: pd.DataFrame):
    return px.bar(
        drawdown_lift,
        x="bucket",
        y="lift",
        color="model_name",
        barmode="group",
        title="Drawdown Event Lift in Highest-Risk Buckets",
    )


def build_feature_importance_chart(drawdown_importance: pd.DataFrame):
    fig = px.bar(
        drawdown_importance,
        x="abs_coefficient",
        y="feature",
        orientation="h",
        title="Drawdown Model Feature Importance",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def build_monthly_gpr_shock_chart(month_level: pd.DataFrame):
    fig = px.line(
        month_level,
        x="date_month",
        y="gpr_change_z",
        title="Monthly GPR Shock Measure",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    return fig


def build_monthly_spread_chart(month_level: pd.DataFrame):
    fig = px.line(
        month_level,
        x="date_month",
        y="spread_em_dev",
        title="Emerging Minus Developed Aggregate Return Spread",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    return fig


def build_monthly_forecast_chart(forecasts: pd.DataFrame):
    fig = px.bar(
        forecasts,
        x="model",
        y="oos_r2",
        title="Monthly Forecast OOS R2 Versus Historical Mean",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    return fig
