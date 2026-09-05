"""
HOPI (Household Operations Priority Index) Calculator.
Implements domain-weighted scoring with pair caps and confidence gating.
"""

from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging


class HOPICalculator:
    """Calculates the HOPI index from multi-domain indicators."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Domain definitions with weights (updated per 57-indicator registry)
        self.domains = {
            'economy': {
                'weight': 1.0,
                'indicators': ['Treasury', 'GroceryCPI', 'MarketVolatility', 'GDPGrowth',
                              'BankFailures', 'DiscountWindow', 'DepositFlow'],
                'critical': ['MarketVolatility']
            },
            'jobs_labor': {
                'weight': 1.0,
                'indicators': ['JoblessClaims', 'StrikeActivity', 'LuxuryCollapse'],
                'critical': []
            },
            'rights_governance': {
                'weight': 1.1,
                'indicators': ['AISurveillance', 'ACLEDProtests'],
                'critical': []
            },
            'security_infrastructure': {
                'weight': 1.25,
                'indicators': ['CISACyber', 'GridReliability', 'WHODisease', 'HormuzRisk',
                              'PharmacyShortage', 'CDCAlerts', 'FEMADisasters'],
                'critical': []
            },
            'energy': {
                'weight': 1.1,
                'indicators': ['SPR', 'NatGasStorage', 'GridEmergency', 'OFACOil'],
                'critical': []
            },
            'supply_chain': {
                'weight': 1.0,
                'indicators': ['PortCongestion', 'FreightIndex', 'ChipLeadTime',
                              'PharmacyShortageIndex', 'JODIOil'],
                'critical': []
            },
            'telecommunications': {
                'weight': 0.9,
                'indicators': ['UnderseaCable', 'BGPAnomalies', 'CellOutages'],
                'critical': []
            },
            'water_infrastructure': {
                'weight': 0.9,
                'indicators': ['WaterAlerts', 'ReservoirLevel'],
                'critical': []
            },
            'ai_window': {
                'weight': 1.0,
                'indicators': ['AILayoffs'],
                'critical': []
            },
            'global_conflict': {
                'weight': 1.25,
                'indicators': ['GlobalConflict', 'TaiwanPLA', 'NATOReadiness',
                              'NuclearTests', 'DefenseSpending'],
                'critical': ['NATOReadiness']
            },
            'domestic_control': {
                'weight': 1.2,
                'indicators': ['ICEDetention', 'FederalRegulations', 'LibertyLitigation', 'ControlBills'],
                'critical': []
            },
            'travel_mobility': {
                'weight': 0.8,
                'indicators': ['TravelAdvisories', 'BorderWait', 'TSAThroughput'],
                'critical': []
            },
            'housing_mortgage': {
                'weight': 0.9,
                'indicators': ['MortgageDelinquency', 'RateShock'],
                'critical': []
            },
            'aviation': {
                'weight': 0.8,
                'indicators': ['GroundStops', 'FlightDelays', 'TFRCount'],
                'critical': []
            },
            'cult_meta': {
                'weight': 0.7,
                'indicators': ['SocialStressSignals'],
                'critical': []
            }
        }
        
        # Pair caps to prevent double-counting correlated indicators
        self.pair_caps = [
            {
                # Pharmacy shortage count vs severity index
                'pair': ['PharmacyShortage', 'PharmacyShortageIndex'],
                'domain': 'supply_chain',
                'cap_factor': 1.5  # Cap at 1.5x a single red
            }
        ]
        
        # History for trend detection
        self.history = []
        self.max_history = 10  # Keep last 10 polls
        
    def calculate(self, indicators: Dict[str, Dict], stale_indicators: Set[str]) -> Dict:
        """
        Calculate HOPI index and domain scores.
        
        Args:
            indicators: Dict of indicator_name -> {color: 0/1/2, value: x, confirmed: bool}
            stale_indicators: Set of indicator names that have stale data
            
        Returns:
            Dict with HOPI, domain_scores, confidence, details
        """
        # Store current poll
        self._update_history(indicators)
        
        # Calculate points for each indicator
        indicator_points = self._calculate_indicator_points(indicators)
        
        # Apply pair caps
        indicator_points = self._apply_pair_caps(indicator_points, indicators)
        
        # Calculate domain scores
        domain_scores = self._calculate_domain_scores(indicator_points)
        
        # Apply trend bonus
        domain_scores = self._apply_trend_bonus(domain_scores)
        
        # Calculate overall HOPI
        hopi = self._calculate_hopi(domain_scores)
        
        # Calculate confidence
        confidence = self._calculate_confidence(indicators, stale_indicators)
        
        # Count reds by type
        red_counts = self._count_reds(indicators)
        
        return {
            'hopi': round(hopi, 3),
            'confidence': round(confidence, 3),
            'domain_scores': {k: round(v, 3) for k, v in domain_scores.items()},
            'total_reds': red_counts['total'],
            'critical_reds': red_counts['critical'],
            'single_source_reds': red_counts['single_source'],
            'stale_count': len(stale_indicators),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _calculate_indicator_points(self, indicators: Dict[str, Dict]) -> Dict[str, float]:
        """Calculate points for each indicator."""
        points = {}
        
        for domain_name, domain_info in self.domains.items():
            domain_weight = domain_info['weight']
            critical_set = set(domain_info['critical'])
            
            for indicator in domain_info['indicators']:
                if indicator in indicators:
                    color = indicators[indicator].get('color', 0)
                    is_critical = indicator in critical_set
                    
                    # Points = color × domain_weight × (2 if critical else 1)
                    indicator_points = color * domain_weight * (2 if is_critical else 1)
                    points[indicator] = indicator_points
                    
                    if indicator_points > 0:
                        self.logger.debug(f"{indicator}: {indicator_points} points "
                                        f"(color={color}, weight={domain_weight}, "
                                        f"critical={is_critical})")
        
        return points
    
    def _apply_pair_caps(self, points: Dict[str, float], indicators: Dict[str, Dict]) -> Dict[str, float]:
        """Apply caps to correlated pairs."""
        capped_points = points.copy()
        
        for cap_rule in self.pair_caps:
            pair = cap_rule['pair']
            domain = cap_rule['domain']
            cap_factor = cap_rule['cap_factor']
            
            # Check if both indicators exist and have points
            if all(ind in points for ind in pair):
                pair_total = sum(points[ind] for ind in pair)
                
                # Calculate cap based on what one red would contribute
                domain_weight = self.domains[domain]['weight']
                red_value = 2 * domain_weight  # Base red contribution
                cap = red_value * cap_factor
                
                if pair_total > cap:
                    # Reduce proportionally
                    scale = cap / pair_total
                    for ind in pair:
                        capped_points[ind] = points[ind] * scale
                    
                    self.logger.info(f"Capped pair {pair}: {pair_total:.1f} -> {cap:.1f}")
        
        return capped_points
    
    def _calculate_domain_scores(self, points: Dict[str, float]) -> Dict[str, float]:
        """Calculate normalized domain scores."""
        domain_scores = {}
        
        for domain_name, domain_info in self.domains.items():
            domain_points = sum(points.get(ind, 0) for ind in domain_info['indicators'])
            domain_weight = domain_info['weight']
            n_indicators = len(domain_info['indicators'])
            
            # D_d = Σ(points_i) / (2 × weight_d × N_d)
            if n_indicators > 0:
                max_possible = 2 * domain_weight * n_indicators
                domain_score = domain_points / max_possible
                domain_scores[domain_name] = min(1.0, domain_score)
            else:
                domain_scores[domain_name] = 0.0
                
        return domain_scores
    
    def _apply_trend_bonus(self, domain_scores: Dict[str, float]) -> Dict[str, float]:
        """Apply +0.10 bonus if ≥2 indicators rose by ≥1 color in last 3 polls."""
        if len(self.history) < 2:
            return domain_scores
        
        bonused_scores = domain_scores.copy()
        
        # Compare current to 3 polls ago (or oldest available)
        lookback = min(3, len(self.history) - 1)
        old_poll = self.history[-lookback - 1]
        current_poll = self.history[-1]
        
        for domain_name, domain_info in self.domains.items():
            rising_count = 0
            
            for indicator in domain_info['indicators']:
                if indicator in current_poll and indicator in old_poll:
                    old_color = old_poll[indicator].get('color', 0)
                    new_color = current_poll[indicator].get('color', 0)
                    
                    if new_color > old_color:
                        rising_count += 1
            
            if rising_count >= 2:
                bonused_scores[domain_name] = min(1.0, bonused_scores[domain_name] + 0.10)
                self.logger.info(f"Trend bonus for {domain_name}: {rising_count} rising indicators")
        
        return bonused_scores
    
    def _calculate_hopi(self, domain_scores: Dict[str, float]) -> float:
        """Calculate overall HOPI as weighted mean of domain scores."""
        # Domain weights for HOPI calculation (per 57-indicator registry)
        hopi_weights = {
            'economy': 1.0,
            'jobs_labor': 1.0,
            'rights_governance': 1.1,
            'security_infrastructure': 1.25,
            'energy': 1.1,
            'supply_chain': 1.0,
            'telecommunications': 0.9,
            'water_infrastructure': 0.9,
            'ai_window': 1.0,
            'global_conflict': 1.25,
            'domestic_control': 1.2,
            'travel_mobility': 0.8,
            'housing_mortgage': 0.9,
            'aviation': 0.8,
            'cult_meta': 0.7
        }
        
        total_weighted = 0.0
        total_weight = 0.0
        
        for domain, score in domain_scores.items():
            weight = hopi_weights.get(domain, 1.0)
            total_weighted += score * weight
            total_weight += weight
        
        return total_weighted / total_weight if total_weight > 0 else 0.0
    
    def _calculate_confidence(self, indicators: Dict[str, Dict], stale_indicators: Set[str]) -> float:
        """Calculate confidence score."""
        total_indicators = len(indicators)
        stale_count = len(stale_indicators)
        
        # Count single-source reds
        red_counts = self._count_reds(indicators)
        total_reds = max(1, red_counts['total'])
        single_source_reds = red_counts['single_source']
        
        # C = 1 - (stale/total) - 0.15 × (single_source_reds/total_reds)
        confidence = 1.0
        confidence -= (stale_count / total_indicators) if total_indicators > 0 else 0
        confidence -= 0.15 * (single_source_reds / total_reds)
        
        return max(0.0, min(1.0, confidence))
    
    def _count_reds(self, indicators: Dict[str, Dict]) -> Dict[str, int]:
        """Count different types of red indicators."""
        total_reds = 0
        critical_reds = 0
        single_source_reds = 0
        
        # Get all critical indicators
        all_critical = set()
        for domain_info in self.domains.values():
            all_critical.update(domain_info['critical'])
        
        for indicator, data in indicators.items():
            if data.get('color') == 2:  # Red
                total_reds += 1
                
                if indicator in all_critical:
                    critical_reds += 1
                
                # Check if single-source (mock data or unconfirmed)
                if not data.get('confirmed', True) or data.get('source') == 'mock':
                    single_source_reds += 1
        
        return {
            'total': total_reds,
            'critical': critical_reds,
            'single_source': single_source_reds
        }
    
    def _update_history(self, indicators: Dict[str, Dict]):
        """Update history for trend detection."""
        self.history.append(indicators.copy())
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history.pop(0)