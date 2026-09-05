"""
AutoGen Financial Analysis System
Enterprise-grade financial data analysis using Microsoft's AutoGen framework
"""

__version__ = "1.0.0"
__author__ = "AutoGen Financial Analysis Team"
__email__ = "team@autogen-financial.com"

from .agents import FinancialAgentFactory, AgentOrchestrator
from .data import EnterpriseDataCollector
from .analysis import AdvancedFinancialAnalyzer
from .risk import AdvancedRiskAnalyzer
from .quant import QuantitativeAnalyzer
from .cache import CacheManager
from .monitoring import SystemMonitor
from .security import SecurityManager
from .config import ConfigurationManager

__all__ = [
    "FinancialAgentFactory",
    "AgentOrchestrator",
    "EnterpriseDataCollector",
    "AdvancedFinancialAnalyzer",
    "AdvancedRiskAnalyzer",
    "QuantitativeAnalyzer",
    "CacheManager",
    "SystemMonitor",
    "SecurityManager",
    "ConfigurationManager"
]