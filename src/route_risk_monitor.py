"""
Route Risk Monitor — threshold-based reroute decisions for supply chain risk.

Extracted from argus-system: monitors shipping/trade routes for geopolitical
disruption risk and suggests rerouting when risk exceeds thresholds.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RouteStatus:
    """Status of a monitored route."""
    route_name: str
    origin: str
    destination: str
    risk_score: float  # 0.0 to 1.0
    bottleneck: str
    shipping_cost_index: float
    transit_days: int
    last_updated: str


@dataclass
class RerouteDecision:
    """Decision about whether to reroute."""
    action: str  # "PROCEED", "REROUTE", "ALERT_NO_ALTERNATIVE", "UNKNOWN_ROUTE"
    current_route: str
    current_risk: float
    bottleneck: Optional[str]
    suggested_route: Optional[str] = None
    suggested_risk: Optional[float] = None
    reason: Optional[str] = None


class RouteRiskMonitor:
    """
    Monitors shipping/trade routes for risk and suggests rerouting.
    
    Usage:
        monitor = RouteRiskMonitor(threshold=0.7)
        monitor.add_route(RouteStatus("route_a", "China", "US", 0.8, "South China Sea", 1.2, 14, "2026-01-01"))
        monitor.add_route(RouteStatus("route_b", "China", "US", 0.3, "Pacific", 1.0, 18, "2026-01-01"))
        decision = monitor.evaluate("route_a")
        print(decision.action)  # "REROUTE"
    """
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.routes: dict = {}
    
    def add_route(self, route: RouteStatus):
        """Add or update a route."""
        self.routes[route.route_name] = route
    
    def evaluate(self, current_route: str) -> RerouteDecision:
        """Evaluate whether to reroute from current route."""
        if current_route not in self.routes:
            return RerouteDecision(
                action="UNKNOWN_ROUTE",
                current_route=current_route,
                current_risk=0.0,
                bottleneck=None,
                reason=f"Route '{current_route}' not found in monitor",
            )
        
        current = self.routes[current_route]
        
        if current.risk_score < self.threshold:
            return RerouteDecision(
                action="PROCEED",
                current_route=current_route,
                current_risk=current.risk_score,
                bottleneck=current.bottleneck,
                reason=f"Risk {current.risk_score:.2f} below threshold {self.threshold:.2f}",
            )
        
        # Risk exceeds threshold — find alternatives
        alternatives = sorted(
            [r for r in self.routes.values() if r.route_name != current_route],
            key=lambda r: r.risk_score,
        )
        
        if not alternatives:
            return RerouteDecision(
                action="ALERT_NO_ALTERNATIVE",
                current_route=current_route,
                current_risk=current.risk_score,
                bottleneck=current.bottleneck,
                reason=f"Risk {current.risk_score:.2f} exceeds threshold {self.threshold:.2f} but no alternatives available",
            )
        
        best_alt = alternatives[0]
        return RerouteDecision(
            action="REROUTE",
            current_route=current_route,
            current_risk=current.risk_score,
            bottleneck=current.bottleneck,
            suggested_route=best_alt.route_name,
            suggested_risk=best_alt.risk_score,
            reason=f"Risk {current.risk_score:.2f} exceeds threshold {self.threshold:.2f}, reroute to {best_alt.route_name} (risk: {best_alt.risk_score:.2f})",
        )
    
    def get_all_route_status(self) -> list:
        """Get status of all monitored routes."""
        return sorted(self.routes.values(), key=lambda r: r.risk_score, reverse=True)
    
    def get_high_risk_routes(self) -> list:
        """Get routes exceeding risk threshold."""
        return [r for r in self.routes.values() if r.risk_score >= self.threshold]
