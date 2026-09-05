"""
Data service that wraps collectors with caching and maps IDs to frontend expectations.
Collectors that can fetch real data (no API key needed) are marked as 'live'.
Others gracefully fall back to mock data.
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# Import individual collector files directly, bypassing collectors/__init__.py
# which imports everything and can fail due to missing optional dependencies.
import importlib.util

def _load_collector(filename: str, class_name: str):
    """Load a collector class directly from its .py file."""
    filepath = src_path / "collectors" / filename
    if not filepath.exists():
        logger.warning(f"Collector file not found: {filepath}")
        return None
    try:
        # First ensure the base module is available
        base_path = src_path / "collectors" / "base.py"
        if "collectors.base" not in sys.modules:
            spec = importlib.util.spec_from_file_location("collectors.base", str(base_path))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["collectors.base"] = mod
            spec.loader.exec_module(mod)

        spec = importlib.util.spec_from_file_location(f"collectors.{filename[:-3]}", str(filepath))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, class_name)
    except Exception as e:
        logger.warning(f"Cannot load {class_name} from {filename}: {e}")
        return None

# Load API keys from secrets.yaml into environment
def _load_secrets():
    """Load API keys from secrets.yaml into environment variables."""
    secrets_path = Path(__file__).parent.parent / "config" / "secrets.yaml"
    if secrets_path.exists():
        try:
            import yaml
            with open(secrets_path) as f:
                secrets = yaml.safe_load(f)
            api_keys = secrets.get('api_keys', {})
            for key, value in api_keys.items():
                if value and not os.environ.get(key):
                    os.environ[key] = str(value)
                    logger.info(f"Loaded API key: {key}")
            # Also load specific keys explicitly
            for key in ['CONGRESS_API_KEY', 'DATA_GOV_API_KEY', 'OPENSTATES_API_KEY', 'COURTLISTENER_API_KEY']:
                if key in api_keys and api_keys[key]:
                    os.environ[key] = str(api_keys[key])
        except Exception as e:
            logger.warning(f"Could not load secrets.yaml: {e}")

_load_secrets()

# These collectors have minimal dependencies (requests, feedparser)
# Core collectors (already working)
_CISACyberCollector = _load_collector("cisa_cyber.py", "CISACyberCollector")
_WHODiseaseCollector = _load_collector("who_disease.py", "WHODiseaseCollector")
_GroceryCPICollector = _load_collector("grocery_cpi.py", "GroceryCPICollector")
_TreasuryCollector = _load_collector("treasury.py", "TreasuryCollector")
_JoblessClaimsCollector = _load_collector("jobless_claims.py", "JoblessClaimsCollector")
_GDPGrowthCollector = _load_collector("gdp_growth.py", "GDPGrowthCollector")
_MarketVolatilityCollector = _load_collector("market_volatility.py", "MarketVolatilityCollector")
_TreasuryAuctionCollector = _load_collector("treasury_auctions.py", "TreasuryAuctionCollector")
_NWSAlertsCollector = _load_collector("nws_alerts.py", "NWSAlertsCollector")
_ACLEDProtestsCollector = _load_collector("acled_protests.py", "ACLEDProtestsCollector")
_EIASPRCollector = _load_collector("eia_energy.py", "EIASPRCollector")

# FAA collectors (free API)
_FAAGroundStopsCollector = _load_collector("faa_flights.py", "FAAGroundStopsCollector")
_FAAFlightDelaysCollector = _load_collector("faa_flights.py", "FAAFlightDelaysCollector")
_FAATFRCollector = _load_collector("faa_flights.py", "FAATFRCollector")

# State Dept / Travel (free)
_StateDeptAdvisoryCollector = _load_collector("state_dept_travel.py", "StateDeptAdvisoryCollector")

# CBP / TSA (free)
_CBPBorderWaitCollector = _load_collector("cbp_travel.py", "CBPBorderWaitCollector")
_TSAThroughputCollector = _load_collector("cbp_travel.py", "TSAThroughputCollector")

# Banking (free - FDIC)
_FDICBankFailuresCollector = _load_collector("fdic_banks.py", "FDICBankFailuresCollector")
_FedDiscountWindowCollector = _load_collector("fdic_banks.py", "FedDiscountWindowCollector")
_FedDepositsCollector = _load_collector("fdic_banks.py", "FedDepositsCollector")

# EIA extras (already have API key)
_EIANaturalGasCollector = _load_collector("eia_energy.py", "EIANaturalGasCollector")
_EIAGridEmergencyCollector = _load_collector("eia_energy.py", "EIAGridEmergencyCollector")

# Labor (free - Cornell ILR)
_StrikeTrackerCollector = _load_collector("strike_tracker.py", "StrikeTrackerCollector")

# Taiwan (web scraping - no API key)
_TaiwanPLACollector = _load_collector("taiwan_pla.py", "TaiwanPLACollector")

# Supply chain (free APIs)
_PortCongestionCollector = _load_collector("supply_chain.py", "PortCongestionCollector")
_FreightIndexCollector = _load_collector("supply_chain.py", "FreightIndexCollector")

# Pharmacy shortages (FDA - free)
_PharmacyShortageCollector = _load_collector("pharmacy_shortage.py", "PharmacyShortageCollector")

# Global conflict (ACLED - have key)
_GlobalConflictCollector = _load_collector("global_conflict.py", "GlobalConflictCollector")

# Congress.gov (free - LegiScan workaround)
_CongressBillsCollector = _load_collector("congress_bills.py", "CongressBillsCollector")

# USDA collectors (Data.gov API key)
_USDACropConditionCollector = _load_collector("usda_crops.py", "USDACropConditionCollector")
_USDALivestockDiseaseCollector = _load_collector("usda_crops.py", "USDALivestockDiseaseCollector")
_USDAMeatProcessingCollector = _load_collector("usda_crops.py", "USDAMeatProcessingCollector")
_FertilizerPriceCollector = _load_collector("fertilizer_price.py", "FertilizerPriceCollector")

# Water infrastructure collectors
_ReservoirLevelCollector = _load_collector("water_infra.py", "ReservoirLevelCollector")
_EPAWaterAlertsCollector = _load_collector("water_infra.py", "EPAWaterAlertsCollector")
_DroughtMonitorCollector = _load_collector("water_infra.py", "DroughtMonitorCollector")

# Treasury/OFAC collector
_OFACSanctionsCollector = _load_collector("ofac_sanctions.py", "OFACSanctionsCollector")

# Telecom infrastructure collectors
_BGPAnomaliesCollector = _load_collector("telecom_infra.py", "BGPAnomaliesCollector")
_CellOutagesCollector = _load_collector("telecom_infra.py", "CellOutagesCollector")
_UnderseaCableCollector = _load_collector("telecom_infra.py", "UnderseaCableCollector")

# RSS feed collectors (free alternatives to paid APIs)
_ProtestNewsCollector = _load_collector("rss_feeds.py", "ProtestNewsCollector")
_GlobalConflictNewsCollector = _load_collector("rss_feeds.py", "GlobalConflictNewsCollector")
_NATONewsCollector = _load_collector("rss_feeds.py", "NATONewsCollector")
_DefenseSpendingCollector = _load_collector("rss_feeds.py", "DefenseSpendingCollector")
_AILayoffsCollector = _load_collector("rss_feeds.py", "AILayoffsCollector")
_NuclearTestsCollector = _load_collector("rss_feeds.py", "NuclearTestsCollector")

# Free alternatives to paid APIs
_YahooLuxuryIndexCollector = _load_collector("free_alternatives.py", "YahooLuxuryIndexCollector")
_EIAOilInventoryCollector = _load_collector("free_alternatives.py", "EIAOilInventoryCollector")
_SemiconductorLeadTimeCollector = _load_collector("free_alternatives.py", "SemiconductorLeadTimeCollector")
_ICEDetentionCollector = _load_collector("free_alternatives.py", "ICEDetentionCollector")
_HormuzRiskCollector = _load_collector("free_alternatives.py", "HormuzRiskCollector")
_MortgageDelinquencyCollector = _load_collector("free_alternatives.py", "MortgageDelinquencyCollector")
_GoogleTrendsCollector = _load_collector("free_alternatives.py", "GoogleTrendsCollector")

# OpenStates (state legislation tracking)
_OpenStatesAISurveillanceCollector = _load_collector("openstates.py", "OpenStatesAISurveillanceCollector")

# CourtListener (civil liberties cases)
_CourtListenerLibertyCollector = _load_collector("courtlistener.py", "CourtListenerLibertyCollector")

# Government RSS feeds (no auth required)
_SECFilingsCollector = _load_collector("gov_rss_feeds.py", "SECFilingsCollector")
_FederalRegisterCollector = _load_collector("gov_rss_feeds.py", "FederalRegisterCollector")
_FEMADisasterCollector = _load_collector("gov_rss_feeds.py", "FEMADisasterCollector")
_CDCHealthAlertsCollector = _load_collector("gov_rss_feeds.py", "CDCHealthAlertsCollector")
_FDAShortagesCollector = _load_collector("gov_rss_feeds.py", "FDAShortagesCollector")
_GovTrackBillsCollector = _load_collector("gov_rss_feeds.py", "GovTrackBillsCollector")

# Freddie Mac (mortgage rates)
_FreddieMacPMMSCollector = _load_collector("freddie_mac.py", "FreddieMacPMMSCollector")

# ─── ID mapping: collector key → frontend indicator ID ───
COLLECTOR_TO_FRONTEND_ID = {
    # Core
    'cisa_cyber':         'cyber_01_cisa_kev',
    'who_disease':        'bio_01_h2h_countries',
    'grocery_cpi':        'econ_02_grocery_cpi',
    'treasury':           'econ_01_treasury_tail',
    'treasury_auctions':  'econ_01_treasury_tail',
    'jobless_claims':     'job_01_jobless_claims',
    'gdp_growth':         'green_g1_gdp_rates',
    'market_volatility':  'market_01_intraday_swing',
    'nws_alerts':         'grid_01_pjm_outages',
    'acled_protests':     'civil_01_acled_protests',
    'eia_spr':            'spr_01_level',
    # FAA - fixed IDs to match mock data
    'faa_ground_stops':   'flight_01_ground_stops',
    'faa_delays':         'flight_02_delay_pct',
    'faa_tfr':            'flight_03_tfr_count',
    # Travel
    'state_dept':         'travel_01_advisories',
    'cbp_border':         'travel_02_border_wait',
    'tsa_throughput':     'travel_03_tsa_throughput',
    # Banking
    'fdic_failures':      'bank_01_failures',
    'fed_discount':       'bank_02_discount_window',
    'fed_deposits':       'bank_03_deposit_flow',
    # Energy extras
    'eia_natgas':         'energy_02_nat_gas_storage',
    'eia_grid':           'energy_03_grid_emergency',
    # Labor
    'strike_tracker':     'job_01_strike_days',
    # Taiwan
    'taiwan_pla':         'taiwan_pla_activity',
    # Supply chain
    'port_congestion':    'supply_01_port_congestion',
    'freight_index':      'supply_02_freight_index',
    # Pharmacy
    'pharmacy_shortage':  'supply_pharmacy_shortage',
    # Global conflict
    'global_conflict':    'global_conflict_intensity',
    # Congress
    'congress_bills':     'hill_control_legislation',
    # Water infrastructure (food removed - no working sources)
    'epa_water':          'water_01_treatment_alerts',
    # Treasury/OFAC
    'ofac_sanctions':     'oil_03_ofac_designations',
    # Telecom infrastructure
    'undersea_cable':     'telecom_01_undersea_cable',
    'bgp_anomalies':      'telecom_02_bgp_anomalies',
    'cell_outages':       'telecom_03_cell_outages',
    # RSS alternatives (ACLED replacement)
    'protest_news':       'civil_01_acled_protests',
    'conflict_news':      'global_conflict_intensity',
    # More RSS collectors
    'nato_news':          'nato_high_readiness',
    'defense_spending':   'defense_spending_growth',
    'ai_layoffs':         'labor_ai_01_layoffs',
    'nuclear_tests':      'nuclear_test_activity',
    # Free alternatives to paid APIs
    'luxury_index':       'luxury_01_collapse',
    # 'oil_inventory' - no matching frontend indicator
    'chip_lead_time':     'supply_03_chip_lead_time',
    'ice_detention':      'ice_detention_surge',
    'hormuz_risk':        'hormuz_war_risk',
    'mortgage_delinq':    'housing_01_delinquency',
    'ai_religion':        'cult_media_01_trends',
    # New collectors
    'openstates':         'power_01_ai_surveillance',
    'courtlistener':      'liberty_litigation_count',
    'sec_filings':        'sec_8k_filings',
    'federal_register':   'federal_regulations',
    'fema_disasters':     'fema_disaster_declarations',
    'cdc_alerts':         'cdc_health_alerts',
    'fda_shortages':      'fda_drug_shortages',
    'govtrack':           'congress_activity',
    'freddie_mac':        'housing_03_rate_shock',
}

# ─── Frontend indicator metadata (matches mockData.ts shape) ───
INDICATOR_META: Dict[str, Dict[str, Any]] = {
    'cyber_01_cisa_kev': {
        'name': 'Cyber Threat Level',
        'domain': 'security_infrastructure',
        'description': 'CISA KEV + ICS per week — active exploitation of infrastructure systems means utilities and banking could go down',
        'unit': 'vulns/wk',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'CISA KEV / ICS-CERT',
        'updateFrequency': 'Weekly',
    },
    'bio_01_h2h_countries': {
        'name': 'Novel Pathogen Risk',
        'domain': 'security_infrastructure',
        'description': 'Novel H2H transmission events — a new pandemic means masks, sealed rooms, prescription stockpiles',
        'unit': 'events',
        'thresholds': {'green': {'max': 0}, 'amber': {'min': 1, 'max': 2}, 'red': {'min': 2}, 'threshold_amber': 1, 'threshold_red': 2},
        'critical': False,
        'dataSource': 'WHO DON',
        'updateFrequency': 'Daily',
    },
    'econ_02_grocery_cpi': {
        'name': 'Grocery Prices',
        'domain': 'economy',
        'description': 'Grocery CPI 3-month annualized — directly hits your weekly grocery bill',
        'unit': '%',
        'thresholds': {'green': {'max': 3.5}, 'amber': {'min': 3.5, 'max': 6}, 'red': {'min': 6}, 'threshold_amber': 3.5, 'threshold_red': 6},
        'critical': False,
        'dataSource': 'BLS API',
        'updateFrequency': 'Monthly',
    },
    'econ_01_treasury_tail': {
        'name': 'Treasury Market Stress',
        'domain': 'economy',
        'description': '10-year Treasury auction tail in basis points — signals global confidence in US debt',
        'unit': 'bps',
        'thresholds': {'green': {'max': 2}, 'amber': {'min': 2, 'max': 4}, 'red': {'min': 4}, 'threshold_amber': 2, 'threshold_red': 4},
        'critical': False,
        'dataSource': 'Treasury / FRED',
        'updateFrequency': 'Per auction',
    },
    'green_g1_gdp_rates': {
        'name': 'Economic Growth',
        'domain': 'economy',
        'description': 'US real GDP growth rate — when economy contracts, jobs disappear and prices stay high',
        'unit': '%',
        'thresholds': {'green': {'min': 2}, 'amber': {'min': 0, 'max': 2}, 'red': {'max': 0}, 'threshold_amber': 2, 'threshold_red': 0},
        'greenFlag': True,
        'dataSource': 'BEA / FRED',
        'updateFrequency': 'Quarterly',
    },
    'market_01_intraday_swing': {
        'name': 'Market Volatility',
        'domain': 'economy',
        'description': '10-year Treasury intraday swing — wild swings mean institutions are panicking',
        'unit': 'bps',
        'thresholds': {'green': {'max': 15}, 'amber': {'min': 15, 'max': 30}, 'red': {'min': 30}, 'threshold_amber': 15, 'threshold_red': 30},
        'critical': True,
        'dataSource': 'Bloomberg / FRED',
        'updateFrequency': 'Real-time',
    },
    'job_01_strike_days': {
        'name': 'Strike Activity',
        'domain': 'jobs_labor',
        'description': 'Strike days (thousands, trailing 30 days) — major strikes shut down ports, hospitals, transit',
        'unit': 'K days',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 20}, 'red': {'min': 20}, 'threshold_amber': 5, 'threshold_red': 20},
        'critical': False,
        'dataSource': 'BLS / Cornell ILR',
        'updateFrequency': 'Weekly',
    },
    'grid_01_pjm_outages': {
        'name': 'Power Grid Reliability',
        'domain': 'security_infrastructure',
        'description': 'Severe weather alerts + grid events — when the grid is stressed, blackouts happen',
        'unit': 'alerts',
        'thresholds': {'green': {'max': 50}, 'amber': {'min': 50, 'max': 100}, 'red': {'min': 100}, 'threshold_amber': 50, 'threshold_red': 100},
        'critical': False,
        'dataSource': 'NWS + PJM',
        'updateFrequency': 'Real-time',
    },
    'civil_01_acled_protests': {
        'name': 'Civil Protest Activity',
        'domain': 'rights_governance',
        'description': 'US protest events per week — high frequency signals social tension affecting supply chains and services',
        'unit': 'events/wk',
        'thresholds': {'green': {'max': 20}, 'amber': {'min': 20, 'max': 50}, 'red': {'min': 50}, 'threshold_amber': 20, 'threshold_red': 50},
        'critical': False,
        'dataSource': 'ACLED',
        'updateFrequency': 'Weekly',
    },
    'spr_01_level': {
        'name': 'Strategic Oil Reserves',
        'domain': 'energy',
        'description': 'US SPR level — when depleted, any supply shock hits gas and heating oil immediately',
        'unit': 'M bbl',
        'thresholds': {'green': {'min': 400}, 'amber': {'min': 350, 'max': 400}, 'red': {'max': 350}, 'threshold_amber': 400, 'threshold_red': 350},
        'critical': False,
        'dataSource': 'EIA',
        'updateFrequency': 'Weekly',
    },
    'job_01_jobless_claims': {
        'name': 'Jobless Claims',
        'domain': 'jobs_labor',
        'description': 'Weekly initial unemployment claims — when layoffs spike, your income is at risk',
        'unit': 'K/week',
        'thresholds': {'green': {'max': 250}, 'amber': {'min': 250, 'max': 350}, 'red': {'min': 350}, 'threshold_amber': 250, 'threshold_red': 350},
        'critical': False,
        'dataSource': 'DOL / FRED',
        'updateFrequency': 'Weekly',
    },
    # FAA
    'flight_01_ground_stops': {
        'name': 'FAA Ground Stops',
        'domain': 'aviation',
        'description': 'Ground stops per week (non-weather) — something is wrong with the system',
        'unit': 'stops/wk',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'FAA',
        'updateFrequency': 'Real-time',
    },
    'flight_02_delay_pct': {
        'name': 'Flight Delay Rate',
        'domain': 'aviation',
        'description': 'Percent of flights delayed — when 40% are delayed, evacuation speed suffers',
        'unit': '%',
        'thresholds': {'green': {'max': 25}, 'amber': {'min': 25, 'max': 40}, 'red': {'min': 40}, 'threshold_amber': 25, 'threshold_red': 40},
        'critical': False,
        'dataSource': 'FAA / BTS',
        'updateFrequency': 'Daily',
    },
    'flight_03_tfr_count': {
        'name': 'TFR Count',
        'domain': 'aviation',
        'description': 'Active non-standard TFRs — lots of them = military activity or security events',
        'unit': 'TFRs',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'FAA',
        'updateFrequency': 'Real-time',
    },
    # Travel
    'travel_01_advisories': {
        'name': 'Travel Advisories',
        'domain': 'travel_mobility',
        'description': 'Countries at Level 3+ — travel advisories limit your escape routes',
        'unit': 'countries',
        'thresholds': {'green': {'max': 15}, 'amber': {'min': 15, 'max': 25}, 'red': {'min': 25}, 'threshold_amber': 15, 'threshold_red': 25},
        'critical': False,
        'dataSource': 'State Dept',
        'updateFrequency': 'Daily',
    },
    'travel_02_border_wait': {
        'name': 'Border Wait Times',
        'domain': 'travel_mobility',
        'description': 'Average wait at crossings — long waits or closures mean leaving gets harder',
        'unit': 'min',
        'thresholds': {'green': {'max': 60}, 'amber': {'min': 60, 'max': 120}, 'red': {'min': 120}, 'threshold_amber': 60, 'threshold_red': 120},
        'critical': False,
        'dataSource': 'CBP',
        'updateFrequency': 'Real-time',
    },
    'travel_03_tsa_throughput': {
        'name': 'Airport Throughput',
        'domain': 'travel_mobility',
        'description': 'TSA passengers per day — throughput cratering means people can\'t or won\'t fly',
        'unit': 'K/day',
        'thresholds': {'green': {'min': 1500}, 'amber': {'min': 800, 'max': 1500}, 'red': {'max': 800}, 'threshold_amber': 1500, 'threshold_red': 800},
        'critical': False,
        'dataSource': 'TSA',
        'updateFrequency': 'Daily',
    },
    # Banking
    'bank_01_failures': {
        'name': 'Bank Failures',
        'domain': 'economy',
        'description': 'FDIC-insured bank failures (trailing 12 months) — deposits could be frozen temporarily',
        'unit': 'banks',
        'thresholds': {'green': {'max': 3}, 'amber': {'min': 3, 'max': 6}, 'red': {'min': 6}, 'threshold_amber': 3, 'threshold_red': 6},
        'critical': False,
        'dataSource': 'FDIC',
        'updateFrequency': 'Weekly',
    },
    'bank_02_discount_window': {
        'name': 'Bank Discount Window',
        'domain': 'economy',
        'description': 'Fed discount window borrowing — the banking system\'s check engine light',
        'unit': '$B',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 20}, 'red': {'min': 20}, 'threshold_amber': 5, 'threshold_red': 20},
        'critical': False,
        'dataSource': 'Federal Reserve',
        'updateFrequency': 'Weekly',
    },
    'bank_03_deposit_flow': {
        'name': 'Bank Deposit Flow',
        'domain': 'economy',
        'description': 'Weekly change in deposits — money fleeing banks means people don\'t trust the system',
        'unit': '%',
        'thresholds': {'green': {'min': -0.5}, 'amber': {'min': -2, 'max': -0.5}, 'red': {'max': -2}, 'threshold_amber': -0.5, 'threshold_red': -2},
        'critical': False,
        'dataSource': 'Federal Reserve H.8',
        'updateFrequency': 'Weekly',
    },
    # Energy extras
    'energy_02_nat_gas_storage': {
        'name': 'Natural Gas Storage',
        'domain': 'energy',
        'description': 'Gas storage vs 5-year average — low storage heading into winter means heating costs spike',
        'unit': '% vs avg',
        'thresholds': {'green': {'min': -15}, 'amber': {'min': -30, 'max': -15}, 'red': {'max': -30}, 'threshold_amber': -15, 'threshold_red': -30},
        'critical': False,
        'dataSource': 'EIA',
        'updateFrequency': 'Weekly',
    },
    'energy_03_grid_emergency': {
        'name': 'Energy Grid Emergency',
        'domain': 'energy',
        'description': 'Grid operator emergency declarations — rolling blackouts are on the table',
        'unit': 'declarations',
        'thresholds': {'green': {'max': 0}, 'amber': {'min': 1, 'max': 2}, 'red': {'min': 2}, 'threshold_amber': 1, 'threshold_red': 2},
        'critical': False,
        'dataSource': 'EIA / NERC',
        'updateFrequency': 'Real-time',
    },
    # Labor
    'job_02_strikes': {
        'name': 'US Strike Days',
        'domain': 'jobs_labor',
        'description': 'Active major work stoppages (1000+ workers)',
        'unit': 'strikes',
        'thresholds': {'green': {'max': 1}, 'amber': {'min': 1, 'max': 3}, 'red': {'min': 3}, 'threshold_amber': 1, 'threshold_red': 3},
        'critical': False,
        'dataSource': 'Cornell ILR',
        'updateFrequency': 'Daily',
    },
    # Geopolitical
    'taiwan_pla_activity': {
        'name': 'Taiwan Strait Activity',
        'domain': 'global_conflict',
        'description': 'PLA incursions per week — Taiwan makes 90% of advanced chips, conflict halts vehicle production',
        'unit': 'incursions/wk',
        'thresholds': {'green': {'max': 10}, 'amber': {'min': 10, 'max': 25}, 'red': {'min': 25}, 'threshold_amber': 10, 'threshold_red': 25},
        'critical': False,
        'dataSource': 'Taiwan MND',
        'updateFrequency': 'Daily',
    },
    'global_conflict_intensity': {
        'name': 'Global Conflict Level',
        'domain': 'global_conflict',
        'description': 'Battle events per week — drives oil prices, refugee flows, and risk of escalation',
        'unit': 'events/wk',
        'thresholds': {'green': {'max': 150}, 'amber': {'min': 150, 'max': 300}, 'red': {'min': 300}, 'threshold_amber': 150, 'threshold_red': 300},
        'critical': False,
        'dataSource': 'ACLED',
        'updateFrequency': 'Weekly',
    },
    # Supply chain
    'supply_01_port_congestion': {
        'name': 'Port Congestion',
        'domain': 'supply_chain',
        'description': 'Ships waiting at major US ports — ships waiting = shelves emptying',
        'unit': 'vessels',
        'thresholds': {'green': {'max': 20}, 'amber': {'min': 20, 'max': 50}, 'red': {'min': 50}, 'threshold_amber': 20, 'threshold_red': 50},
        'critical': False,
        'dataSource': 'Marine Exchange',
        'updateFrequency': 'Daily',
    },
    'supply_02_freight_index': {
        'name': 'Freight Cost Index',
        'domain': 'supply_chain',
        'description': 'Container freight index — high freight costs become high shelf prices within 60-90 days',
        'unit': '$/FEU',
        'thresholds': {'green': {'max': 3000}, 'amber': {'min': 3000, 'max': 6000}, 'red': {'min': 6000}, 'threshold_amber': 3000, 'threshold_red': 6000},
        'critical': False,
        'dataSource': 'Freightos FBX',
        'updateFrequency': 'Daily',
    },
    # Health
    'supply_pharmacy_shortage': {
        'name': 'FDA Drug Shortages',
        'domain': 'security_infrastructure',
        'description': 'Drugs in shortage — when prescriptions aren\'t available, a 90-day buffer is the difference',
        'unit': 'drugs',
        'thresholds': {'green': {'max': 100}, 'amber': {'min': 100, 'max': 200}, 'red': {'min': 200}, 'threshold_amber': 100, 'threshold_red': 200},
        'critical': False,
        'dataSource': 'FDA / ASHP',
        'updateFrequency': 'Weekly',
    },
    # Congress
    'hill_control_legislation': {
        'name': 'Control Bills Advancing',
        'domain': 'domestic_control',
        'description': 'Bills related to AI, surveillance, emergency powers advancing in Congress',
        'unit': 'bills',
        'thresholds': {'green': {'max': 3}, 'amber': {'min': 3, 'max': 8}, 'red': {'min': 8}, 'threshold_amber': 3, 'threshold_red': 8},
        'critical': False,
        'dataSource': 'Congress.gov',
        'updateFrequency': 'Daily',
    },
    # Food Production
    'food_01_crop_condition': {
        'name': 'Crop Conditions',
        'domain': 'food_production',
        'description': 'Major crops rated Good/Excellent — domestic food supply health',
        'unit': '%',
        'thresholds': {'green': {'min': 60}, 'amber': {'min': 40, 'max': 60}, 'red': {'max': 40}, 'threshold_amber': 60, 'threshold_red': 40},
        'critical': False,
        'dataSource': 'USDA NASS',
        'updateFrequency': 'Weekly',
    },
    'food_02_livestock_disease': {
        'name': 'Livestock Disease Alerts',
        'domain': 'food_production',
        'description': 'Active USDA animal disease emergencies — meat supply and zoonotic risk',
        'unit': 'alerts',
        'thresholds': {'green': {'max': 1}, 'amber': {'min': 1, 'max': 3}, 'red': {'min': 3}, 'threshold_amber': 1, 'threshold_red': 3},
        'critical': False,
        'dataSource': 'USDA APHIS',
        'updateFrequency': 'Daily',
    },
    'food_03_fertilizer_price': {
        'name': 'Fertilizer Price Index',
        'domain': 'food_production',
        'description': 'DAP/Urea price vs 5-year average — food price leading indicator',
        'unit': '% of avg',
        'thresholds': {'green': {'max': 120}, 'amber': {'min': 120, 'max': 180}, 'red': {'min': 180}, 'threshold_amber': 120, 'threshold_red': 180},
        'critical': False,
        'dataSource': 'World Bank',
        'updateFrequency': 'Monthly',
    },
    'food_04_processing_capacity': {
        'name': 'Meat Processing Capacity',
        'domain': 'food_production',
        'description': 'Slaughter capacity utilization — supply chain health',
        'unit': '%',
        'thresholds': {'green': {'min': 85}, 'amber': {'min': 70, 'max': 85}, 'red': {'max': 70}, 'threshold_amber': 85, 'threshold_red': 70},
        'critical': False,
        'dataSource': 'USDA AMS',
        'updateFrequency': 'Daily',
    },
    # Water Infrastructure
    'water_01_treatment_alerts': {
        'name': 'Water Treatment Alerts',
        'domain': 'water_infrastructure',
        'description': 'Serious violations in region — tap water may not be safe, stored water is backup',
        'unit': 'violations/qtr',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'EPA SDWIS',
        'updateFrequency': 'Daily',
    },
    'water_02_reservoir_level': {
        'name': 'Reservoir Levels',
        'domain': 'water_infrastructure',
        'description': 'Regional reservoir capacity — low levels mean water restrictions and eventually rationing',
        'unit': '%',
        'thresholds': {'green': {'min': 60}, 'amber': {'min': 40, 'max': 60}, 'red': {'max': 40}, 'threshold_amber': 60, 'threshold_red': 40},
        'critical': False,
        'dataSource': 'USBR / NJ DEP',
        'updateFrequency': 'Weekly',
    },
    # OFAC/Treasury
    'ofac_01_designations': {
        'name': 'OFAC Sanctions (Oil)',
        'domain': 'oil_dollar',
        'description': 'OFAC sanctions designations targeting oil trade entities (30-day count)',
        'unit': 'designations',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'OFAC Treasury',
        'updateFrequency': 'Daily',
    },
    # Telecom Infrastructure
    'telecom_01_undersea_cable': {
        'name': 'Undersea Cable Incidents',
        'domain': 'telecommunications',
        'description': 'Cable cuts — cables carry 95% of intercontinental data, multiple cuts = potential sabotage',
        'unit': 'incidents/mo',
        'thresholds': {'green': {'max': 1}, 'amber': {'min': 1, 'max': 3}, 'red': {'min': 3}, 'threshold_amber': 1, 'threshold_red': 3},
        'critical': False,
        'dataSource': 'TeleGeography',
        'updateFrequency': 'Daily',
    },
    'telecom_02_bgp_anomalies': {
        'name': 'BGP Routing Anomalies',
        'domain': 'telecommunications',
        'description': 'Major anomalies per day — BGP hijacks can redirect your traffic through hostile countries',
        'unit': 'anomalies/day',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'BGPStream / RIPE',
        'updateFrequency': 'Real-time',
    },
    'telecom_03_cell_outages': {
        'name': 'Cell Network Outages',
        'domain': 'telecommunications',
        'description': 'Major carrier outages per week — can\'t call 911 or coordinate when networks are down',
        'unit': 'outages/wk',
        'thresholds': {'green': {'max': 2}, 'amber': {'min': 2, 'max': 5}, 'red': {'min': 5}, 'threshold_amber': 2, 'threshold_red': 5},
        'critical': False,
        'dataSource': 'FCC / Downdetector',
        'updateFrequency': 'Real-time',
    },
    # Housing & Financial
    'housing_01_delinquency': {
        'name': 'Mortgage Delinquency',
        'domain': 'housing_mortgage',
        'description': 'Seriously delinquent mortgages — rising delinquencies mean neighbors struggling, community stability erodes',
        'unit': '%',
        'thresholds': {'green': {'max': 3}, 'amber': {'min': 3, 'max': 5}, 'red': {'min': 5}, 'threshold_amber': 3, 'threshold_red': 5},
        'critical': False,
        'dataSource': 'MBA',
        'updateFrequency': 'Monthly',
    },
    'housing_03_rate_shock': {
        'name': 'Mortgage Rate Shock',
        'domain': 'housing_mortgage',
        'description': '30yr fixed rate — high rates freeze the market, affects your financial flexibility',
        'unit': '%',
        'thresholds': {'green': {'max': 7}, 'amber': {'min': 7, 'max': 8.5}, 'red': {'min': 8.5}, 'threshold_amber': 7, 'threshold_red': 8.5},
        'critical': False,
        'dataSource': 'Freddie Mac PMMS',
        'updateFrequency': 'Weekly',
    },
    # Domestic Control
    'ice_detention_surge': {
        'name': 'Immigration Enforcement',
        'domain': 'domestic_control',
        'description': 'ICE total detainees — mass detention expansion signals authoritarian overreach',
        'unit': 'detainees',
        'thresholds': {'green': {'max': 30000}, 'amber': {'min': 30000, 'max': 50000}, 'red': {'min': 50000}, 'threshold_amber': 30000, 'threshold_red': 50000},
        'critical': False,
        'dataSource': 'ICE / TRAC',
        'updateFrequency': 'Monthly',
    },
    'federal_regulations': {
        'name': 'Federal Regulatory Activity',
        'domain': 'domestic_control',
        'description': 'Liberty-restricting EOs and bills per quarter — legal infrastructure of authoritarianism',
        'unit': 'actions/qtr',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 12}, 'red': {'min': 12}, 'threshold_amber': 5, 'threshold_red': 12},
        'critical': False,
        'dataSource': 'Federal Register / Congress.gov',
        'updateFrequency': 'Daily',
    },
    'liberty_litigation_count': {
        'name': 'Constitutional Pushback',
        'domain': 'domestic_control',
        'description': 'Active constitutional challenges — INVERSE: more cases = better (institutions fighting back)',
        'unit': 'cases',
        'thresholds': {'green': {'min': 10}, 'amber': {'min': 3, 'max': 10}, 'red': {'max': 3}, 'threshold_amber': 10, 'threshold_red': 3},
        'critical': False,
        'dataSource': 'CourtListener / ACLU',
        'updateFrequency': 'Weekly',
    },
    'hill_control_legislation': {
        'name': 'Control Bills Advancing',
        'domain': 'domestic_control',
        'description': 'Bills related to AI, surveillance, emergency powers advancing',
        'unit': 'bills',
        'thresholds': {'green': {'max': 3}, 'amber': {'min': 3, 'max': 8}, 'red': {'min': 8}, 'threshold_amber': 3, 'threshold_red': 8},
        'critical': False,
        'dataSource': 'Congress.gov',
        'updateFrequency': 'Daily',
    },
    # Rights & Governance
    'power_01_ai_surveillance': {
        'name': 'AI Surveillance Expansion',
        'domain': 'rights_governance',
        'description': 'AI surveillance bills in session — erodes privacy, signals shift toward authoritarian control',
        'unit': 'bills',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'LegiScan / OpenStates',
        'updateFrequency': 'Daily',
    },
    # AI Window
    'labor_ai_01_layoffs': {
        'name': 'AI Job Displacement',
        'domain': 'ai_window',
        'description': 'AI-attributed layoffs per month — jobs replaced faster than new ones appear',
        'unit': 'K/month',
        'thresholds': {'green': {'max': 10}, 'amber': {'min': 10, 'max': 50}, 'red': {'min': 50}, 'threshold_amber': 10, 'threshold_red': 50},
        'critical': False,
        'dataSource': 'Layoffs.fyi / BLS',
        'updateFrequency': 'Monthly',
    },
    # Cult / Meta
    'cult_media_01_trends': {
        'name': 'Social Stress Signals',
        'domain': 'cult_meta',
        'description': 'Cult-like behavior around AI/doomsday movements — when these spike, social cohesion is degrading',
        'unit': 'index',
        'thresholds': {'green': {'max': 130}, 'amber': {'min': 130, 'max': 200}, 'red': {'min': 200}, 'threshold_amber': 130, 'threshold_red': 200},
        'critical': False,
        'dataSource': 'Google Trends',
        'updateFrequency': 'Daily',
    },
    # Global Conflict - additional
    'nato_high_readiness': {
        'name': 'NATO Alert Level',
        'domain': 'global_conflict',
        'description': 'NATO readiness level — high readiness means Europe is preparing for war, US is NATO backbone',
        'unit': 'level',
        'thresholds': {'green': {'max': 1}, 'amber': {'min': 1, 'max': 2}, 'red': {'min': 2}, 'threshold_amber': 1, 'threshold_red': 2},
        'critical': True,
        'dataSource': 'NATO / SHAPE',
        'updateFrequency': 'Daily',
    },
    'defense_spending_growth': {
        'name': 'Defense Spending Growth',
        'domain': 'global_conflict',
        'description': 'Global defense spending y/y — nations arming up means world is preparing for conflict',
        'unit': '% y/y',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 10}, 'red': {'min': 10}, 'threshold_amber': 5, 'threshold_red': 10},
        'critical': False,
        'dataSource': 'SIPRI',
        'updateFrequency': 'Quarterly',
    },
    'nuclear_test_activity': {
        'name': 'Nuclear Test Activity',
        'domain': 'global_conflict',
        'description': 'Nuclear tests or credible prep — breaks decades-old taboo, fallout planning becomes immediate',
        'unit': 'events',
        'thresholds': {'green': {'max': 0}, 'amber': {'min': 0, 'max': 1}, 'red': {'min': 1}, 'threshold_amber': 0.5, 'threshold_red': 1},
        'critical': False,
        'dataSource': 'CTBTO / OSINT',
        'updateFrequency': 'Weekly',
    },
    # Security/Infra - additional
    'hormuz_war_risk': {
        'name': 'Hormuz Strait Risk',
        'domain': 'security_infrastructure',
        'description': 'War-risk insurance premium — 20% of global oil transits Hormuz, gas prices spike within weeks',
        'unit': '%',
        'thresholds': {'green': {'max': 1}, 'amber': {'min': 1, 'max': 3}, 'red': {'min': 3}, 'threshold_amber': 1, 'threshold_red': 3},
        'critical': False,
        'dataSource': 'Lloyd\'s',
        'updateFrequency': 'Daily',
    },
    'fema_disaster_declarations': {
        'name': 'FEMA Disaster Declarations',
        'domain': 'security_infrastructure',
        'description': 'Declarations per quarter — high activity means federal resources stretch thin',
        'unit': 'decl/qtr',
        'thresholds': {'green': {'max': 15}, 'amber': {'min': 15, 'max': 30}, 'red': {'min': 30}, 'threshold_amber': 15, 'threshold_red': 30},
        'critical': False,
        'dataSource': 'FEMA',
        'updateFrequency': 'Daily',
    },
    'cdc_health_alerts': {
        'name': 'CDC Health Alerts',
        'domain': 'security_infrastructure',
        'description': 'HAN alerts per month — local health infrastructure stressed, hospitals fill up',
        'unit': 'alerts/mo',
        'thresholds': {'green': {'max': 3}, 'amber': {'min': 3, 'max': 8}, 'red': {'min': 8}, 'threshold_amber': 3, 'threshold_red': 8},
        'critical': False,
        'dataSource': 'CDC HAN',
        'updateFrequency': 'Daily',
    },
    'fda_drug_shortages': {
        'name': 'Pharmacy Shortage Index',
        'domain': 'supply_chain',
        'description': 'Shortage severity index — measures how badly common drugs affected at retail',
        'unit': 'index',
        'thresholds': {'green': {'max': 15}, 'amber': {'min': 15, 'max': 30}, 'red': {'min': 30}, 'threshold_amber': 15, 'threshold_red': 30},
        'critical': False,
        'dataSource': 'FDA / GoodRx',
        'updateFrequency': 'Weekly',
    },
    # Supply Chain - additional
    'supply_03_chip_lead_time': {
        'name': 'Semiconductor Lead Time',
        'domain': 'supply_chain',
        'description': 'Chip lead times in weeks — affects electronics, vehicles, medical devices',
        'unit': 'weeks',
        'thresholds': {'green': {'max': 20}, 'amber': {'min': 20, 'max': 30}, 'red': {'min': 30}, 'threshold_amber': 20, 'threshold_red': 30},
        'critical': False,
        'dataSource': 'Susquehanna',
        'updateFrequency': 'Monthly',
    },
    # Jobs - additional
    'luxury_01_collapse': {
        'name': 'Luxury Sector Health',
        'domain': 'jobs_labor',
        'description': 'Luxury spending vs peak — collapses 3-6 months before broad recession',
        'unit': '% from peak',
        'thresholds': {'green': {'min': -10}, 'amber': {'min': -25, 'max': -10}, 'red': {'max': -25}, 'threshold_amber': -10, 'threshold_red': -25},
        'critical': False,
        'dataSource': 'Bloomberg',
        'updateFrequency': 'Daily',
    },
    # Energy - additional
    'oil_03_ofac_designations': {
        'name': 'Oil Sanctions Activity',
        'domain': 'energy',
        'description': 'OFAC designations per quarter targeting oil — prices spike as legal oil gets scarcer',
        'unit': 'designations/qtr',
        'thresholds': {'green': {'max': 5}, 'amber': {'min': 5, 'max': 15}, 'red': {'min': 15}, 'threshold_amber': 5, 'threshold_red': 15},
        'critical': False,
        'dataSource': 'Treasury OFAC',
        'updateFrequency': 'Daily',
    },
}


def _determine_level(value: float, thresholds: Dict[str, Any]) -> str:
    """Determine green/amber/red level from value and thresholds."""
    amber = thresholds.get('threshold_amber')
    red = thresholds.get('threshold_red')

    if amber is None or red is None:
        return 'unknown'

    # Standard: higher is worse
    if red > amber:
        if value >= red:
            return 'red'
        elif value >= amber:
            return 'amber'
        return 'green'
    # Inverted: lower is worse (e.g. GDP)
    else:
        if value <= red:
            return 'red'
        elif value <= amber:
            return 'amber'
        return 'green'


class DataService:
    """Cached data service that collects from real APIs where possible."""

    def __init__(self):
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        self.config = ConfigLoader(str(config_path))

        # Initialize collectors that can work without API keys
        self._collectors: Dict[str, Any] = {}
        self._init_collectors()

        # Cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._default_ttl = 300  # 5 minutes

    def _init_collectors(self):
        """Initialize collectors. Only include ones that imported successfully."""
        candidate_collectors = {
            # Core
            'cisa_cyber': _CISACyberCollector,
            'who_disease': _WHODiseaseCollector,
            'grocery_cpi': _GroceryCPICollector,
            'treasury': _TreasuryCollector,
            'jobless_claims': _JoblessClaimsCollector,
            'gdp_growth': _GDPGrowthCollector,
            'market_volatility': _MarketVolatilityCollector,
            'treasury_auctions': _TreasuryAuctionCollector,
            'nws_alerts': _NWSAlertsCollector,
            'acled_protests': _ACLEDProtestsCollector,
            'eia_spr': _EIASPRCollector,
            # FAA
            'faa_ground_stops': _FAAGroundStopsCollector,
            'faa_delays': _FAAFlightDelaysCollector,
            'faa_tfr': _FAATFRCollector,
            # Travel
            'state_dept': _StateDeptAdvisoryCollector,
            'cbp_border': _CBPBorderWaitCollector,
            'tsa_throughput': _TSAThroughputCollector,
            # Banking
            'fdic_failures': _FDICBankFailuresCollector,
            'fed_discount': _FedDiscountWindowCollector,
            'fed_deposits': _FedDepositsCollector,
            # EIA extras
            'eia_natgas': _EIANaturalGasCollector,
            'eia_grid': _EIAGridEmergencyCollector,
            # Labor
            'strike_tracker': _StrikeTrackerCollector,
            # Taiwan
            'taiwan_pla': _TaiwanPLACollector,
            # Supply chain
            'port_congestion': _PortCongestionCollector,
            'freight_index': _FreightIndexCollector,
            # Pharmacy
            'pharmacy_shortage': _PharmacyShortageCollector,
            # Global conflict
            'global_conflict': _GlobalConflictCollector,
            # Congress
            'congress_bills': _CongressBillsCollector,
            # USDA / Food
            'usda_crops': _USDACropConditionCollector,
            'usda_livestock': _USDALivestockDiseaseCollector,
            'fertilizer_price': _FertilizerPriceCollector,
            'usda_processing': _USDAMeatProcessingCollector,
            # Water Infrastructure
            # 'reservoir_level': _ReservoirLevelCollector,  # UNAVAILABLE - data source parsing issue
            'epa_water': _EPAWaterAlertsCollector,
            # 'drought_monitor': _DroughtMonitorCollector,  # REMOVED from frontend - no working API
            # Treasury/OFAC
            'ofac_sanctions': _OFACSanctionsCollector,
            # Telecom Infrastructure
            'bgp_anomalies': _BGPAnomaliesCollector,
            # 'cell_outages': _CellOutagesCollector,  # UNAVAILABLE - DownDetector scraping unreliable
            'undersea_cable': _UnderseaCableCollector,
            # RSS alternatives
            'protest_news': _ProtestNewsCollector,
            'conflict_news': _GlobalConflictNewsCollector,
            'nato_news': _NATONewsCollector,
            'defense_spending': _DefenseSpendingCollector,
            'ai_layoffs': _AILayoffsCollector,
            'nuclear_tests': _NuclearTestsCollector,
            # Free alternatives
            'luxury_index': _YahooLuxuryIndexCollector,
            'oil_inventory': _EIAOilInventoryCollector,
            'chip_lead_time': _SemiconductorLeadTimeCollector,
            # 'ice_detention': _ICEDetentionCollector,  # UNAVAILABLE - ICE data not publicly accessible
            'hormuz_risk': _HormuzRiskCollector,
            'mortgage_delinq': _MortgageDelinquencyCollector,
            'ai_religion': _GoogleTrendsCollector,
            # OpenStates (state legislation)
            'openstates': _OpenStatesAISurveillanceCollector,
            # CourtListener (civil liberties cases)
            'courtlistener': _CourtListenerLibertyCollector,
            # Government RSS feeds
            # 'sec_filings': _SECFilingsCollector,  # RSS parsing unreliable
            'federal_register': _FederalRegisterCollector,
            'fema_disasters': _FEMADisasterCollector,
            'cdc_alerts': _CDCHealthAlertsCollector,
            'fda_shortages': _FDAShortagesCollector,
            'govtrack': _GovTrackBillsCollector,
            # Freddie Mac mortgage rates
            'freddie_mac': _FreddieMacPMMSCollector,
        }

        for key, cls in candidate_collectors.items():
            if cls is None:
                continue
            try:
                self._collectors[key] = cls(self.config)
                logger.info(f"Initialized collector: {key}")
            except Exception as e:
                logger.warning(f"Failed to init {key}: {e}")

    def collect_indicator(self, collector_key: str) -> Optional[Dict[str, Any]]:
        """Collect a single indicator, with caching."""
        # Check cache
        now = time.time()
        if collector_key in self._cache:
            if now < self._cache_ttl.get(collector_key, 0):
                return self._cache[collector_key]

        collector = self._collectors.get(collector_key)
        if not collector:
            return None

        try:
            raw = collector.collect()
            if raw is None:
                return None

            frontend_id = COLLECTOR_TO_FRONTEND_ID.get(collector_key, collector_key)
            meta = INDICATOR_META.get(frontend_id, {})
            thresholds = meta.get('thresholds', {})

            value = raw.get('value', 0)
            source_type = raw.get('metadata', {}).get('data_source', raw.get('metadata', {}).get('source', 'LIVE'))
            is_live = source_type not in ('mock_data', 'MOCK', 'Mock data')

            level = _determine_level(value, thresholds) if thresholds else 'unknown'

            indicator = {
                'id': frontend_id,
                'name': meta.get('name', collector_key),
                'domain': meta.get('domain', 'economy'),
                'description': meta.get('description', ''),
                'unit': meta.get('unit', ''),
                'thresholds': thresholds,
                'critical': meta.get('critical', False),
                'greenFlag': meta.get('greenFlag', False),
                'enabled': True,
                'dataSource': meta.get('dataSource', 'Unknown'),
                'updateFrequency': meta.get('updateFrequency', '60m'),
                'status': {
                    'level': level,
                    'value': value,
                    'trend': 'stable',
                    'lastUpdate': raw.get('timestamp', datetime.utcnow().isoformat()),
                    'dataSource': 'LIVE' if is_live else 'MOCK',
                },
            }

            # Cache it
            self._cache[collector_key] = indicator
            self._cache_ttl[collector_key] = now + self._default_ttl

            return indicator

        except Exception as e:
            logger.error(f"Error collecting {collector_key}: {e}")
            return None

    def collect_all(self) -> List[Dict[str, Any]]:
        """Collect all indicators that have registered collectors.

        When multiple collectors map to the same frontend ID,
        the last one wins (allows treasury_auctions to override treasury).
        """
        seen: Dict[str, Dict[str, Any]] = {}
        for key in self._collectors:
            indicator = self.collect_indicator(key)
            if indicator:
                seen[indicator['id']] = indicator
        return list(seen.values())

    def get_live_ids(self) -> List[str]:
        """Return frontend IDs that have live collectors."""
        return [
            COLLECTOR_TO_FRONTEND_ID[k]
            for k in self._collectors
            if k in COLLECTOR_TO_FRONTEND_ID
        ]

    def invalidate_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_ttl.clear()


# Singleton
_service: Optional[DataService] = None


def get_data_service() -> DataService:
    global _service
    if _service is None:
        _service = DataService()
    return _service
