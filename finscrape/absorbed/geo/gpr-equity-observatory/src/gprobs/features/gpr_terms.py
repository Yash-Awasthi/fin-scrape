from dataclasses import dataclass

GPR_CHANGE_COLUMN = "gpr_change"
GPR_CHANGE_Z_COLUMN = "gpr_change_z"
FULL_SAMPLE_GPR_CHANGE_SHOCK_COLUMN = "gpr_change_shock_full_sample"
EXPANDING_GPR_CHANGE_SHOCK_COLUMN = "gpr_change_shock_expanding"
GPR_CHANGE_SHOCK_COMPATIBILITY_ALIAS = "gpr_change_shock"
GPR_SHOCK_COMPATIBILITY_ALIAS = "gpr_shock"
GPR_SHOCK_FULL_SAMPLE_ALIAS = "gpr_shock_full_sample"
GPR_SHOCK_EXPANDING_ALIAS = "gpr_shock_expanding"
PREFERRED_GPR_SHOCK_COLUMN = EXPANDING_GPR_CHANGE_SHOCK_COLUMN
LEGACY_GPR_SHOCK_ALIASES = (
    GPR_CHANGE_SHOCK_COMPATIBILITY_ALIAS,
    GPR_SHOCK_COMPATIBILITY_ALIAS,
    GPR_SHOCK_FULL_SAMPLE_ALIAS,
    GPR_SHOCK_EXPANDING_ALIAS,
)


@dataclass(frozen=True)
class GprFeatureContext:
    column: str
    label: str
    standardization: str
    time_aware: bool
    primary_use: str


DAILY_DESCRIPTIVE_GPR_CHANGE_Z = GprFeatureContext(
    column=GPR_CHANGE_Z_COLUMN,
    label="Daily descriptive z-score",
    standardization="Full-sample daily GPR-change mean and standard deviation.",
    time_aware=False,
    primary_use="Daily GPR output summaries and descriptive shock tables.",
)
PANEL_REGRESSION_GPR_CHANGE_Z = GprFeatureContext(
    column=GPR_CHANGE_Z_COLUMN,
    label="Panel regression z-score",
    standardization="Regression sample mean and standard deviation, reused for robustness subsamples.",
    time_aware=False,
    primary_use="Daily ETF panel, quantile, and sample-robustness regressions.",
)
PREDICTION_LAB_EXPANDING_GPR_CHANGE_Z = GprFeatureContext(
    column=GPR_CHANGE_Z_COLUMN,
    label="Prediction Lab expanding z-score",
    standardization="Prior expanding mean and standard deviation available at each prediction date.",
    time_aware=True,
    primary_use="Out-of-sample drawdown-risk classification features.",
)
MONTHLY_DESCRIPTIVE_GPR_CHANGE_Z = GprFeatureContext(
    column=GPR_CHANGE_Z_COLUMN,
    label="Monthly benchmark descriptive z-score",
    standardization="Full-sample monthly benchmark GPR-change mean and standard deviation.",
    time_aware=False,
    primary_use="Monthly developed/emerging aggregate benchmark regressions and charts.",
)

GPR_CHANGE_Z_CONTEXTS = {
    "daily_descriptive": DAILY_DESCRIPTIVE_GPR_CHANGE_Z,
    "panel_regression": PANEL_REGRESSION_GPR_CHANGE_Z,
    "prediction_lab_expanding": PREDICTION_LAB_EXPANDING_GPR_CHANGE_Z,
    "monthly_descriptive": MONTHLY_DESCRIPTIVE_GPR_CHANGE_Z,
}
