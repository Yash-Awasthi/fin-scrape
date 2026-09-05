"""
Phase Manager for Brown Man Bunker.
Handles phase transitions based on metric conditions and provides action guidance.
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class PhaseManager:
    """Manages resilience phases 0-9 based on system metrics."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.phase_config = config.config.get('phases', {})
        self.current_phase = self.phase_config.get('current_phase', 0)
        self.phase_history = []
        
        # Track metric states over time for sustained conditions
        self.metric_history = {}
        
    def evaluate_phase(self, metrics: Dict[str, Dict], threat_levels: Dict[str, str]) -> Tuple[int, Dict]:
        """
        Evaluate current metrics and determine appropriate phase.
        
        Returns:
            Tuple of (new_phase, phase_info)
        """
        # Count conditions
        red_count = sum(1 for level in threat_levels.values() if level == 'red')
        amber_count = sum(1 for level in threat_levels.values() if level == 'amber')
        
        # Check for sustained conditions
        sustained_ambers = self._check_sustained_condition(threat_levels, 'amber', days=7)
        sustained_reds = self._check_sustained_condition(threat_levels, 'red', hours=48)
        
        # Check specific metric conditions
        acled_red = threat_levels.get('ACLEDProtests', '') == 'red'
        cyber_red = threat_levels.get('CISACyber', '') == 'red'
        oil_01_red = threat_levels.get('CREAOil', '') == 'red'
        oil_02_red = threat_levels.get('MBridgeSettlements', '') == 'red'
        market_critical = self._check_market_critical(metrics)
        
        # Check green flags
        green_flags = self._check_green_flags(metrics)
        
        # Determine phase based on conditions
        new_phase = self._calculate_phase(
            red_count, amber_count, sustained_ambers, sustained_reds,
            acled_red, cyber_red, oil_01_red, oil_02_red,
            market_critical, green_flags
        )
        
        # Get phase info
        phase_info = self._get_phase_info(new_phase)
        
        # Record phase change if different
        if new_phase != self.current_phase:
            self._record_phase_change(self.current_phase, new_phase)
            self.current_phase = new_phase
        
        return new_phase, phase_info
    
    def _calculate_phase(self, red_count: int, amber_count: int,
                        sustained_ambers: int, sustained_reds: int,
                        acled_red: bool, cyber_red: bool,
                        oil_01_red: bool, oil_02_red: bool,
                        market_critical: bool, green_flags: Dict) -> int:
        """Calculate appropriate phase based on conditions."""
        
        # Phase 8: Grid instability pattern
        if self._check_grid_instability():
            return 8
        
        # Phase 7: Local Guard activation or court chaos + 2 reds
        if self._check_local_emergency() and red_count >= 2:
            return 7
        
        # Phase 6: 2+ reds sustained ≥48h
        if sustained_reds >= 2:
            return 6
        
        # Phase 5: Oil crisis or market shock
        if oil_01_red or oil_02_red or market_critical:
            return 5
        
        # Phase 4: ACLED or CYBER red, or 2 total reds
        if acled_red or cyber_red or red_count >= 2:
            return 4
        
        # Phase 3: 1 red anywhere or 2 ambers sustained 7 days
        if red_count >= 1 or sustained_ambers >= 2:
            return 3
        
        # Phase 2.5: 2 ambers or GREEN-G1 false
        if amber_count >= 2 or not green_flags.get('GREEN_G1', True):
            return 2.5
        
        # Phase 2: Any 1 amber in econ/rights/security
        if amber_count >= 1:
            return 2
        
        # Phase 1: Normal/green overall
        if red_count == 0 and amber_count == 0:
            return 1
        
        # Default: Phase 0 (foundations)
        return 0
    
    def _check_sustained_condition(self, threat_levels: Dict[str, str], 
                                 level: str, days: int = 0, hours: int = 0) -> int:
        """Check how many metrics have sustained a threat level."""
        # In production, would check historical data
        # For now, return current count
        return sum(1 for l in threat_levels.values() if l == level)
    
    def _check_market_critical(self, metrics: Dict) -> bool:
        """Check if market volatility hit critical threshold."""
        market_metric = metrics.get('MarketVolatility', {})
        return market_metric.get('value', 0) >= 30
    
    def _check_grid_instability(self) -> bool:
        """Check for grid instability pattern (3+ PJM outages/quarter)."""
        # Would check historical grid outage data
        return False
    
    def _check_local_emergency(self) -> bool:
        """Check for local Guard activation or court chaos."""
        # Would integrate with local emergency feeds
        return False
    
    def _check_green_flags(self, metrics: Dict) -> Dict[str, bool]:
        """Check positive indicator conditions."""
        green_flags = {}
        
        # COMPUTE-01: $/training-FLOP down 30%+ for 6 months
        compute_metric = metrics.get('EpochCompute', {})
        green_flags['COMPUTE_01'] = compute_metric.get('value', 0) <= -30
        
        # GREEN-G1: GDP ≥4% and 10Y <4%
        gdp_metric = metrics.get('GDPGrowth', {})
        treasury_metric = metrics.get('Treasury', {})
        green_flags['GREEN_G1'] = (
            gdp_metric.get('value', 0) >= 4 and
            treasury_metric.get('value', 10) < 4
        )
        
        return green_flags
    
    def _get_phase_info(self, phase: int) -> Dict:
        """Get detailed information about a phase."""
        phase_defs = self.phase_config.get('definitions', {})
        phase_key = str(int(phase)) if phase != 2.5 else '2.5'
        
        if phase_key in phase_defs:
            return phase_defs[phase_key]
        
        return {
            'name': f'Phase {phase}',
            'trigger': 'Unknown',
            'actions': ['Check phase configuration']
        }
    
    def _record_phase_change(self, old_phase: int, new_phase: int):
        """Record phase transition in history."""
        self.phase_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'from_phase': old_phase,
            'to_phase': new_phase,
            'direction': 'escalate' if new_phase > old_phase else 'de-escalate'
        })
        
        self.logger.info(f"Phase transition: {old_phase} → {new_phase}")
    
    def get_phase_actions(self, phase: int) -> List[str]:
        """Get recommended actions for current phase."""
        phase_info = self._get_phase_info(phase)
        return phase_info.get('actions', [])
    
    def should_tighten_up(self, red_count: int) -> bool:
        """Check if TIGHTEN-UP protocol should activate."""
        threshold = self.phase_config.get('phase_rules', {}).get('tighten_threshold', 2)
        return red_count >= threshold