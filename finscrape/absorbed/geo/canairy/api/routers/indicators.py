"""
Indicators router - connects to live data collectors
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add src directory to Python path to import collectors
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from collectors import (
    TreasuryCollector, ICEDetentionCollector, TaiwanZoneCollector,
    HormuzRiskCollector, DoDAutonomyCollector, JoblessClaimsCollector,
    LuxuryCollapseCollector, PharmacyShortageCollector, SchoolClosureCollector,
    AGIMilestoneCollector, LaborDisplacementCollector, GroceryCPICollector,
    CISACyberCollector, GridOutageCollector, GDPGrowthCollector,
    StrikeTrackerCollector, LegiScanCollector, ACLEDProtestsCollector,
    MarketVolatilityCollector, WHODiseaseCollector, CREAOilCollector,
    OFACDesignationsCollector, AILayoffsCollector, MBridgeSettlementsCollector,
    JODIOilCollector, AIRansomwareCollector, DeepfakeShocksCollector
)
from processors.threat_analyzer import ThreatAnalyzer
from utils.config_loader import ConfigLoader

router = APIRouter()

# Initialize components
config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
config = ConfigLoader(str(config_path))
threat_analyzer = ThreatAnalyzer(config)

# Initialize collectors
collectors = {
    'Treasury': TreasuryCollector(config),
    'ICEDetention': ICEDetentionCollector(config),
    'TaiwanZone': TaiwanZoneCollector(config),
    'HormuzRisk': HormuzRiskCollector(config),
    'DoDAutonomy': DoDAutonomyCollector(config),
    'JoblessClaims': JoblessClaimsCollector(config),
    'LuxuryCollapse': LuxuryCollapseCollector(config),
    'PharmacyShortage': PharmacyShortageCollector(config),
    'SchoolClosures': SchoolClosureCollector(config),
    'AGIMilestones': AGIMilestoneCollector(config),
    'LaborDisplacement': LaborDisplacementCollector(config),
    'GroceryCPI': GroceryCPICollector(config),
    'CISACyber': CISACyberCollector(config),
    'GridOutages': GridOutageCollector(config),
    'GDPGrowth': GDPGrowthCollector(config),
    'StrikeTracker': StrikeTrackerCollector(config),
    'LegiScan': LegiScanCollector(config),
    'ACLEDProtests': ACLEDProtestsCollector(config),
    'MarketVolatility': MarketVolatilityCollector(config),
    'WHODisease': WHODiseaseCollector(config),
    'CREAOil': CREAOilCollector(config),
    'OFACDesignations': OFACDesignationsCollector(config),
    'AILayoffs': AILayoffsCollector(config),
    'MBridgeSettlements': MBridgeSettlementsCollector(config),
    'JODIOil': JODIOilCollector(config),
    'AIRansomware': AIRansomwareCollector(config),
    'DeepfakeShocks': DeepfakeShocksCollector(config),
}

logger = logging.getLogger(__name__)

def collect_all_data():
    """Collect data from all enabled collectors"""
    current_readings = {}
    
    for name, collector in collectors.items():
        try:
            reading = collector.collect()
            if reading:
                current_readings[name] = reading
        except Exception as e:
            logger.error(f"Error collecting {name}: {e}")
    
    return current_readings

def _get_domain(collector_name: str) -> str:
    """Map collector name to domain"""
    domain_mapping = {
        'Treasury': 'economy',
        'GroceryCPI': 'economy', 
        'JoblessClaims': 'jobs_labor',
        'MarketVolatility': 'economy',
        'GDPGrowth': 'economy',
        'LuxuryCollapse': 'economy',
        'LaborDisplacement': 'jobs_labor',
        'StrikeTracker': 'jobs_labor',
        'TaiwanZone': 'global_conflict',
        'HormuzRisk': 'global_conflict',
        'ACLEDProtests': 'global_conflict',
        'CREAOil': 'oil_axis',
        'JODIOil': 'oil_axis',
        'MBridgeSettlements': 'oil_axis',
        'OFACDesignations': 'oil_axis',
        'AGIMilestones': 'ai_window',
        'AILayoffs': 'ai_window',
        'AIRansomware': 'ai_window',
        'DeepfakeShocks': 'ai_window',
        'ICEDetention': 'domestic_control',
        'DoDAutonomy': 'domestic_control',
        'PharmacyShortage': 'security_infrastructure',
        'SchoolClosures': 'security_infrastructure',
        'CISACyber': 'security_infrastructure',
        'GridOutages': 'security_infrastructure',
        'WHODisease': 'security_infrastructure',
        'LegiScan': 'rights_governance',
    }
    return domain_mapping.get(collector_name, 'other')

@router.get("/")
async def get_indicators() -> Dict[str, Any]:
    """Get all indicators with live data"""
    try:
        # Collect fresh data
        current_readings = collect_all_data()
        
        # Analyze threat levels
        threat_levels = threat_analyzer.analyze(current_readings)
        
        indicators = []
        for collector_name, data in current_readings.items():
            if data:
                # Get threat level
                threat_level = threat_levels.get(collector_name, 'unknown')
                
                indicator = {
                    'id': collector_name,
                    'name': data.get('name', collector_name),
                    'domain': _get_domain(collector_name),
                    'description': f"Live data from {collector_name}",
                    'unit': data.get('metadata', {}).get('unit', ''),
                    'status': {
                        'level': threat_level,
                        'value': data.get('value', 0),
                        'trend': 'stable',  # Could be enhanced
                        'lastUpdate': data.get('timestamp', datetime.utcnow().isoformat()),
                        'dataSource': 'LIVE'
                    },
                    'thresholds': data.get('metadata', {}),
                    'critical': collector_name in ['Treasury', 'TaiwanZone', 'ICEDetention'],
                    'dataSource': data.get('metadata', {}).get('source', 'Unknown'),
                    'updateFrequency': '60m'
                }
                indicators.append(indicator)
        
        return {
            'indicators': indicators,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting indicators: {e}")
        raise HTTPException(status_code=500, detail=f"Error collecting indicators: {str(e)}")

@router.get("/{indicator_id}")
async def get_indicator(indicator_id: str) -> Dict[str, Any]:
    """Get specific indicator"""
    indicators_response = await get_indicators()
    indicators = indicators_response.get('indicators', [])
    
    for indicator in indicators:
        if indicator.get("id") == indicator_id:
            return indicator
    
    raise HTTPException(status_code=404, detail="Indicator not found")