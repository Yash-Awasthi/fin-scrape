"""
Data collectors for various trip-wire indicators.

Each collector implements the BaseCollector interface and is responsible
for gathering data from specific sources.
"""

from .base import BaseCollector
from .treasury import TreasuryCollector
from .ice_detention import ICEDetentionCollector
from .taiwan_zone import TaiwanZoneCollector
from .hormuz_risk import HormuzRiskCollector
from .dod_autonomy import DoDAutonomyCollector
from .jobless_claims import JoblessClaimsCollector
from .luxury_collapse import LuxuryCollapseCollector
from .pharmacy_shortage import PharmacyShortageCollector
from .school_closures import SchoolClosureCollector
from .agi_milestones import AGIMilestoneCollector
from .labor_displacement import LaborDisplacementCollector
from .grocery_cpi import GroceryCPICollector
from .cisa_cyber import CISACyberCollector
from .grid_outage import GridOutageCollector
from .gdp_growth import GDPGrowthCollector
from .strike_tracker import StrikeTrackerCollector
from .legiscan import LegiScanCollector
from .acled_protests import ACLEDProtestsCollector
from .market_volatility import MarketVolatilityCollector
from .who_disease import WHODiseaseCollector
from .crea_oil import CREAOilCollector
from .ofac_designations import OFACDesignationsCollector
from .ai_layoffs import AILayoffsCollector
from .mbridge_settlements import MBridgeSettlementsCollector
from .jodi_oil import JODIOilCollector
from .ai_ransomware import AIRansomwareCollector
from .deepfake_shocks import DeepfakeShocksCollector
from .global_conflict import GlobalConflictCollector
from .taiwan_pla import TaiwanPLACollector
from .nato_readiness import NATOReadinessCollector
from .nuclear_tests import NuclearTestsCollector
from .russia_nato import RussiaNATOCollector
from .defense_spending import DefenseSpendingCollector
from .dc_control import DCControlCollector
from .guard_metros import GuardMetrosCollector
from .ice_detentions import ICEDetentionsCollector
from .dhs_removal import DHSRemovalCollector
from .hill_legislation import HillLegislationCollector
from .liberty_litigation import LibertyLitigationCollector
from .strike_tracker_scraper import StrikeTrackerScraperCollector
from .taiwan_pla_scraper import TaiwanPLAScraperCollector
from .ice_detention_scraper import ICEDetentionScraperCollector
from .news_aggregator import NewsAggregatorCollector

# New collectors - Energy
from .eia_energy import EIASPRCollector, EIANaturalGasCollector, EIAGridEmergencyCollector

# New collectors - Banking
from .fdic_banks import FDICBankFailuresCollector, FedDiscountWindowCollector, FedDepositsCollector

# New collectors - Flights/Airspace
from .faa_flights import FAAGroundStopsCollector, FAAFlightDelaysCollector, FAATFRCollector

# New collectors - Travel
from .cbp_travel import CBPBorderWaitCollector, TSAThroughputCollector
from .state_dept_travel import StateDeptAdvisoryCollector, PassportWaitCollector

# New collectors - Supply Chain
from .supply_chain import PortCongestionCollector, FreightIndexCollector, SemiconductorLeadTimeCollector

__all__ = [
    'BaseCollector',
    'TreasuryCollector',
    'ICEDetentionCollector',
    'TaiwanZoneCollector',
    'HormuzRiskCollector',
    'DoDAutonomyCollector',
    'JoblessClaimsCollector',
    'LuxuryCollapseCollector',
    'PharmacyShortageCollector',
    'SchoolClosureCollector',
    'AGIMilestoneCollector',
    'LaborDisplacementCollector',
    'GroceryCPICollector',
    'CISACyberCollector',
    'GridOutageCollector',
    'GDPGrowthCollector',
    'StrikeTrackerCollector',
    'LegiScanCollector',
    'ACLEDProtestsCollector',
    'MarketVolatilityCollector',
    'WHODiseaseCollector',
    'CREAOilCollector',
    'OFACDesignationsCollector',
    'AILayoffsCollector',
    'MBridgeSettlementsCollector',
    'JODIOilCollector',
    'AIRansomwareCollector',
    'DeepfakeShocksCollector',
    'GlobalConflictCollector',
    'TaiwanPLACollector',
    'NATOReadinessCollector',
    'NuclearTestsCollector',
    'RussiaNATOCollector',
    'DefenseSpendingCollector',
    'DCControlCollector',
    'GuardMetrosCollector',
    'ICEDetentionsCollector',
    'DHSRemovalCollector',
    'HillLegislationCollector',
    'LibertyLitigationCollector',
    'StrikeTrackerScraperCollector',
    'TaiwanPLAScraperCollector',
    'ICEDetentionScraperCollector',
    'NewsAggregatorCollector',
    # Energy
    'EIASPRCollector',
    'EIANaturalGasCollector',
    'EIAGridEmergencyCollector',
    # Banking
    'FDICBankFailuresCollector',
    'FedDiscountWindowCollector',
    'FedDepositsCollector',
    # Flights/Airspace
    'FAAGroundStopsCollector',
    'FAAFlightDelaysCollector',
    'FAATFRCollector',
    # Travel
    'CBPBorderWaitCollector',
    'TSAThroughputCollector',
    'StateDeptAdvisoryCollector',
    'PassportWaitCollector',
    # Supply Chain
    'PortCongestionCollector',
    'FreightIndexCollector',
    'SemiconductorLeadTimeCollector',
]