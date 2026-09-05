"""Quantitative Analysis Module Initialization"""

from .portfolio_optimizer import PortfolioOptimizer
from .factor_models import FactorModels

__all__ = [
    "PortfolioOptimizer",
    "FactorModels",
    "QuantitativeAnalyzer"
]


class QuantitativeAnalyzer:
    """Quantitative analyzer wrapper for portfolio optimization and factor models"""
    
    def __init__(self):
        self.portfolio_optimizer = PortfolioOptimizer()
        self.factor_models = FactorModels()
    
    async def analyze_portfolio(self, returns_data, objective="maximize_sharpe", constraints=None):
        """Analyze portfolio using optimization techniques"""
        try:
            # Convert objective string to enum if needed
            from .portfolio_optimizer import OptimizationObjective
            if isinstance(objective, str):
                objective = OptimizationObjective(objective.lower())
            
            result = self.portfolio_optimizer.optimize_portfolio(
                returns_data=returns_data,
                objective=objective,
                constraints=constraints
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Portfolio analysis failed: {str(e)}")
    
    async def analyze_factors(self, returns, factor_data, model_type="fama_french"):
        """Analyze factors using factor models"""
        try:
            # Convert model type string to enum if needed
            from .factor_models import FactorType
            if isinstance(model_type, str):
                model_type = FactorType(model_type.lower())
            
            result = self.factor_models.analyze_portfolio_factors(
                portfolio_returns=returns,
                factor_data=factor_data,
                model_type=model_type
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Factor analysis failed: {str(e)}")
    
    async def calculate_efficient_frontier(self, returns_data, n_points=100):
        """Calculate efficient frontier"""
        try:
            result = self.portfolio_optimizer.calculate_efficient_frontier(
                returns_data=returns_data,
                n_points=n_points
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Efficient frontier calculation failed: {str(e)}")
    
    async def backtest_portfolio(self, returns_data, weights):
        """Backtest portfolio performance"""
        try:
            result = self.portfolio_optimizer.backtest_portfolio(
                returns_data=returns_data,
                weights=weights
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Portfolio backtest failed: {str(e)}")