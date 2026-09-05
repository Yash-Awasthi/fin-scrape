"""
Single entry point for one ARGUS monitoring cycle:
  1. Ingest any new GDELT events for monitored locations
  2. Recompute risk scores for locations that got new events
  3. Roll up to route-level scores
  4. Evaluate thresholds and alert/reroute as needed

Run this on a schedule (every 15 min) via GitHub Actions / Cloud Scheduler.
Required env vars: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
Optional: SLACK_WEBHOOK_URL, ANTHROPIC_API_KEY (for graphrag explanations)
"""
from config.routes import ROUTES, ALL_LOCATIONS, RISK_THRESHOLD, RISK_WINDOW_HOURS
from argus.graph_client import get_driver, setup_schema, ingest_routes
from argus.ingest import run_ingestion_cycle
from argus.scoring import score_and_log_locations, score_all_routes
from argus.reroute import process_decisions


def main():
    driver = get_driver()
    try:
        # One-time setup, safe to call every run (IF NOT EXISTS / MERGE)
        setup_schema(driver)
        ingest_routes(driver, ROUTES)

        # 1. Ingest new events
        new_events = run_ingestion_cycle(driver, ALL_LOCATIONS)

        # 2. Recompute risk for all monitored locations
        #    (cheap enough to do every cycle at this scale; optimize to
        #     "affected locations only" later if the location list grows large)
        location_risk_df = score_and_log_locations(driver, ALL_LOCATIONS, window_hours=RISK_WINDOW_HOURS)
        print("\nLocation risk scores:")
        print(location_risk_df)

        # 3. Roll up to routes
        route_df = score_all_routes(ROUTES, location_risk_df)
        print("\nRoute risk scores:")
        print(route_df)

        # 4. Evaluate + alert
        process_decisions(route_df, RISK_THRESHOLD)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
