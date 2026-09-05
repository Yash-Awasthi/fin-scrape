"""
API Clients for War-Probability OSINT.

Exposes all data-ingestion modules for easy top-level imports:
    from api_clients import adsb_client, foot_traffic_client, gdelt_client, finance_client
"""

from api_clients import adsb_client
from api_clients import foot_traffic_client
from api_clients import gdelt_client
from api_clients import finance_client

__all__ = [
    "adsb_client",
    "foot_traffic_client",
    "gdelt_client",
    "finance_client",
]
