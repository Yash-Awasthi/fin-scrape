"""
Pulls the latest GDELT 15-minute event export, filters to monitored
locations, and ingests into Neo4j via idempotent MERGE. Safe to run
repeatedly (e.g. every 15 min via cron/GitHub Actions) — re-processing
the same file is a no-op thanks to the checkpoint + MERGE semantics.
"""
import io
import zipfile
import requests
import pandas as pd

from argus.graph_client import get_checkpoint, set_checkpoint

EVENTS_COLS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate", "Actor1Code", "Actor1Name",
    "Actor1CountryCode", "Actor1KnownGroupCode", "Actor1EthnicCode", "Actor1Religion1Code",
    "Actor1Religion2Code", "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code", "Actor2Code",
    "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode", "Actor2EthnicCode", "Actor2Religion1Code",
    "Actor2Religion2Code", "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code", "IsRootEvent",
    "EventCode", "EventBaseCode", "EventRootCode", "QuadClass", "GoldsteinScale", "NumMentions",
    "NumSources", "NumArticles", "AvgTone", "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_ADM2Code", "Actor1Geo_Lat", "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode", "Actor2Geo_ADM1Code", "Actor2Geo_ADM2Code",
    "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID", "ActionGeo_Type", "ActionGeo_FullName",
    "ActionGeo_CountryCode", "ActionGeo_ADM1Code", "ActionGeo_ADM2Code", "ActionGeo_Lat", "ActionGeo_Long",
    "ActionGeo_FeatureID", "DATEADDED", "SOURCEURL",
]

GDELT_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"


def get_latest_gdelt_files() -> dict:
    r = requests.get(GDELT_LASTUPDATE_URL, timeout=30)
    r.raise_for_status()
    files = {}
    for line in r.text.strip().split("\n"):
        url = line.split(" ")[-1]
        if "export.csv" in url:
            files["events"] = url
        elif "gkg.csv" in url:
            files["gkg"] = url
    return files


def fetch_events_csv(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    fname = z.namelist()[0]
    return pd.read_csv(z.open(fname), sep="\t", names=EVENTS_COLS, low_memory=False)


def filter_to_locations(df: pd.DataFrame, locations: list) -> pd.DataFrame:
    pattern = "|".join(locations)
    return df[df["ActionGeo_FullName"].str.contains(pattern, case=False, na=False)].copy()


def prepare_rows(df: pd.DataFrame) -> list:
    rows = []
    for idx, r in df.iterrows():
        rows.append({
            "event_id": str(r["GLOBALEVENTID"]),
            "location": r["ActionGeo_FullName"],
            "date": str(r["SQLDATE"]),
            "event_code": r.get("EventCode"),
            "goldstein": float(r["GoldsteinScale"]) if pd.notna(r["GoldsteinScale"]) else None,
            "tone": float(r["AvgTone"]) if pd.notna(r["AvgTone"]) else None,
            "mentions": int(r["NumMentions"]) if pd.notna(r["NumMentions"]) else 1,
            "quad_class": int(r["QuadClass"]) if pd.notna(r["QuadClass"]) else None,
            "actor1": r.get("Actor1Name") if pd.notna(r.get("Actor1Name")) else None,
            "actor2": r.get("Actor2Name") if pd.notna(r.get("Actor2Name")) else None,
        })
    return rows


def ingest_events(driver, rows: list, batch_size: int = 500):
    query = """
    UNWIND $rows AS row
    MERGE (l:Location {name: row.location})
    MERGE (e:Event {id: row.event_id})
    SET e.date = row.date,
        e.event_code = row.event_code,
        e.goldstein = row.goldstein,
        e.tone = row.tone,
        e.mentions = row.mentions,
        e.quad_class = row.quad_class
    MERGE (e)-[:OCCURRED_AT]->(l)
    FOREACH (_ IN CASE WHEN row.actor1 IS NOT NULL THEN [1] ELSE [] END |
        MERGE (a1:Actor {name: row.actor1})
        MERGE (a1)-[:INVOLVED_IN]->(e)
    )
    FOREACH (_ IN CASE WHEN row.actor2 IS NOT NULL THEN [1] ELSE [] END |
        MERGE (a2:Actor {name: row.actor2})
        MERGE (a2)-[:INVOLVED_IN]->(e)
    )
    """
    with driver.session() as session:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            session.run(query, rows=batch)


def run_ingestion_cycle(driver, locations: list) -> pd.DataFrame | None:
    """
    One cycle: check for a new GDELT file, ingest any events matching
    monitored locations, advance the checkpoint. Returns the matched
    dataframe (possibly empty) or None if there was nothing new to fetch.
    """
    files = get_latest_gdelt_files()
    last_processed = get_checkpoint(driver)

    if files.get("events") == last_processed:
        print("No new GDELT update since last cycle — skipping.")
        return None

    print(f"New GDELT file: {files['events']}")
    df = fetch_events_csv(files["events"])
    relevant = filter_to_locations(df, locations)
    print(f"{len(relevant)} events matched monitored locations")

    if len(relevant) > 0:
        rows = prepare_rows(relevant)
        ingest_events(driver, rows)

    set_checkpoint(driver, files["events"])
    return relevant
