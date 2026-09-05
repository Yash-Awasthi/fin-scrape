#!/usr/bin/env python3
"""
Web dashboard for Household Resilience Monitoring System.
Provides family-friendly interface to view status and emergency procedures.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import logging
import os
import pickle
from typing import Dict, Any

from collectors import (
    TreasuryCollector,
    ICEDetentionCollector, 
    TaiwanZoneCollector,
    HormuzRiskCollector,
    DoDAutonomyCollector,
    JoblessClaimsCollector,
    LuxuryCollapseCollector,
    PharmacyShortageCollector,
    SchoolClosureCollector,
    AGIMilestoneCollector,
    LaborDisplacementCollector,
    GroceryCPICollector,
    CISACyberCollector,
    GridOutageCollector,
    GDPGrowthCollector,
    StrikeTrackerCollector,
    LegiScanCollector,
    ACLEDProtestsCollector,
    MarketVolatilityCollector,
    WHODiseaseCollector,
    CREAOilCollector,
    OFACDesignationsCollector,
    AILayoffsCollector,
    MBridgeSettlementsCollector,
    JODIOilCollector,
    AIRansomwareCollector,
    DeepfakeShocksCollector,
    GlobalConflictCollector,
    TaiwanPLACollector,
    NATOReadinessCollector,
    NuclearTestsCollector,
    RussiaNATOCollector,
    DefenseSpendingCollector,
    DCControlCollector,
    GuardMetrosCollector,
    ICEDetentionsCollector,
    DHSRemovalCollector,
    HillLegislationCollector,
    LibertyLitigationCollector
)
from processors.threat_analyzer import ThreatAnalyzer
from processors.phase_manager_hopi import PhaseManagerHOPI
from processors.stale_handler import StaleDataHandler
from utils.config_loader import ConfigLoader

app = Flask(__name__)
# Enable CORS for React development and production
CORS(app, origins=[
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:3003',
    'http://localhost:3004',
    'http://localhost:5173',
    'https://canairy.onrender.com',
    'https://*.onrender.com'
], 
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'])
app.config['SECRET_KEY'] = 'household-resilience-2024'

# Initialize components
import os
config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
config = ConfigLoader(config_path)
# Initialize collectors based on enabled status in config
all_collectors = {
    'Treasury': TreasuryCollector,
    'ICEDetention': ICEDetentionCollector,
    'TaiwanZone': TaiwanZoneCollector,
    'HormuzRisk': HormuzRiskCollector,
    'DoDAutonomy': DoDAutonomyCollector,
    'JoblessClaims': JoblessClaimsCollector,
    'LuxuryCollapse': LuxuryCollapseCollector,
    'PharmacyShortage': PharmacyShortageCollector,
    'SchoolClosures': SchoolClosureCollector,
    'AGIMilestones': AGIMilestoneCollector,
    'LaborDisplacement': LaborDisplacementCollector,
    'GroceryCPI': GroceryCPICollector,
    'CISACyber': CISACyberCollector,
    'GridOutages': GridOutageCollector,
    'GDPGrowth': GDPGrowthCollector,
    'StrikeTracker': StrikeTrackerCollector,
    'LegiScan': LegiScanCollector,
    'ACLEDProtests': ACLEDProtestsCollector,
    'MarketVolatility': MarketVolatilityCollector,
    'WHODisease': WHODiseaseCollector,
    'CREAOil': CREAOilCollector,
    'OFACDesignations': OFACDesignationsCollector,
    'AILayoffs': AILayoffsCollector,
    'MBridgeSettlements': MBridgeSettlementsCollector,
    'JODIOil': JODIOilCollector,
    'AIRansomware': AIRansomwareCollector,
    'DeepfakeShocks': DeepfakeShocksCollector,
    'GlobalConflict': GlobalConflictCollector,
    'TaiwanPLA': TaiwanPLACollector,
    'NATOReadiness': NATOReadinessCollector,
    'NuclearTests': NuclearTestsCollector,
    'RussiaNATO': RussiaNATOCollector,
    'DefenseSpending': DefenseSpendingCollector,
    'DCControl': DCControlCollector,
    'GuardMetros': GuardMetrosCollector,
    'ICEDetentions': ICEDetentionsCollector,
    'DHSRemoval': DHSRemovalCollector,
    'HillLegislation': HillLegislationCollector,
    'LibertyLitigation': LibertyLitigationCollector
}

# Only initialize enabled collectors
collectors = {}
trip_wire_config = config.config.get('trip_wires', {})

# Map config names to collector names
config_to_collector = {
    # Original indicators
    'treasury_tail': 'Treasury',
    'ice_detention': 'ICEDetention',
    'taiwan_exclusion': 'TaiwanZone',
    'hormuz_risk': 'HormuzRisk',
    'dod_autonomy': 'DoDAutonomy',
    'jobless_claims': 'JoblessClaims',
    'luxury_collapse': 'LuxuryCollapse',
    'pharmacy_shortage': 'PharmacyShortage',
    'school_closures': 'SchoolClosures',
    'agi_milestones': 'AGIMilestones',
    'labor_displacement': 'LaborDisplacement',
    'grocery_cpi': 'GroceryCPI',
    'cisa_cyber': 'CISACyber',
    'grid_outages': 'GridOutages',
    'gdp_growth': 'GDPGrowth',
    # New phase-based indicators
    'econ_01_treasury_tail': 'Treasury',
    'econ_02_grocery_cpi': 'GroceryCPI',
    'job_01_strike_days': 'StrikeTracker',
    'power_01_ai_surveillance': 'LegiScan',
    'cyber_01_cisa_kev': 'CISACyber',
    'civil_01_acled_protests': 'ACLEDProtests',
    'grid_01_pjm_outages': 'GridOutages',
    'market_01_intraday_swing': 'MarketVolatility',
    'bio_01_h2h_countries': 'WHODisease',
    'oil_01_russian_brics': 'CREAOil',
    'oil_02_mbridge_settlements': 'MBridgeSettlements',
    'oil_03_ofac_designations': 'OFACDesignations',
    'oil_04_refinery_ratio': 'JODIOil',
    'labor_ai_01_layoffs': 'AILayoffs',
    'cyber_02_ai_ransomware': 'AIRansomware',
    'info_02_deepfake_shocks': 'DeepfakeShocks',
    'green_g1_gdp_rates': 'GDPGrowth',  # Green flag indicator using GDP collector
    # New global conflict indicators
    'global_conflict_intensity': 'GlobalConflict',
    'taiwan_pla_activity': 'TaiwanPLA',
    'nato_high_readiness': 'NATOReadiness',
    'nuclear_test_activity': 'NuclearTests',
    'russia_nato_escalation': 'RussiaNATO',
    'defense_spending_growth': 'DefenseSpending',
    # New domestic control indicators
    'dc_control_countdown': 'DCControl',
    'national_guard_metros': 'GuardMetros',
    'ice_detention_surge': 'ICEDetentions',
    'dhs_removal_expansion': 'DHSRemoval',
    'hill_control_legislation': 'HillLegislation',
    'liberty_litigation_count': 'LibertyLitigation'
}

for config_name, collector_name in config_to_collector.items():
    if config_name in trip_wire_config and trip_wire_config[config_name].get('enabled', True):
        if collector_name in all_collectors:
            collectors[collector_name] = all_collectors[collector_name](config)
threat_analyzer = ThreatAnalyzer(config)
phase_manager = PhaseManagerHOPI(config)
stale_handler = StaleDataHandler(config)

# Cache for latest readings
latest_data = {
    'readings': {},
    'threat_levels': {},
    'last_update': None,
    'tighten_up': False
}

# Manual data overrides
data_dir = Path(__file__).parent.parent / 'data'
data_dir.mkdir(exist_ok=True)
manual_data_file = data_dir / 'manual_overrides.pkl'
manual_overrides = {}

# Load manual overrides if they exist
if manual_data_file.exists():
    try:
        with open(manual_data_file, 'rb') as f:
            manual_overrides = pickle.load(f)
    except:
        manual_overrides = {}

def collect_all_data():
    """Collect data from all enabled collectors."""
    global latest_data
    
    # Collect fresh data
    current_readings = {}
    for name, collector in collectors.items():
        # Check for manual override first
        if name in manual_overrides:
            # Use manual data if it's less than 24 hours old
            override = manual_overrides[name]
            override_time = datetime.fromisoformat(override['timestamp'].replace('Z', '+00:00'))
            if (datetime.utcnow() - override_time.replace(tzinfo=None)).total_seconds() < 86400:
                current_readings[name] = override
                continue
        
        # Otherwise collect fresh data
        try:
            reading = collector.collect()
            if reading:
                reading = stale_handler.process_indicator(name, reading)
                current_readings[name] = reading
        except Exception as e:
            logging.error(f"Error collecting {name}: {e}")
    
    # Analyze threat levels
    threat_levels = threat_analyzer.analyze(current_readings)
    
    # Update latest data
    latest_data['readings'] = current_readings
    latest_data['threat_levels'] = threat_levels
    latest_data['last_update'] = datetime.utcnow().isoformat()
    latest_data['tighten_up'] = threat_analyzer.check_tighten_up(threat_levels)

@app.route('/')
def index():
    """Main dashboard page (executive summary)."""
    return render_template('executive.html')

@app.route('/indicators')
def indicators():
    """Detailed indicators page."""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current system status."""
    global latest_data
    
    # Collect fresh data
    current_readings = {}
    for name, collector in collectors.items():
        # Check for manual override first
        if name in manual_overrides:
            # Use manual data if it's less than 24 hours old
            override = manual_overrides[name]
            override_time = datetime.fromisoformat(override['timestamp'].replace('Z', '+00:00'))
            if (datetime.utcnow() - override_time.replace(tzinfo=None)).total_seconds() < 86400:
                current_readings[name] = override
                continue
        
        # Otherwise collect fresh data
        try:
            reading = collector.collect()
            # Check for staleness
            if reading:
                reading = stale_handler.check_staleness(reading)
            current_readings[name] = reading
            # Save to history
            if reading:
                save_to_history(name, reading.get('value'), reading.get('metadata', {}))
        except Exception as e:
            app.logger.error(f"Failed to collect {name}: {e}")
            current_readings[name] = None
    
    # Analyze threat levels
    threat_levels = threat_analyzer.analyze(current_readings)
    
    # Apply stale data forced levels
    for name, reading in current_readings.items():
        if reading and reading.get('metadata', {}).get('stale'):
            original_level = threat_levels.get(name, 'unknown')
            threat_levels[name] = stale_handler.apply_stale_level(
                original_level, reading.get('metadata', {})
            )
    
    # Check for TIGHTEN-UP condition
    red_count = sum(1 for level in threat_levels.values() if level == "red")
    tighten_up = red_count >= config.get_alert_config().get('tighten_up_threshold', 2)
    
    # Evaluate current phase using HOPI
    hopi_result = phase_manager.evaluate(current_readings, threat_levels)
    
    # Update cache
    latest_data = {
        'readings': current_readings,
        'threat_levels': threat_levels,
        'last_update': datetime.now().isoformat(),
        'tighten_up': tighten_up,
        'red_count': red_count,
        'hopi_result': hopi_result
    }
    
    # Format for frontend
    indicators = []
    for name, reading in current_readings.items():
        if reading:
            value = reading.get('value', 'N/A')
            unit = reading.get('metadata', {}).get('unit', '')
            
            # Format value based on unit
            if unit == 'billions_usd':
                formatted_value = f"${value}B"
            elif unit == 'percent':
                formatted_value = f"{value}%"
            elif unit == 'basis_points':
                formatted_value = f"{value} bp"
            elif unit == 'incursions_per_week':
                formatted_value = f"{value}/week"
            elif unit == 'systems':
                formatted_value = f"{value} systems"
            else:
                formatted_value = str(value)
            
            indicators.append({
                'name': name,
                'value': formatted_value,
                'raw_value': value,
                'level': threat_levels.get(name, 'unknown'),
                'timestamp': reading.get('timestamp', ''),
                'unit': unit,
                'metadata': reading.get('metadata', {})
            })
        else:
            indicators.append({
                'name': name,
                'value': 'No Data',
                'raw_value': None,
                'level': 'unknown',
                'timestamp': '',
                'unit': ''
            })
    
    return jsonify({
        'status': 'ok',
        'timestamp': latest_data['last_update'],
        'tighten_up': tighten_up,
        'red_count': red_count,
        'indicators': indicators,
        'current_phase': hopi_result['phase'],
        'phase_info': {
            'name': hopi_result['phase_name'],
            'headline': hopi_result['headline'],
            'actions': phase_manager.get_actions(hopi_result['phase'])
        },
        'hopi': {
            'score': hopi_result['hopi'],
            'confidence': hopi_result['confidence'],
            'domain_scores': hopi_result['domain_scores'],
            'critical_reds': hopi_result['critical_reds'],
            'stale_count': hopi_result['stale_count']
        }
    })

@app.route('/api/history')
def get_history():
    """Get historical data from log files."""
    # Load historical data
    history_file = Path(__file__).parent.parent / 'data' / 'history.json'
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    return jsonify({
        'status': 'ok',
        'history': history[-100:]  # Last 100 entries
    })

@app.route('/emergency')
def emergency():
    """Emergency procedures page."""
    return render_template('emergency.html')

@app.route('/procedures')
def procedures():
    """Emergency procedures page (alias)."""
    return render_template('emergency.html')

@app.route('/framework')
def framework():
    """H1-H6 Risk Analysis Framework page."""
    return render_template('framework.html')

@app.route('/executive')
def executive():
    """Executive summary dashboard."""
    return render_template('executive.html')

@app.route('/manual-input')
def manual_input():
    """Manual data input page."""
    return render_template('manual_input.html')

@app.route('/api/manual-update', methods=['POST'])
def manual_update():
    """Update manual data override."""
    global manual_overrides
    
    data = request.json
    indicator = data.get('indicator')
    value = data.get('value')
    metadata = data.get('metadata', {})
    
    # Store manual override
    manual_overrides[indicator] = {
        'value': value,
        'metadata': metadata,
        'timestamp': datetime.utcnow().isoformat(),
        'collector': indicator
    }
    
    # Save to file
    manual_data_file.parent.mkdir(exist_ok=True)
    with open(manual_data_file, 'wb') as f:
        pickle.dump(manual_overrides, f)
    
    # Also save to history
    save_to_history(indicator, value, metadata)
    
    return jsonify({'status': 'ok', 'message': f'{indicator} updated'})

@app.route('/api/scrape-fda')
def scrape_fda():
    """Scrape FDA drug shortage data."""
    try:
        # In production, would actually scrape FDA site
        # For now, return mock data
        import random
        
        # Simulate scraping delay
        import time
        time.sleep(1)
        
        data = {
            'success': True,
            'total_shortages': random.randint(8, 15),
            'mental_health': random.randint(2, 5),
            'adhd': random.randint(3, 5),
            'antibiotics': random.randint(1, 3)
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def save_to_history(indicator, value, metadata):
    """Save data point to history."""
    history_file = Path(__file__).parent.parent / 'data' / 'history.json'
    
    # Load existing history
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    # Add new entry
    history.append({
        'timestamp': datetime.utcnow().isoformat(),
        'indicator': indicator,
        'value': value,
        'metadata': metadata
    })
    
    # Keep last 10000 entries
    history = history[-10000:]
    
    # Save
    history_file.parent.mkdir(exist_ok=True)
    with open(history_file, 'w') as f:
        json.dump(history, f)

@app.route('/api/indicators')
def get_indicators():
    """Get all indicators with their current status."""
    collect_all_data()

    # Reverse mapping: collector name -> standardized config ID
    # Use phase-based IDs that match the frontend translation map
    collector_to_config = {
        'Treasury': 'econ_01_treasury_tail',
        'GroceryCPI': 'econ_02_grocery_cpi',
        'MarketVolatility': 'market_01_intraday_swing',
        'GDPGrowth': 'green_g1_gdp_rates',
        'StrikeTracker': 'job_01_strike_days',
        'LegiScan': 'power_01_ai_surveillance',
        'ACLEDProtests': 'civil_01_acled_protests',
        'CISACyber': 'cyber_01_cisa_kev',
        'GridOutages': 'grid_01_pjm_outages',
        'WHODisease': 'bio_01_h2h_countries',
        'CREAOil': 'oil_01_russian_brics',
        'MBridgeSettlements': 'oil_02_mbridge_settlements',
        'OFACDesignations': 'oil_03_ofac_designations',
        'JODIOil': 'oil_04_refinery_ratio',
        'AILayoffs': 'labor_ai_01_layoffs',
        'AIRansomware': 'cyber_02_ai_ransomware',
        'DeepfakeShocks': 'info_02_deepfake_shocks',
        'GlobalConflict': 'global_conflict_intensity',
        'TaiwanPLA': 'taiwan_pla_activity',
        'NATOReadiness': 'nato_high_readiness',
        'NuclearTests': 'nuclear_test_activity',
        'RussiaNATO': 'russia_nato_escalation',
        'DefenseSpending': 'defense_spending_growth',
        'DCControl': 'dc_control_countdown',
        'GuardMetros': 'national_guard_metros',
        'ICEDetentions': 'ice_detention_surge',
        'ICEDetention': 'ice_detention_surge',
        'DHSRemoval': 'dhs_removal_expansion',
        'HillLegislation': 'hill_control_legislation',
        'LibertyLitigation': 'liberty_litigation_count',
        'TaiwanZone': 'taiwan_pla_activity',
        'HormuzRisk': 'oil_01_wri_premium',
        'DoDAutonomy': 'dod_autonomy',
        'JoblessClaims': 'job_01_strike_days',
        'LuxuryCollapse': 'luxury_collapse',
        'PharmacyShortage': 'pharmacy_shortage',
        'SchoolClosures': 'school_closures',
        'AGIMilestones': 'compute_01_training_cost',
        'LaborDisplacement': 'labor_ai_01_layoffs'
    }

    # Human-readable display names for indicators
    display_names = {
        'Treasury': '10Y Auction Tail',
        'GroceryCPI': 'Grocery CPI',
        'MarketVolatility': '10Y Intraday Swing',
        'GDPGrowth': 'GDP Green Flag',
        'StrikeTracker': 'US Strike Days',
        'LegiScan': 'AI Surveillance Bills',
        'ACLEDProtests': 'US Protests (7d avg)',
        'CISACyber': 'CISA KEV + ICS',
        'GridOutages': 'PJM Grid Outages',
        'WHODisease': 'Novel H2H Pathogen',
        'CREAOil': 'Russian Crude to BRICS',
        'MBridgeSettlements': 'mBridge Settlement',
        'OFACDesignations': 'OFAC Designations',
        'JODIOil': 'Refinery Run Ratio',
        'AILayoffs': 'AI-Linked Layoffs',
        'AIRansomware': 'AI Ransomware',
        'DeepfakeShocks': 'Deepfake Market Shocks',
        'GlobalConflict': 'Global Battle Intensity',
        'TaiwanPLA': 'Taiwan PLA Incursions',
        'NATOReadiness': 'NATO High Readiness',
        'NuclearTests': 'Nuclear/Missile Tests',
        'RussiaNATO': 'Russia-NATO Index',
        'DefenseSpending': 'Defense Spending Growth',
        'DCControl': 'DC Autonomy Countdown',
        'GuardMetros': 'Guard Metro Deployments',
        'ICEDetentions': 'ICE Detention Population',
        'DHSRemoval': 'DHS Expedited Removal',
        'HillLegislation': 'Control Bills Advancing',
        'LibertyLitigation': 'Liberty Cases Active',
        'ICEDetention': 'ICE Detention Population',
        'TaiwanZone': 'Taiwan Exclusion Zone',
        'HormuzRisk': 'Hormuz War Risk Premium',
        'DoDAutonomy': 'DoD Auto-Execute',
        'JoblessClaims': 'Jobless Claims',
        'LuxuryCollapse': 'Luxury Retail Index',
        'PharmacyShortage': 'Pharmacy Shortages',
        'SchoolClosures': 'School Closures',
        'AGIMilestones': 'AGI Milestones',
        'LaborDisplacement': 'Labor Displacement'
    }

    indicators = []
    for collector_name, data in latest_data['readings'].items():
        if data:
            # Get standardized ID (e.g., econ_01_treasury_tail)
            indicator_id = collector_to_config.get(collector_name, collector_name)

            # Get indicator config
            indicator_config = trip_wire_config.get(indicator_id, {})
            if not indicator_config:
                # Try the collector name directly in config
                for config_name, mapped_name in config_to_collector.items():
                    if mapped_name == collector_name:
                        indicator_config = trip_wire_config.get(config_name, {})
                        break

            # Determine status level
            threat_level = latest_data['threat_levels'].get(collector_name, 'unknown')
            status_level = threat_level if isinstance(threat_level, str) else 'unknown'

            indicator = {
                'id': indicator_id,
                'name': display_names.get(collector_name, data.get('name', collector_name)),
                'domain': _get_domain(collector_name),
                'description': indicator_config.get('description', ''),
                'unit': data.get('metadata', {}).get('unit', ''),
                'status': {
                    'level': status_level,
                    'value': data.get('value', 0),
                    'trend': _get_trend(collector_name),
                    'lastUpdate': data.get('timestamp', datetime.utcnow().isoformat()),
                    'dataSource': data.get('metadata', {}).get('data_source', 'LIVE')
                },
                'thresholds': indicator_config.get('thresholds', {}),
                'critical': indicator_config.get('critical', False),
                'greenFlag': indicator_config.get('green_flag', False),
                'dataSource': data.get('metadata', {}).get('source', 'Unknown'),
                'updateFrequency': indicator_config.get('update_frequency', '60m')
            }
            indicators.append(indicator)

    return jsonify({
        'indicators': indicators,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/hopi')
def get_hopi():
    """Get current HOPI score and phase information."""
    collect_all_data()
    
    # Get HOPI calculation from phase manager
    hopi_result = phase_manager.calculate_hopi()
    current_phase = phase_manager.get_current_phase()
    
    return jsonify({
        'score': hopi_result['hopi_score'],
        'confidence': hopi_result['confidence'],
        'phase': current_phase['phase'],
        'targetPhase': hopi_result['target_phase'],
        'domains': hopi_result['domain_scores'],
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/phase')
def get_phase():
    """Get current phase information."""
    current_phase = phase_manager.get_current_phase()
    
    return jsonify({
        'number': current_phase['phase'],
        'name': current_phase['name'],
        'description': current_phase.get('description', ''),
        'triggers': current_phase.get('triggers', []),
        'actions': current_phase.get('actions', []),
        'color': _get_phase_color(current_phase['phase'])
    })

def _get_domain(collector_name):
    """Map collector to domain (matching frontend domain taxonomy)."""
    domain_mapping = {
        # Economy
        'Treasury': 'economy',
        'JoblessClaims': 'economy',
        'GroceryCPI': 'economy',
        'GDPGrowth': 'economy',
        'MarketVolatility': 'economy',
        # Jobs & Labor
        'StrikeTracker': 'jobs_labor',
        # Rights & Governance
        'LegiScan': 'rights_governance',
        'ACLEDProtests': 'rights_governance',
        # Security & Infrastructure
        'CISACyber': 'security_infrastructure',
        'GridOutages': 'security_infrastructure',
        'WHODisease': 'security_infrastructure',
        # Oil Axis
        'CREAOil': 'oil_axis',
        'MBridgeSettlements': 'oil_axis',
        'OFACDesignations': 'oil_axis',
        'JODIOil': 'oil_axis',
        # AI Window
        'AILayoffs': 'ai_window',
        'AIRansomware': 'ai_window',
        'DeepfakeShocks': 'ai_window',
        'AGIMilestones': 'ai_window',
        'LaborDisplacement': 'ai_window',
        # Global Conflict
        'GlobalConflict': 'global_conflict',
        'TaiwanPLA': 'global_conflict',
        'TaiwanZone': 'global_conflict',
        'NATOReadiness': 'global_conflict',
        'NuclearTests': 'global_conflict',
        'RussiaNATO': 'global_conflict',
        'DefenseSpending': 'global_conflict',
        'HormuzRisk': 'global_conflict',
        # Domestic Control
        'DCControl': 'domestic_control',
        'GuardMetros': 'domestic_control',
        'ICEDetention': 'domestic_control',
        'ICEDetentions': 'domestic_control',
        'DHSRemoval': 'domestic_control',
        'HillLegislation': 'domestic_control',
        'LibertyLitigation': 'domestic_control',
        'DoDAutonomy': 'domestic_control',
        # Energy
        'GridOutages': 'energy',
        # Supply Chain
        'PharmacyShortage': 'supply_chain',
        'LuxuryCollapse': 'supply_chain',
        'SchoolClosures': 'supply_chain'
    }
    return domain_mapping.get(collector_name, 'other')

def _get_trend(collector_name):
    """Get trend for indicator (placeholder)."""
    import random
    return random.choice(['up', 'down', 'stable', None])

def _get_phase_color(phase):
    """Get color for phase."""
    if phase <= 2:
        return '#10B981'
    elif phase <= 5:
        return '#F59E0B'
    else:
        return '#EF4444'

@app.route('/api/config')
def get_config():
    """Get configuration info for display."""
    trip_wires = config.config.get('trip_wires', {})
    
    thresholds = {}
    for key, value in trip_wires.items():
        name = {
            'treasury_tail': 'Treasury',
            'ice_detention': 'ICEDetention',
            'taiwan_exclusion': 'TaiwanZone',
            'hormuz_risk': 'HormuzRisk',
            'dod_autonomy': 'DoDAutonomy',
            'mbridge_crude': 'MBridge'
        }.get(key, key)
        
        thresholds[name] = {
            'name': value.get('name', ''),
            'thresholds': value.get('thresholds', {}),
            'unit': value.get('unit', '')
        }
    
    return jsonify({
        'status': 'ok',
        'thresholds': thresholds,
        'tighten_up_threshold': config.get_alert_config().get('tighten_up_threshold', 2)
    })

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("🌐 Starting Household Resilience Dashboard...")
    print("📍 Access at: http://localhost:5555")
    print("Press Ctrl+C to stop")
    
    app.run(debug=True, host='0.0.0.0', port=5555)