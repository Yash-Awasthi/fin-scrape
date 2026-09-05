"""
Define your monitored sea routes as sequences of chokepoints/ports.
Edit this file to match your actual shipping network.
"""

ROUTES = {
    "Asia-US_via_Suez": ["Suez Canal", "Strait of Gibraltar", "New York"],
    "Asia-US_via_Panama": ["Strait of Malacca", "Panama Canal", "Los Angeles"],
    "Asia-Europe_via_Suez": ["Strait of Malacca", "Suez Canal", "Rotterdam"],
    "Asia-Europe_via_Cape": ["Strait of Malacca", "Cape of Good Hope", "Rotterdam"],
}

# Flattened, de-duplicated list of every location that needs monitoring
ALL_LOCATIONS = sorted(set(loc for route in ROUTES.values() for loc in route))

# Risk threshold above which a reroute alert fires (0-100 scale). Tune after backtesting.
RISK_THRESHOLD = 60

# Rolling window (hours) used when recomputing a location's risk score
RISK_WINDOW_HOURS = 168  # 7 days
