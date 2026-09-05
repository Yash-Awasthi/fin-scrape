"""
HOPI-based Phase Manager for Brown Man Bunker.
Integrates HOPI calculator and phase controller for comprehensive threat assessment.
"""

import logging
from typing import Dict, List, Tuple, Optional, Set, Any
from datetime import datetime
from collections import defaultdict

from .hopi_calculator import HOPICalculator
from .phase_controller import PhaseController
from .stale_handler import StaleDataHandler


class PhaseManagerHOPI:
    """Manages phases using HOPI scoring system."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.hopi_calculator = HOPICalculator()
        self.phase_controller = PhaseController()
        self.stale_handler = StaleDataHandler(config)
        
        # Track confirmation states
        self.confirmation_tracker = defaultdict(lambda: {'count': 0, 'first_seen': None})
        
        # Load scoring rules
        self._load_scoring_rules()
        
    def _load_scoring_rules(self):
        """Load scoring rules from config."""
        # In production, would load from scoring_rules.yaml
        # For now, use defaults
        self.confirmation_polls = 2
        self.critical_indicators = {
            'MarketVolatility', 'DeepfakeShocks', 'TaiwanZone',
            'NATOReadiness', 'GuardMetros', 'DHSRemoval'
        }
        
    def evaluate(self, readings: Dict[str, Any], threat_levels: Dict[str, str]) -> Dict:
        """
        Evaluate current state and determine phase.
        
        Args:
            readings: Raw indicator readings
            threat_levels: Color assignments from threat analyzer
            
        Returns:
            Dict with phase, HOPI score, actions, etc.
        """
        # Convert to HOPI format
        indicators = self._prepare_indicators(readings, threat_levels)
        
        # Check for stale data
        stale_indicators = self._check_stale_data(readings)
        
        # Apply stale data forcing rules
        indicators = self._apply_stale_forcing(indicators, stale_indicators)
        
        # Apply confirmation rules
        indicators = self._apply_confirmation_rules(indicators)
        
        # Calculate HOPI
        hopi_result = self.hopi_calculator.calculate(indicators, stale_indicators)
        
        # Determine phase
        phase_result = self.phase_controller.update(hopi_result, indicators)
        
        # Combine results
        return {
            'phase': phase_result['phase'],
            'phase_name': phase_result['phase_name'],
            'headline': phase_result['headline'],
            'hopi': hopi_result['hopi'],
            'confidence': hopi_result['confidence'],
            'domain_scores': hopi_result['domain_scores'],
            'indicators': indicators,
            'stale_count': len(stale_indicators),
            'red_count': hopi_result['total_reds'],
            'critical_reds': hopi_result['critical_reds'],
            'phase_changed': phase_result['changed'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _prepare_indicators(self, readings: Dict[str, Any], 
                           threat_levels: Dict[str, str]) -> Dict[str, Dict]:
        """Convert readings and threat levels to HOPI format."""
        indicators = {}
        
        for name, reading in readings.items():
            if reading is None:
                continue
                
            # Get color from threat level
            level = threat_levels.get(name, 'unknown')
            color_map = {'green': 0, 'amber': 1, 'red': 2}
            color = color_map.get(level, 0)
            
            # Extract metadata
            metadata = reading.get('metadata', {})
            
            indicators[name] = {
                'color': color,
                'value': reading.get('value'),
                'level': level,
                'source': metadata.get('source', 'unknown'),
                'timestamp': reading.get('timestamp'),
                'confirmed': True,  # Will be updated by confirmation rules
                'metadata': metadata
            }
        
        return indicators
    
    def _check_stale_data(self, readings: Dict[str, Any]) -> Set[str]:
        """Check which indicators have stale data."""
        stale = set()
        
        for name, reading in readings.items():
            if reading is None:
                stale.add(name)
                continue
                
            # Use stale handler
            staleness = self.stale_handler.check_staleness(reading)
            if staleness.get('is_stale', False):
                stale.add(name)
        
        return stale
    
    def _apply_stale_forcing(self, indicators: Dict[str, Dict], 
                            stale_indicators: Set[str]) -> Dict[str, Dict]:
        """Force amber/red for stale indicators."""
        for name in stale_indicators:
            if name not in indicators:
                continue
                
            indicator = indicators[name]
            
            # Check staleness level from timestamp
            if 'timestamp' in indicator:
                try:
                    ts = datetime.fromisoformat(indicator['timestamp'].replace('Z', '+00:00'))
                    age_hours = (datetime.utcnow() - ts.replace(tzinfo=None)).total_seconds() / 3600
                    
                    if age_hours > 168:  # 7 days
                        indicator['color'] = 2  # Force red
                        indicator['level'] = 'red'
                        indicator['stale_reason'] = 'stale>7d'
                    elif age_hours > 48:  # 2 days
                        if indicator['color'] < 1:
                            indicator['color'] = 1  # Force amber
                            indicator['level'] = 'amber'
                        indicator['stale'] = True
                except:
                    pass
        
        return indicators
    
    def _apply_confirmation_rules(self, indicators: Dict[str, Dict]) -> Dict[str, Dict]:
        """Apply confirmation rules for red states."""
        current_time = datetime.utcnow()
        
        for name, indicator in indicators.items():
            # Skip if not red
            if indicator['color'] != 2:
                # Clear confirmation tracking
                if name in self.confirmation_tracker:
                    del self.confirmation_tracker[name]
                continue
            
            # Critical indicators skip confirmation
            if name in self.critical_indicators:
                indicator['confirmed'] = True
                continue
            
            # Track confirmation
            tracker = self.confirmation_tracker[name]
            
            if tracker['count'] == 0:
                # First time seeing red
                tracker['count'] = 1
                tracker['first_seen'] = current_time
                indicator['confirmed'] = False
            else:
                # Check if consecutive
                time_since_first = (current_time - tracker['first_seen']).total_seconds()
                
                if time_since_first < 3600:  # Within 1 hour (typical poll interval)
                    tracker['count'] += 1
                    
                    if tracker['count'] >= self.confirmation_polls:
                        indicator['confirmed'] = True
                    else:
                        indicator['confirmed'] = False
                else:
                    # Too much time passed, reset
                    tracker['count'] = 1
                    tracker['first_seen'] = current_time
                    indicator['confirmed'] = False
        
        return indicators
    
    def get_actions(self, phase: float) -> List[str]:
        """Get recommended actions for current phase."""
        actions = {
            0: [
                "Continue normal routines",
                "Maintain fitness and skills training",
                "Review emergency contacts"
            ],
            1: [
                "Verify 72-hour kit contents",
                "Update contact sheet",
                "Test emergency communications"
            ],
            2: [
                "Complete digital security audit",
                "Test backup communications",
                "Review financial accounts"
            ],
            2.5: [
                "Increase cash reserves",
                "Ensure passports accessible",
                "Review evacuation routes"
            ],
            3: [
                "Stock N95/HEPA supplies",
                "Avoid crowded venues",
                "Top off medications"
            ],
            4: [
                "Implement light curfew",
                "Fill vehicle fuel tanks",
                "Maximize cash on hand"
            ],
            5: [
                "Prepare generator/fuel",
                "Stock 60-90 day medications",
                "Reduce unnecessary travel"
            ],
            6: [
                "Activate shelter preparations",
                "Implement roles matrix",
                "Begin remote work if possible"
            ],
            7: [
                "Harden shelter space",
                "Generator/ATS operational",
                "Full work from home"
            ],
            8: [
                "Fill water storage",
                "Minimize all movement",
                "Monitor emergency channels only"
            ],
            9: [
                "Full emergency posture",
                "Shelter in place",
                "Execute contingency plans"
            ]
        }
        
        return actions.get(phase, ["Monitor situation"])
    
    def get_current_phase(self) -> int:
        """
        Get the current phase number.
        
        Returns:
            Current phase (0-9)
        """
        try:
            # Get current phase from config or default to 0
            phases_config = self.config.config.get('phases', {})
            current_phase = phases_config.get('current_phase', 0)
            return int(current_phase)
        except Exception as e:
            self.logger.error(f"Error getting current phase: {e}")
            return 0
    
    def calculate_hopi(self, readings: Dict[str, Any] = None, threat_levels: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Calculate HOPI score and related metrics.
        
        Args:
            readings: Optional readings data
            threat_levels: Optional threat levels
            
        Returns:
            HOPI calculation results
        """
        try:
            if readings and threat_levels:
                # Prepare indicators for HOPI calculation
                indicators = self._prepare_indicators(readings, threat_levels)
                
                # Use the HOPI calculator
                result = self.hopi_calculator.calculate(indicators)
            else:
                # Return default/empty HOPI result
                result = {
                    'score': 0.0,
                    'confidence': 1.0,
                    'critical_reds': 0,
                    'stale_count': 0,
                    'domain_scores': {
                        'economy': 0.0,
                        'global_conflict': 0.0,
                        'oil_axis': 0.0,
                        'ai_window': 0.0,
                        'domestic_control': 0.0,
                        'jobs_labor': 0.0,
                        'security_infrastructure': 0.0,
                        'rights_governance': 0.0,
                        'cult': 0.0
                    }
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating HOPI: {e}")
            # Return safe default
            return {
                'score': 0.0,
                'confidence': 0.0,
                'critical_reds': 0,
                'stale_count': 0,
                'domain_scores': {}
            }