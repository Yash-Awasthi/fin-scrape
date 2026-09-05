from contextlib import nullcontext
from pathlib import Path

import pandas as pd
import streamlit as st

DASHBOARD_MODES = ("Beginner", "Technical")
DASHBOARD_INTRO = (
    "This dashboard studies whether equity markets respond to geopolitical risk shocks, "
    "using 20 country ETF proxies."
)
DASHBOARD_MAIN_TAKEAWAY = (
    "Geopolitical risk appears associated with equity-market risk, but the evidence "
    "does not strongly prove that emerging markets always react more than developed markets."
)
DASHBOARD_USE_NOTE = "Use this dashboard as a research observatory, not as a trading system."
CENTRAL_PROJECT_QUESTION = (
    "When geopolitical risk jumps, does it help us understand or rank downside risk in international equity "
    "markets, especially for emerging markets?"
)
OVERVIEW_JOB_STATEMENTS = [
    (
        "Explanation",
        "Do markets look worse around geopolitical-risk shocks?",
    ),
    (
        "Prediction",
        "Does geopolitical risk help rank ETF-country observations by short-term drawdown risk?",
    ),
]
OVERVIEW_READER_PATH = [
    {
        "step": "1",
        "title": "Start with the question",
        "body": "The dashboard asks whether geopolitical risk jumps are associated with country ETF returns.",
    },
    {
        "step": "2",
        "title": "Look at the graphs",
        "body": "Use the GPR timeline and market-reaction charts before reading statistical tables.",
    },
    {
        "step": "3",
        "title": "Check the evidence labels",
        "body": "Weak or mixed evidence is a result; it is not a failed dashboard.",
    },
]
METHOD_MAP_ROWS = [
    {
        "Question": "What happened around shocks?",
        "Tool": "Event study",
        "Output": "Market response chart",
        "What to look for": "Whether ETF abnormal returns worsen around GPR shock dates.",
    },
    {
        "Question": "Does it survive controls?",
        "Tool": "Panel regression",
        "Output": "Coefficient table",
        "What to look for": "Whether GPR terms remain meaningful after market controls.",
    },
    {
        "Question": "Does it matter more on bad days?",
        "Tool": "Quantile regression",
        "Output": "Downside-risk chart",
        "What to look for": "Whether lower-return quantiles show stronger downside association.",
    },
    {
        "Question": "Does the response persist?",
        "Tool": "Local projection",
        "Output": "20-day response path",
        "What to look for": "Whether cumulative abnormal returns build or fade after shocks.",
    },
    {
        "Question": "Can we rank drawdown risk?",
        "Tool": "Prediction Lab",
        "Output": "AUC, lift, and calibration",
        "What to look for": "Whether GPR improves out-of-sample downside-risk ranking.",
    },
    {
        "Question": "Does monthly evidence agree?",
        "Tool": "Monthly benchmark",
        "Output": "HAC and forecast table",
        "What to look for": "Whether lower-frequency aggregate evidence aligns with the daily panel.",
    },
]
OVERVIEW_CURRENT_ANSWER_POINTS = [
    "GPR is associated with equity-market risk, but the current evidence is mixed rather than dramatic.",
    "The emerging-market asymmetry is mixed and not statistically strong after controls.",
    "Prediction Lab shows modest ranking signal for drawdown risk.",
    "GPR alone is weak compared with volatility and broader market features.",
]
OVERVIEW_DOES_NOT_PROVE_POINTS = [
    "causality",
    "investment advice",
    "a trading system",
    "that emerging markets always react more",
]
HOW_TO_READ_NOTES = {
    "overview": (
        "Start with the project question and Method Map, then use the Evidence Map to compare what each method "
        "says about explanation or drawdown-risk ranking. Mixed or weak labels mean the result should stay cautious."
    ),
    "shocks": (
        "The line shows the GPR index over time. Markers highlight the largest daily GPR changes, which anchor "
        "the question of what happens when geopolitical risk jumps."
    ),
    "market_response": (
        "The line shows average cumulative abnormal returns around GPR shock dates. Day 0 is the "
        "shock day. A negative line after day 0 means ETFs tended to underperform their "
        "market-model expectation after shocks."
    ),
    "regression": (
        "The key term is the emerging-market interaction. If it is negative and statistically strong, "
        "that would support the idea that emerging markets react more. In the current version, this "
        "evidence is not strong."
    ),
    "downside_risk": (
        "Lower return quantiles describe worse return days. A more negative coefficient in the lower "
        "tail suggests downside association, but p-values still determine how strong the evidence is."
    ),
    "dynamic_response": (
        "Each horizon shows the estimated cumulative abnormal-return response after a GPR shock. "
        "Confidence bands crossing zero indicate weak statistical evidence at that horizon."
    ),
    "prediction_lab": (
        "This is an exploratory risk classifier for the ranking question. AUC above 0.5 means some ranking "
        "signal, but it is not a trading strategy and should not be read as a price forecast."
    ),
    "country_sensitivity": (
        "The rolling beta shows how one country's ETF return sensitivity to GPR changes over time. "
        "Use it as a diagnostic, not as a stable country ranking."
    ),
    "monthly_benchmark": (
        "This tab is separate from the daily ETF panel. Sample mode validates the workflow, while real "
        "mode is aggregate benchmark evidence, not country-level panel evidence."
    ),
    "data_quality": (
        "Coverage and large-return flags help identify data limitations that may affect interpretation. "
        "They are checks on the research inputs, not standalone findings."
    ),
}
BEGINNER_TAB_GUIDES = {
    "overview": {
        "question": "What problem is this dashboard solving?",
        "takeaways": [
            (
                "One question",
                "The dashboard asks whether GPR helps explain or rank downside risk in international ETFs.",
            ),
            (
                "Current answer",
                "GPR is associated with risk, but the emerging-market asymmetry is mixed and not strong.",
            ),
            (
                "Prediction signal",
                "Prediction Lab has modest ranking signal, mostly beyond GPR alone.",
            ),
        ],
        "does_not_prove": (
            "It does not prove causality, a trading rule, or that emerging markets always react more."
        ),
    },
    "shocks": {
        "question": "When did geopolitical risk jump the most?",
        "takeaways": [
            (
                "Shock days",
                "Marked dates are the largest daily increases in the GPR index.",
            ),
            (
                "Starting points",
                "These dates anchor the event studies and follow-up risk checks.",
            ),
        ],
        "does_not_prove": (
            "It does not prove that GPR caused any specific market move on those dates."
        ),
    },
    "market_response": {
        "question": "What happened around GPR shock days?",
        "takeaways": [
            (
                "Average response",
                "The chart compares average ETF behavior before and after shock dates.",
            ),
            (
                "Group comparison",
                "Developed and emerging averages can move differently, but the evidence varies by window.",
            ),
            (
                "Robustness matters",
                "Changing the shock cutoff or window can change the apparent response.",
            ),
        ],
        "does_not_prove": (
            "It does not prove every country moved this way or that GPR was the only driver."
        ),
    },
    "regression": {
        "question": "Does the controlled panel show a stronger emerging-market response?",
        "takeaways": [
            (
                "Controls included",
                "The controlled models compare GPR with market conditions held in the model.",
            ),
            (
                "Cautious result",
                "Current emerging-market asymmetry is mixed and not statistically strong.",
            ),
            (
                "Association only",
                "The estimates describe conditional association, not cause and effect.",
            ),
        ],
        "does_not_prove": (
            "It does not prove a causal GPR effect or a reliable emerging-market penalty."
        ),
    },
    "downside_risk": {
        "question": "Is the GPR relationship stronger on bad market days?",
        "takeaways": [
            (
                "Tail focus",
                "Lower quantiles describe worse return days rather than average days.",
            ),
            (
                "Pattern check",
                "More negative lower-tail estimates would point to downside-risk association.",
            ),
        ],
        "does_not_prove": (
            "It does not prove that the lower-tail pattern is stable across samples or tradeable."
        ),
    },
    "dynamic_response": {
        "question": "How long did average responses persist after a shock?",
        "takeaways": [
            (
                "Time path",
                "Each point estimates the response at a later post-shock horizon.",
            ),
            (
                "Uncertainty",
                "Wide bands or bands crossing zero mean the timing evidence is weak.",
            ),
        ],
        "does_not_prove": (
            "It does not prove a permanent market effect or a precisely timed reaction."
        ),
    },
    "prediction_lab": {
        "question": "Can recent conditions rank short-horizon drawdown risk?",
        "takeaways": [
            (
                "Risk ranking",
                "Prediction Lab ranks drawdown risk for ETF-date observations; it does not predict prices.",
            ),
            (
                "Modest signal",
                "The full-feature model has some ranking signal, while GPR alone is weak.",
            ),
            (
                "Probability check",
                "Calibration and Brier score show whether risk scores match realized drawdown rates.",
            ),
        ],
        "does_not_prove": (
            "It does not predict prices, choose ETFs, or turn GPR into investment advice."
        ),
    },
    "country_sensitivity": {
        "question": "Which country ETF looked more sensitive to GPR over time?",
        "takeaways": [
            (
                "Rolling view",
                "The line changes as the estimation window moves through time.",
            ),
            (
                "Diagnostic only",
                "Use it to inspect instability, not to rank countries permanently.",
            ),
        ],
        "does_not_prove": (
            "It does not prove that one country is always more exposed than another."
        ),
    },
    "monthly_benchmark": {
        "question": "What does the separate monthly benchmark add?",
        "takeaways": [
            (
                "Separate layer",
                "Monthly benchmark data is kept separate from the daily 20-country ETF panel.",
            ),
            (
                "Sample boundary",
                "Sample monthly mode checks software behavior; it is not empirical evidence.",
            ),
            (
                "Limited inference",
                "Real monthly mode is aggregate benchmark evidence, not country-clustered panel proof.",
            ),
        ],
        "does_not_prove": (
            "It does not prove country-level emerging-market asymmetry."
        ),
    },
    "data_quality": {
        "question": "Are the input files broad enough to interpret the results?",
        "takeaways": [
            (
                "Coverage",
                "Country coverage shows which ETF histories support the panel.",
            ),
            (
                "Flags",
                "Large daily-return flags point to rows worth checking before over-interpreting results.",
            ),
        ],
        "does_not_prove": (
            "It does not prove the results are free of data limitations or source risk."
        ),
    },
}
GLOSSARY_TERMS = {
    "GPR": "Geopolitical Risk index: a news-based measure of geopolitical tension and threat.",
    "ETF": "Exchange-traded fund: this project uses country ETFs as public market proxies.",
    "shock": "A large jump in GPR, used as an event date or high-risk signal.",
    "control": "Another market variable included so the GPR estimate is not standing alone.",
    "p-value": (
        "A statistical check for how surprising an estimate would be if the true effect "
        "were zero; smaller is stronger, but not proof."
    ),
    "AUC": (
        "A ranking score for the classifier; 0.5 is random-like, and higher means "
        "better separation of drawdown and non-drawdown cases."
    ),
    "average precision": (
        "A score focused on the highest-risk rows; higher means actual drawdowns are "
        "more concentrated near the top of the ranking."
    ),
    "Brier score": "A probability-accuracy score; lower is better because predicted risks are closer to what happened.",
    "lift": "How much more common drawdowns are inside a high-risk bucket than in the full sample.",
    "calibration": "A check of whether predicted risk levels match realized drawdown rates.",
}
PREDICTION_METRIC_EXPLANATIONS = {
    "AUC": (
        "A ranking score: 0.5 is no better than random, while higher values mean drawdown "
        "events tend to receive higher risk scores than non-events."
    ),
    "average precision": (
        "A high-risk ranking score: higher values mean the top-ranked rows contain more "
        "of the actual drawdown events."
    ),
    "Brier score": (
        "A probability-accuracy score: lower is better because predicted risks are closer "
        "to what actually happened."
    ),
    "lift": (
        "A concentration score: 1.5x means drawdowns were 50% more common in a selected "
        "high-risk bucket than in the full sample."
    ),
    "calibration": (
        "A probability check: if a bucket has 20% predicted risk, calibration asks whether "
        "about 20% of rows in that bucket actually had drawdowns."
    ),
}


def is_beginner_mode(mode: str) -> bool:
    return mode == DASHBOARD_MODES[0]


def render_intro() -> None:
    st.markdown(DASHBOARD_INTRO)
    st.markdown(f"**Main takeaway:** {DASHBOARD_MAIN_TAKEAWAY}")
    st.caption(DASHBOARD_USE_NOTE)


def render_mode_selector() -> str:
    return st.radio(
        "Dashboard mode",
        DASHBOARD_MODES,
        index=0,
        horizontal=True,
        help=(
            "Beginner starts each tab with plain-English takeaways. "
            "Technical keeps detailed tables, downloads, and diagnostics in view."
        ),
    )


def render_glossary() -> None:
    with st.sidebar.expander("Glossary", expanded=False):
        for term, explanation in GLOSSARY_TERMS.items():
            st.markdown(f"**{term}:** {explanation}")


def render_beginner_intro(tab_key: str) -> None:
    guide = BEGINNER_TAB_GUIDES[tab_key]
    st.markdown(f"**Question:** {guide['question']}")


def render_beginner_takeaways(tab_key: str) -> None:
    guide = BEGINNER_TAB_GUIDES[tab_key]
    columns = st.columns(len(guide["takeaways"]))
    for column, (title, body) in zip(columns, guide["takeaways"], strict=True):
        with column:
            st.subheader(title)
            st.write(body)
    st.warning(f"What this does not prove: {guide['does_not_prove']}")


def render_prediction_metric_explanations() -> None:
    with st.expander("How to read Prediction Lab scores", expanded=True):
        for metric, explanation in PREDICTION_METRIC_EXPLANATIONS.items():
            st.markdown(f"**{metric}:** {explanation}")


def render_summary_cards() -> None:
    cards = [
        (
            "Question",
            "Does GPR help explain or rank downside risk in international ETF exposure?",
        ),
        ("Data", "20 country ETF proxies, daily GPR data, and market controls."),
        (
            "Methods",
            "Event studies, regressions, quantile analysis, local projections, rolling betas, "
            "and drawdown-risk classification.",
        ),
        (
            "Bottom line",
            "Evidence is useful but mixed. Stronger for general risk association than for "
            "emerging-market asymmetry.",
        ),
    ]
    columns = st.columns(4)
    for column, (title, body) in zip(columns, cards, strict=True):
        with column:
            st.subheader(title)
            st.write(body)


def render_how_to_read(tab_key: str) -> None:
    st.info(f"How to read this: {HOW_TO_READ_NOTES[tab_key]}")


def technical_details(label: str, mode: str):
    if is_beginner_mode(mode):
        return st.expander(f"Technical details: {label}", expanded=False)
    return nullcontext()


def render_csv_download(df: pd.DataFrame, label: str, filename: str) -> None:
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=f"download-{filename}",
    )


def render_missing_data_message(missing: list[Path]) -> None:
    st.error("Processed data files are missing.")
    st.write("To rebuild everything, run:")
    st.code("python scripts/build_all.py")
    with st.expander("Advanced: individual scripts"):
        from gprobs.pipeline import PIPELINE_STEPS

        st.code("\n".join(f"python scripts/{step.script_name}" for step in PIPELINE_STEPS))
    st.write("Missing files:")
    st.write([str(path) for path in missing])
