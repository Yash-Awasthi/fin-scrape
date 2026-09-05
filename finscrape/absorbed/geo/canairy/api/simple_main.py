"""
Canairy API — serves indicator data with live collection where available.

Live collectors (no API key needed):
  - CISA KEV (cyber threats)
  - WHO Disease Outbreaks (RSS)
  - Grocery CPI (BLS — limited free tier)

Live collectors (need FRED_API_KEY env var):
  - Treasury yield volatility
  - Jobless claims
  - GDP growth

All other indicators served from curated mock data matching the frontend schema.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Canairy",
    version="2.2.0",
    description="Household Resilience Monitoring — Live + Mock Data API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:5173",
        "https://canairy.onrender.com",
        "https://canairy.news",
        "https://www.canairy.news",
        "https://canairy.xyz",
        "https://www.canairy.xyz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Try to initialize live data service ───
data_service = None
try:
    # Try relative import first (when running as module)
    from .data_service import get_data_service
    data_service = get_data_service()
    logger.info(f"Live data service initialized with collectors: {list(data_service._collectors.keys())}")
except ImportError:
    try:
        # Fallback for direct execution
        from data_service import get_data_service
        data_service = get_data_service()
        logger.info(f"Live data service initialized with collectors: {list(data_service._collectors.keys())}")
    except Exception as e:
        logger.warning(f"Live data service unavailable, using mock only: {e}")
except Exception as e:
    logger.warning(f"Live data service unavailable, using mock only: {e}")


# ─── Mock data for all 34 indicators (matches frontend mockData.ts IDs) ───

def _now() -> str:
    return datetime.utcnow().isoformat()


def _ind(id: str, name: str, domain: str, desc: str, unit: str,
         value: Any, level: str, trend: str, source: str,
         threshold_amber: float, threshold_red: float,
         critical: bool = False, green_flag: bool = False,
         enabled: bool = True, unavailable: bool = False) -> Dict[str, Any]:
    """Build an indicator dict matching the frontend IndicatorData shape."""
    # If unavailable, show blank values
    if unavailable:
        status_value = None
        status_level = "unknown"
        status_trend = "unknown"
        data_source = "UNAVAILABLE"
    else:
        status_value = value
        status_level = level
        status_trend = trend
        data_source = "MOCK"

    return {
        "id": id,
        "name": name,
        "domain": domain,
        "description": desc,
        "unit": unit,
        "thresholds": {
            "green": {"max": threshold_amber},
            "amber": {"min": threshold_amber, "max": threshold_red},
            "red": {"min": threshold_red},
            "threshold_amber": threshold_amber,
            "threshold_red": threshold_red,
        },
        "critical": critical,
        "greenFlag": green_flag,
        "enabled": enabled,
        "unavailable": unavailable,
        "dataSource": source,
        "updateFrequency": "60m",
        "status": {
            "level": status_level,
            "value": status_value,
            "trend": status_trend,
            "lastUpdate": _now(),
            "dataSource": data_source,
        },
    }


def get_all_mock_indicators() -> List[Dict[str, Any]]:
    """Return indicators - only those with live collectors + unavailable placeholders."""
    return [
        # ── Economy ──
        _ind("econ_01_treasury_tail", "10Y Auction Tail", "economy",
             "10-year Treasury auction tail in basis points", "bps",
             2.1, "green", "stable", "US Treasury API", 3, 7),
        _ind("econ_02_grocery_cpi", "Grocery CPI", "economy",
             "Grocery CPI 3-month annualized", "%",
             5.4, "amber", "up", "BLS API", 4, 8),
        _ind("market_01_intraday_swing", "10Y Intraday Swing", "economy",
             "10-year Treasury intraday swing in basis points", "bps",
             24.3, "amber", "up", "Yahoo Finance", 20, 30, critical=True),
        _ind("green_g1_gdp_rates", "GDP Green Flag", "economy",
             "US real GDP growth rate", "condition",
             0, "amber", "stable", "BEA / FRED", 1, 0, green_flag=True),
        _ind("bank_01_failures", "Bank Failures", "economy",
             "FDIC bank failures year-to-date", "banks",
             2, "green", "stable", "FDIC", 3, 10),
        _ind("bank_02_discount_window", "Fed Discount Window", "economy",
             "Federal Reserve discount window borrowing", "B USD",
             5.2, "green", "stable", "Federal Reserve", 10, 50),
        _ind("bank_03_deposit_flow", "Bank Deposit Flows", "economy",
             "Weekly change in commercial bank deposits", "B USD",
             -12, "amber", "down", "Federal Reserve H.8", -20, -50),
        _ind("housing_01_delinquency", "Mortgage Delinquency", "economy",
             "Mortgage delinquency rate (30+ days)", "%",
             3.8, "amber", "up", "Freddie Mac PMMS", 3.5, 6.0),
        _ind("luxury_01_collapse", "Luxury Market", "economy",
             "Luxury goods index vs S&P 500", "ratio",
             0.92, "amber", "down", "Yahoo Finance", 0.95, 0.85),
        _ind("housing_03_rate_shock", "Mortgage Rate Shock", "economy",
             "30-year fixed mortgage rate", "%",
             7.1, "red", "up", "Freddie Mac PMMS", 6.5, 7.0),

        # ── Jobs & Labor ──
        _ind("job_01_jobless_claims", "Initial Jobless Claims", "jobs_labor",
             "Weekly initial unemployment claims", "K claims",
             228, "green", "stable", "DOL / FRED", 250, 350),
        _ind("job_01_strike_days", "US Strike Days", "jobs_labor",
             "US strike worker-days per month", "worker-days",
             78000, "green", "stable", "Cornell ILR", 100000, 500000),

        # ── Rights & Governance ──
        _ind("civil_01_acled_protests", "US Protests (7d avg)", "rights_governance",
             "ACLED US protests 7-day average", "protests/day",
             18, "green", "stable", "News RSS", 25, 75),
        _ind("power_01_ai_surveillance", "AI Surveillance Bills", "rights_governance",
             "AI/surveillance bills advancing in state legislatures", "bills",
             6, "amber", "up", "OpenStates", 3, 10),
        _ind("liberty_litigation_count", "Liberty Cases Active", "rights_governance",
             "Major civil liberty cases in federal courts", "cases",
             8, "amber", "up", "CourtListener", 5, 20),

        # ── Security & Infrastructure ──
        _ind("cyber_01_cisa_kev", "CISA KEV + ICS", "security_infrastructure",
             "CISA Known Exploited Vulnerabilities (90-day count)", "vulns",
             4, "amber", "up", "CISA JSON Feed", 2, 5),
        _ind("grid_01_pjm_outages", "NWS Severe Alerts", "security_infrastructure",
             "NWS extreme+severe weather alerts active", "alerts",
             1, "green", "stable", "NWS API", 3, 8),
        _ind("bio_01_h2h_countries", "Novel H2H Pathogen", "security_infrastructure",
             "Countries with novel human-to-human transmission (14-day)", "countries",
             0, "green", "stable", "WHO DON RSS", 1, 3),
        _ind("cdc_health_alerts", "CDC Health Alerts", "security_infrastructure",
             "CDC health alert network notices (30-day)", "alerts",
             2, "green", "stable", "CDC RSS", 5, 15),
        _ind("fema_disaster_declarations", "FEMA Disasters", "security_infrastructure",
             "FEMA disaster declarations (30-day)", "declarations",
             5, "green", "stable", "FEMA API", 10, 25),
        _ind("fda_drug_shortages", "FDA Drug Shortages", "security_infrastructure",
             "Active FDA drug shortage listings", "shortages",
             45, "amber", "stable", "FDA", 50, 100),
        _ind("supply_01_port_congestion", "Port Congestion", "security_infrastructure",
             "Ships waiting at major US ports", "ships",
             28, "amber", "up", "Marine Exchange", 20, 50),
        _ind("supply_02_freight_index", "Freight Index", "security_infrastructure",
             "Freightos Baltic Index", "index",
             1850, "green", "stable", "Freightos", 2500, 5000),
        _ind("supply_03_chip_lead_time", "Chip Lead Times", "security_infrastructure",
             "Semiconductor lead times (weeks)", "weeks",
             14, "amber", "up", "News RSS", 12, 20),
        _ind("supply_pharmacy_shortage", "Pharmacy Shortages", "security_infrastructure",
             "FDA drug shortage list additions (30-day)", "drugs",
             8, "amber", "up", "FDA", 5, 15),
        _ind("energy_02_nat_gas_storage", "Natural Gas Storage", "energy",
             "Natural gas storage vs 5-year average", "%",
             -5, "green", "stable", "EIA", -10, -20),
        _ind("energy_03_grid_emergency", "Grid Emergencies", "security_infrastructure",
             "NERC grid emergency declarations (30-day)", "emergencies",
             1, "green", "stable", "EIA", 2, 5),
        _ind("telecom_01_bgp_anomalies", "BGP Anomalies", "security_infrastructure",
             "BGP routing anomalies (24h)", "anomalies",
             45, "green", "stable", "BGPStream", 100, 500),
        _ind("telecom_02_cell_outages", "Cell Network Outages", "security_infrastructure",
             "Major cell network outages (7-day)", "outages",
             2, "green", "stable", "Downdetector", 5, 15, unavailable=True),
        _ind("telecom_03_undersea_cable", "Undersea Cable Events", "security_infrastructure",
             "Undersea cable damage/repair events (90-day)", "events",
             3, "amber", "up", "TeleGeography", 2, 5),
        _ind("water_01_reservoir_level", "Reservoir Levels", "water_infrastructure",
             "Major reservoir levels vs capacity", "%",
             68, "green", "stable", "USBR", 50, 30, unavailable=True),
        _ind("water_02_treatment_alerts", "Water Treatment Alerts", "water_infrastructure",
             "EPA water treatment violations (30-day)", "violations",
             15, "amber", "up", "EPA SDWIS", 10, 30),
        _ind("flight_01_ground_stops", "FAA Ground Stops", "security_infrastructure",
             "FAA ground stop events (7-day)", "events",
             3, "green", "stable", "FAA", 5, 15),
        _ind("flight_02_delay_pct", "Flight Delays", "security_infrastructure",
             "Flights delayed >15 min (%)", "%",
             18, "green", "stable", "FAA", 25, 40),
        _ind("flight_03_tfr_count", "Temporary Flight Restrictions", "security_infrastructure",
             "Active TFRs (non-standard)", "TFRs",
             12, "green", "stable", "FAA", 20, 40),
        _ind("travel_03_tsa_throughput", "TSA Throughput", "security_infrastructure",
             "TSA checkpoint throughput vs 2019", "%",
             95, "green", "stable", "TSA", 80, 60),

        # ── Oil & Energy ──
        _ind("oil_03_ofac_designations", "OFAC Designations", "oil_axis",
             "OFAC sanctions designations (30-day count)", "designations",
             0, "green", "stable", "Treasury OFAC", 1, 5),
        _ind("spr_01_level", "Strategic Petroleum Reserve", "oil_axis",
             "SPR level vs 10-year average", "%",
             -42, "red", "down", "EIA", -20, -35),

        # ── AI Window ──
        _ind("labor_ai_01_layoffs", "AI-Linked Layoffs", "ai_window",
             "Monthly workers laid off citing AI/automation", "workers",
             3200, "green", "stable", "Layoffs.fyi RSS", 5000, 25000),
        _ind("cult_media_01_trends", "AI Religion Trends", "ai_window",
             "Google Trends score for 'AI religion' (US weekly)", "score",
             8, "green", "stable", "Google Trends", 15, 40),

        # ── Global Conflict ──
        _ind("global_conflict_intensity", "Global Battle Intensity", "global_conflict",
             "ACLED global battle-related events 90-day average", "events/day",
             720, "amber", "up", "News RSS", 500, 2000),
        _ind("taiwan_pla_activity", "Taiwan PLA Incursions", "global_conflict",
             "PLA aircraft incursions into Taiwan ADIZ (14-day avg)", "aircraft/day",
             28, "amber", "up", "Taiwan MND", 20, 100),
        _ind("nato_high_readiness", "NATO High Readiness", "global_conflict",
             "NATO high-readiness force activations", "activations",
             0, "green", "stable", "NATO News RSS", 1, 2, critical=True),
        _ind("nuclear_test_activity", "Nuclear/Missile Tests", "global_conflict",
             "Nuclear detonation or ICBM tests (90-day count)", "tests",
             1, "green", "stable", "News RSS", 2, 10),
        _ind("defense_spending_growth", "Defense Spending Growth", "global_conflict",
             "Global defense spending year-over-year growth", "%",
             6.2, "amber", "up", "SIPRI RSS", 5, 15),
        _ind("travel_01_advisories", "Travel Advisories", "global_conflict",
             "Countries with Level 3-4 travel advisories", "countries",
             18, "green", "stable", "State Dept", 25, 40),
        _ind("hormuz_war_risk", "Hormuz War Risk", "global_conflict",
             "Lloyd's war risk insurance premium", "%",
             0.8, "amber", "up", "News RSS", 0.5, 1.5),

        # ── Domestic Control ──
        _ind("travel_02_border_wait", "Border Wait Times", "domestic_control",
             "Average US border crossing wait time", "minutes",
             45, "green", "stable", "CBP", 60, 120),
        _ind("ice_detention_surge", "ICE Detention Population", "domestic_control",
             "ICE detention population", "detainees",
             62000, "amber", "up", "ICE Statistics", 50000, 150000, unavailable=True),
        _ind("federal_regulations", "Federal Regulations", "domestic_control",
             "Significant federal regulations (7-day)", "regulations",
             5, "green", "stable", "Federal Register", 10, 25),
        _ind("congress_activity", "Congressional Activity", "domestic_control",
             "Congressional votes and actions (7-day)", "actions",
             15, "green", "stable", "GovTrack", 20, 50),
    ]


def get_indicators_with_live_data() -> Dict[str, Any]:
    """
    Merge live-collected data into the full indicator set.
    Live data overrides mock for matching IDs.
    """
    mock_indicators = get_all_mock_indicators()
    live_count = 0

    if data_service:
        try:
            live_data = data_service.collect_all()
            live_by_id = {ind['id']: ind for ind in live_data}

            for i, mock in enumerate(mock_indicators):
                if mock['id'] in live_by_id:
                    mock_indicators[i] = live_by_id[mock['id']]
                    live_count += 1
        except Exception as e:
            logger.error(f"Live collection error, serving mock: {e}")

    logger.info(f"Serving {len(mock_indicators)} indicators ({live_count} live, {len(mock_indicators) - live_count} mock)")

    return {
        "indicators": mock_indicators,
        "timestamp": _now(),
        "live_count": live_count,
        "total_count": len(mock_indicators),
    }


# ─── Compute HOPI score from current indicators ───

def compute_hopi(indicators: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute HOPI score from current indicator states."""
    from collections import defaultdict

    DOMAIN_WEIGHTS = {
        'economy': 1.0, 'jobs_labor': 1.0, 'rights_governance': 1.0,
        'security_infrastructure': 1.25, 'oil_axis': 1.0, 'ai_window': 1.0,
        'global_conflict': 1.5, 'domestic_control': 1.25, 'cult': 0.75,
    }
    LEVEL_SCORES = {'green': 0.0, 'amber': 0.5, 'red': 1.0, 'unknown': 0.3}

    domain_indicators: Dict[str, List] = defaultdict(list)
    domain_critical: Dict[str, List] = defaultdict(list)

    for ind in indicators:
        domain = ind.get('domain', 'economy')
        level = ind.get('status', {}).get('level', 'unknown')
        domain_indicators[domain].append(ind)
        if ind.get('critical') and level == 'red':
            domain_critical[domain].append(ind['id'])

    domains = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for domain, weight in DOMAIN_WEIGHTS.items():
        inds = domain_indicators.get(domain, [])
        if not inds:
            domains[domain] = {"score": 0, "weight": weight, "indicators": [], "criticalAlerts": []}
            continue

        scores = [LEVEL_SCORES.get(i['status']['level'], 0.3) for i in inds]
        avg = sum(scores) / len(scores)
        domains[domain] = {
            "score": round(avg, 2),
            "weight": weight,
            "indicators": [i['id'] for i in inds],
            "criticalAlerts": domain_critical.get(domain, []),
        }
        weighted_sum += avg * weight
        total_weight += weight

    hopi = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0

    # Determine phase from HOPI score
    red_count = sum(1 for i in indicators if i['status']['level'] == 'red')
    amber_count = sum(1 for i in indicators if i['status']['level'] == 'amber')

    if red_count >= 3:
        phase = 6
    elif red_count >= 2:
        phase = 4
    elif red_count >= 1 or amber_count >= 2:
        phase = 3
    elif amber_count >= 1:
        phase = 2
    else:
        phase = 1

    return {
        "score": hopi,
        "confidence": 88,
        "phase": phase,
        "targetPhase": phase,
        "domains": domains,
        "timestamp": _now(),
    }


# ═══════════════════════════════════════════════
# Routes — match frontend API paths exactly
# ═══════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "name": "Canairy",
        "version": "2.2.0",
        "status": "operational",
        "docs": "/docs",
        "live_collectors": list(data_service._collectors.keys()) if data_service else [],
    }


@app.get("/api/indicators")
async def get_indicators():
    """All indicators — live where available, mock elsewhere."""
    return get_indicators_with_live_data()


# Also serve on /api/v1/ paths for backwards compatibility
@app.get("/api/v1/indicators/")
async def get_indicators_v1():
    return get_indicators_with_live_data()


@app.get("/api/indicators/{indicator_id}")
async def get_indicator(indicator_id: str):
    """Single indicator by ID."""
    data = get_indicators_with_live_data()
    for ind in data["indicators"]:
        if ind["id"] == indicator_id:
            return ind
    return {"error": "Not found", "id": indicator_id}


@app.get("/api/hopi")
async def get_hopi():
    """HOPI score computed from current indicators."""
    data = get_indicators_with_live_data()
    return compute_hopi(data["indicators"])


@app.get("/api/v1/hopi")
async def get_hopi_v1():
    return await get_hopi()


@app.get("/api/status")
async def get_status():
    """System status."""
    data = get_indicators_with_live_data()
    red_count = sum(1 for i in data["indicators"] if i["status"]["level"] == "red")
    return {
        "operational": True,
        "lastUpdate": _now(),
        "activeAlerts": red_count,
        "dataQuality": round(data["live_count"] / max(data["total_count"], 1) * 100) if data["live_count"] > 0 else 88,
        "message": f"Monitoring {data['total_count']} indicators ({data['live_count']} live).",
    }


@app.get("/api/v1/status")
async def get_status_v1():
    return await get_status()


@app.get("/api/phase")
async def get_phase():
    """Current recommended phase."""
    data = get_indicators_with_live_data()
    hopi = compute_hopi(data["indicators"])
    phase_num = hopi["phase"]

    PHASE_NAMES = {
        0: "Foundations", 1: "72-Hour Bin", 2: "Digital & Comms",
        3: "Air, Health, Mobile", 4: "Dry-Basement / Perimeter",
        5: "Oil-Tank → Generator Prep", 6: "Shelter Nook Build",
        7: "Harden + Genset Live", 8: "Water & Circuits",
        9: "Optional Safe-Room",
    }
    PHASE_COLORS = {
        0: "#10B981", 1: "#10B981", 2: "#10B981", 3: "#F59E0B",
        4: "#F59E0B", 5: "#F97316", 6: "#F97316", 7: "#EF4444",
        8: "#EF4444", 9: "#991B1B",
    }

    return {
        "number": phase_num,
        "name": PHASE_NAMES.get(phase_num, "Unknown"),
        "description": f"Phase {phase_num} activated based on current indicator readings.",
        "triggers": [f"Based on {hopi['score']:.0%} HOPI score"],
        "actions": [],
        "color": PHASE_COLORS.get(phase_num, "#6B7280"),
    }


@app.get("/api/v1/phase")
async def get_phase_v1():
    return await get_phase()


@app.post("/api/indicators/refresh-all")
async def refresh_all():
    """Invalidate cache and re-collect."""
    if data_service:
        data_service.invalidate_cache()
    return {"status": "ok", "message": "Cache invalidated, next request will re-collect."}


@app.post("/api/indicators/{indicator_id}/refresh")
async def refresh_indicator(indicator_id: str):
    """Refresh a single indicator."""
    if data_service:
        data_service.invalidate_cache()
    return await get_indicator(indicator_id)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5555))
    uvicorn.run("simple_main:app", host="0.0.0.0", port=port, reload=True)
