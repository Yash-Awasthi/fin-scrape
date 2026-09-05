"""
Threshold-based reroute decisions, with optional Slack alerting.
Set SLACK_WEBHOOK_URL as an env var / GitHub secret to enable alerts;
if unset, decisions are just printed/returned (no alert sent).
"""
import os
import requests
import pandas as pd


def evaluate_route(current_route: str, route_df: pd.DataFrame, threshold: float) -> dict:
    match = route_df[route_df["route"] == current_route]
    if match.empty:
        return {"action": "UNKNOWN_ROUTE", "current_route": current_route}
    current = match.iloc[0]

    if current["risk_score"] >= threshold:
        alternatives = route_df[route_df["route"] != current_route].sort_values("risk_score")
        if alternatives.empty:
            return {
                "action": "ALERT_NO_ALTERNATIVE",
                "current_route": current_route,
                "current_risk": current["risk_score"],
                "bottleneck": current["bottleneck"],
            }
        best_alt = alternatives.iloc[0]
        return {
            "action": "REROUTE",
            "current_route": current_route,
            "current_risk": current["risk_score"],
            "bottleneck": current["bottleneck"],
            "suggested_route": best_alt["route"],
            "suggested_risk": best_alt["risk_score"],
        }
    return {
        "action": "PROCEED",
        "current_route": current_route,
        "current_risk": current["risk_score"],
        "bottleneck": current["bottleneck"],
    }


def evaluate_all_routes(route_df: pd.DataFrame, threshold: float) -> list:
    return [evaluate_route(r, route_df, threshold) for r in route_df["route"]]


def send_slack_alert(decision: dict):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print(f"[no SLACK_WEBHOOK_URL set] Would alert: {decision}")
        return

    if decision["action"] == "REROUTE":
        text = (
            f":rotating_light: *ARGUS Reroute Alert*\n"
            f"Route *{decision['current_route']}* risk = {decision['current_risk']} "
            f"(bottleneck: {decision['bottleneck']})\n"
            f"Suggested alternative: *{decision['suggested_route']}* "
            f"(risk = {decision['suggested_risk']})"
        )
    elif decision["action"] == "ALERT_NO_ALTERNATIVE":
        text = (
            f":warning: *ARGUS Alert — No Safe Alternative*\n"
            f"Route *{decision['current_route']}* risk = {decision['current_risk']} "
            f"(bottleneck: {decision['bottleneck']}), but no lower-risk alternative is defined."
        )
    else:
        return  # don't alert on PROCEED

    requests.post(webhook_url, json={"text": text}, timeout=15)


def process_decisions(route_df: pd.DataFrame, threshold: float):
    decisions = evaluate_all_routes(route_df, threshold)
    for d in decisions:
        print(d)
        if d["action"] in ("REROUTE", "ALERT_NO_ALTERNATIVE"):
            send_slack_alert(d)
    return decisions
