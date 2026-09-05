"""
Factor Models
Comprehensive factor analysis and modeling for quantitative finance
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from scipy import stats
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm


class FactorType(Enum):
    """Factor model types"""
    MARKET = "market"
    FAMA_FRENCH = "fama_french"
    CARHART = "carhart"
    PCA = "pca"
    STATISTICAL = "statistical"
    FUNDAMENTAL = "fundamental"
    MACROECONOMIC = "macroeconomic"
    ALTERNATIVE = "alternative"


@dataclass
class Factor:
    """Individual factor definition"""
    name: str
    type: FactorType
    description: str
    data_source: str
    calculation_method: str
    is_long_short: bool = False
    universe: str = "us_equities"


@dataclass
class FactorExposure:
    """Factor exposure for a security or portfolio"""
    factor_name: str
    exposure: float
    t_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool = False


@dataclass
class FactorReturn:
    """Factor return for a specific period"""
    factor_name: str
    period_start: datetime
    period_end: datetime
    return_value: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float


@dataclass
class FactorModel:
    """Complete factor model specification"""
    model_name: str
    model_type: FactorType
    factors: List[Factor]
    estimation_period: str
    r_squared: float
    adjusted_r_squared: float
    factor_exposures: List[FactorExposure]
    model_significance: float
    residuals_stats: Dict[str, float]
    creation_date: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioFactorAnalysis:
    """Factor analysis results for a portfolio"""
    portfolio_id: str
    analysis_date: datetime
    factor_model: FactorModel
    total_risk_explained: float
    active_factor_exposures: List[FactorExposure]
    factor_attribution: Dict[str, float]
    risk_budget: Dict[str, float]
    performance_attribution: Dict[str, float]
    factor_tilt: Dict[str, str]


class FactorModels:
    """Comprehensive factor modeling system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.factors_database = self._initialize_factors_database()

    def _initialize_factors_database(self) -> Dict[str, Factor]:
        """Initialize standard factors database"""
        return {
            # Market factors
            "market": Factor(
                name="Market",
                type=FactorType.MARKET,
                description="Market excess return factor",
                data_source="market_data",
                calculation_method="Market return minus risk-free rate"
            ),

            # Fama-French factors
            "smb": Factor(
                name="SMB",
                type=FactorType.FAMA_FRENCH,
                description="Small minus big factor",
                data_source="ken_french",
                calculation_method="Small cap return minus large cap return",
                is_long_short=True
            ),

            "hml": Factor(
                name="HML",
                type=FactorType.FAMA_FRENCH,
                description="High minus low factor",
                data_source="ken_french",
                calculation_method="Value stock return minus growth stock return",
                is_long_short=True
            ),

            # Carhart momentum factor
            "mom": Factor(
                name="MOM",
                type=FactorType.CARHART,
                description="Momentum factor",
                data_source="ken_french",
                calculation_method="High momentum return minus low momentum return",
                is_long_short=True
            ),

            # Fundamental factors
            "quality": Factor(
                name="Quality",
                type=FactorType.FUNDAMENTAL,
                description="Quality factor based on profitability and leverage",
                data_source="fundamental_data",
                calculation_method="Composite score of ROE, debt ratios, and earnings quality"
            ),

            "value": Factor(
                name="Value",
                type=FactorType.FUNDAMENTAL,
                description="Value factor based on valuation multiples",
                data_source="fundamental_data",
                calculation_method="Composite score of P/E, P/B, and EV/EBITDA ratios"
            ),

            "momentum": Factor(
                name="Momentum",
                type=FactorType.FUNDAMENTAL,
                description="Price momentum factor",
                data_source="price_data",
                calculation_method="12-month price momentum excluding recent month"
            ),

            "low_volatility": Factor(
                name="Low Volatility",
                type=FactorType.FUNDAMENTAL,
                description="Low volatility factor",
                data_source="price_data",
                calculation_method="12-month historical volatility"
            ),

            # Macroeconomic factors
            "inflation": Factor(
                name="Inflation",
                type=FactorType.MACROECONOMIC,
                description="Inflation sensitivity factor",
                data_source="economic_data",
                calculation_method="CPI change rate"
            ),

            "interest_rate": Factor(
                name="Interest Rate",
                type=FactorType.MACROECONOMIC,
                description="Interest rate sensitivity factor",
                data_source="economic_data",
                calculation_method="10-year Treasury yield change"
            )
        }

    def build_fama_french_model(self, returns: pd.Series, factor_data: pd.DataFrame,
                              risk_free_rate: float = 0.02) -> Optional[FactorModel]:
        """Build Fama-French 3-factor model"""
        try:
            # Required factors for Fama-French model
            required_factors = ['market', 'smb', 'hml']
            available_factors = [f for f in required_factors if f in factor_data.columns]

            if len(available_factors) < len(required_factors):
                self.logger.warning("Insufficient factors for Fama-French model")
                return None

            # Prepare data
            X = factor_data[available_factors]
            y = returns - risk_free_rate / 252  # Excess returns

            # Add constant term
            X = sm.add_constant(X)

            # Fit model
            model = sm.OLS(y, X).fit()

            # Create factor exposures
            factor_exposures = []
            for factor in available_factors:
                exposure = model.params[factor]
                t_stat = model.tvalues[factor]
                p_value = model.pvalues[factor]
                conf_int = model.conf_int().loc[factor].tolist()

                factor_exposures.append(FactorExposure(
                    factor_name=factor,
                    exposure=exposure,
                    t_statistic=t_stat,
                    p_value=p_value,
                    confidence_interval=tuple(conf_int),
                    is_significant=p_value < 0.05
                ))

            # Get factor definitions
            factors = [self.factors_database[f] for f in available_factors]

            return FactorModel(
                model_name="Fama-French 3-Factor",
                model_type=FactorType.FAMA_FRENCH,
                factors=factors,
                estimation_period="3_years",
                r_squared=model.rsquared,
                adjusted_r_squared=model.rsquared_adj,
                factor_exposures=factor_exposures,
                model_significance=model.f_pvalue,
                residuals_stats={
                    "skewness": stats.skew(model.resid),
                    "kurtosis": stats.kurtosis(model.resid),
                    "jarque_bera": stats.jarque_bera(model.resid)[0]
                }
            )

        except Exception as e:
            self.logger.error(f"Error building Fama-French model: {str(e)}")
            return None

    def build_carhart_model(self, returns: pd.Series, factor_data: pd.DataFrame,
                           risk_free_rate: float = 0.02) -> Optional[FactorModel]:
        """Build Carhart 4-factor model"""
        try:
            # Required factors for Carhart model
            required_factors = ['market', 'smb', 'hml', 'mom']
            available_factors = [f for f in required_factors if f in factor_data.columns]

            if len(available_factors) < len(required_factors):
                self.logger.warning("Insufficient factors for Carhart model")
                return None

            # Prepare data
            X = factor_data[available_factors]
            y = returns - risk_free_rate / 252  # Excess returns

            # Add constant term
            X = sm.add_constant(X)

            # Fit model
            model = sm.OLS(y, X).fit()

            # Create factor exposures
            factor_exposures = []
            for factor in available_factors:
                exposure = model.params[factor]
                t_stat = model.tvalues[factor]
                p_value = model.pvalues[factor]
                conf_int = model.conf_int().loc[factor].tolist()

                factor_exposures.append(FactorExposure(
                    factor_name=factor,
                    exposure=exposure,
                    t_statistic=t_stat,
                    p_value=p_value,
                    confidence_interval=tuple(conf_int),
                    is_significant=p_value < 0.05
                ))

            # Get factor definitions
            factors = [self.factors_database[f] for f in available_factors]

            return FactorModel(
                model_name="Carhart 4-Factor",
                model_type=FactorType.CARHART,
                factors=factors,
                estimation_period="3_years",
                r_squared=model.rsquared,
                adjusted_r_squared=model.rsquared_adj,
                factor_exposures=factor_exposures,
                model_significance=model.f_pvalue,
                residuals_stats={
                    "skewness": stats.skew(model.resid),
                    "kurtosis": stats.kurtosis(model.resid),
                    "jarque_bera": stats.jarque_bera(model.resid)[0]
                }
            )

        except Exception as e:
            self.logger.error(f"Error building Carhart model: {str(e)}")
            return None

    def build_pca_model(self, returns_matrix: pd.DataFrame, n_components: int = 5) -> Optional[FactorModel]:
        """Build PCA-based factor model"""
        try:
            if len(returns_matrix.columns) < n_components:
                n_components = len(returns_matrix.columns)

            # Standardize returns
            scaler = StandardScaler()
            scaled_returns = scaler.fit_transform(returns_matrix)

            # Perform PCA
            pca = PCA(n_components=n_components)
            pca.fit(scaled_returns)

            # Create factor definitions
            factors = []
            for i in range(n_components):
                factor = Factor(
                    name=f"PCA_Factor_{i+1}",
                    type=FactorType.PCA,
                    description=f"Principal component {i+1} explaining {pca.explained_variance_ratio_[i]:.1%} of variance",
                    data_source="returns_data",
                    calculation_method="Principal component analysis"
                )
                factors.append(factor)

            # Calculate factor exposures (factor loadings)
            factor_exposures = []
            for i, asset in enumerate(returns_matrix.columns):
                for j in range(n_components):
                    exposure = pca.components_[j, i]
                    t_stat = exposure / (pca.components_[j].std() / np.sqrt(len(pca.components_[j])))
                    p_value = 2 * (1 - stats.norm.cdf(abs(t_stat)))

                    factor_exposures.append(FactorExposure(
                        factor_name=f"PCA_Factor_{j+1}",
                        exposure=exposure,
                        t_statistic=t_stat,
                        p_value=p_value,
                        confidence_interval=(exposure - 1.96 * exposure / np.sqrt(len(pca.components_[j])),
                                            exposure + 1.96 * exposure / np.sqrt(len(pca.components_[j]))),
                        is_significant=p_value < 0.05
                    ))

            return FactorModel(
                model_name="PCA Factor Model",
                model_type=FactorType.PCA,
                factors=factors,
                estimation_period="3_years",
                r_squared=sum(pca.explained_variance_ratio_),
                adjusted_r_squared=sum(pca.explained_variance_ratio_),
                factor_exposures=factor_exposures,
                model_significance=0.05,  # PCA doesn't have p-value in traditional sense
                residuals_stats={
                    "total_variance_explained": sum(pca.explained_variance_ratio_),
                    "n_components": n_components
                }
            )

        except Exception as e:
            self.logger.error(f"Error building PCA model: {str(e)}")
            return None

    def build_fundamental_model(self, returns: pd.Series, fundamental_data: pd.DataFrame) -> Optional[FactorModel]:
        """Build fundamental factor model"""
        try:
            # Required fundamental factors
            required_factors = ['quality', 'value', 'momentum', 'low_volatility']
            available_factors = [f for f in required_factors if f in fundamental_data.columns]

            if not available_factors:
                self.logger.warning("No fundamental factors available")
                return None

            # Prepare data
            X = fundamental_data[available_factors]
            y = returns

            # Add constant term
            X = sm.add_constant(X)

            # Fit model
            model = sm.OLS(y, X).fit()

            # Create factor exposures
            factor_exposures = []
            for factor in available_factors:
                exposure = model.params[factor]
                t_stat = model.tvalues[factor]
                p_value = model.pvalues[factor]
                conf_int = model.conf_int().loc[factor].tolist()

                factor_exposures.append(FactorExposure(
                    factor_name=factor,
                    exposure=exposure,
                    t_statistic=t_stat,
                    p_value=p_value,
                    confidence_interval=tuple(conf_int),
                    is_significant=p_value < 0.05
                ))

            # Get factor definitions
            factors = [self.factors_database[f] for f in available_factors]

            return FactorModel(
                model_name="Fundamental Factor Model",
                model_type=FactorType.FUNDAMENTAL,
                factors=factors,
                estimation_period="3_years",
                r_squared=model.rsquared,
                adjusted_r_squared=model.rsquared_adj,
                factor_exposures=factor_exposures,
                model_significance=model.f_pvalue,
                residuals_stats={
                    "skewness": stats.skew(model.resid),
                    "kurtosis": stats.kurtosis(model.resid),
                    "jarque_bera": stats.jarque_bera(model.resid)[0]
                }
            )

        except Exception as e:
            self.logger.error(f"Error building fundamental model: {str(e)}")
            return None

    def calculate_factor_returns(self, factor_data: pd.DataFrame, returns_data: pd.DataFrame) -> List[FactorReturn]:
        """Calculate factor returns over time"""
        factor_returns = []

        try:
            for factor in factor_data.columns:
                factor_series = factor_data[factor]

                # Calculate basic metrics
                annual_return = factor_series.mean() * 252
                annual_vol = factor_series.std() * np.sqrt(252)
                sharpe_ratio = annual_return / annual_vol if annual_vol > 0 else 0

                # Calculate maximum drawdown
                cumulative = np.cumprod(1 + factor_series)
                peak = np.maximum.accumulate(cumulative)
                drawdown = (peak - cumulative) / peak
                max_drawdown = np.max(drawdown)

                # Calculate win rate
                win_rate = (factor_series > 0).mean()

                # Create monthly returns (assuming daily data)
                monthly_returns = factor_series.resample('M').apply(lambda x: (1 + x).prod() - 1)

                for period_end, monthly_return in monthly_returns.items():
                    factor_return = FactorReturn(
                        factor_name=factor,
                        period_start=period_end - timedelta(days=30),
                        period_end=period_end,
                        return_value=monthly_return,
                        sharpe_ratio=sharpe_ratio,
                        max_drawdown=max_drawdown,
                        win_rate=win_rate
                    )
                    factor_returns.append(factor_return)

        except Exception as e:
            self.logger.error(f"Error calculating factor returns: {str(e)}")

        return factor_returns

    def analyze_portfolio_factors(self, portfolio_returns: pd.Series,
                                factor_data: pd.DataFrame,
                                benchmark_returns: pd.Series = None,
                                model_type: FactorType = FactorType.FAMA_FRENCH) -> Optional[PortfolioFactorAnalysis]:
        """Analyze portfolio factor exposures and attributions"""
        try:
            # Build appropriate factor model
            if model_type == FactorType.FAMA_FRENCH:
                factor_model = self.build_fama_french_model(portfolio_returns, factor_data)
            elif model_type == FactorType.CARHART:
                factor_model = self.build_carhart_model(portfolio_returns, factor_data)
            elif model_type == FactorType.PCA:
                factor_model = self.build_pca_model(factor_data)
            else:
                factor_model = self.build_fundamental_model(portfolio_returns, factor_data)

            if not factor_model:
                return None

            # Calculate factor attribution
            factor_attribution = self._calculate_factor_attribution(factor_model, portfolio_returns)

            # Calculate risk budget
            risk_budget = self._calculate_factor_risk_budget(factor_model)

            # Calculate performance attribution
            performance_attribution = self._calculate_performance_attribution(factor_model, portfolio_returns)

            # Determine factor tilts
            factor_tilt = self._determine_factor_tilts(factor_model)

            # Calculate active factor exposures (vs benchmark)
            active_exposures = factor_model.factor_exposures
            if benchmark_returns is not None:
                benchmark_model = self.build_fama_french_model(benchmark_returns, factor_data)
                if benchmark_model:
                    active_exposures = self._calculate_active_exposures(factor_model, benchmark_model)

            return PortfolioFactorAnalysis(
                portfolio_id="portfolio_1",
                analysis_date=datetime.now(),
                factor_model=factor_model,
                total_risk_explained=factor_model.r_squared,
                active_factor_exposures=active_exposures,
                factor_attribution=factor_attribution,
                risk_budget=risk_budget,
                performance_attribution=performance_attribution,
                factor_tilt=factor_tilt
            )

        except Exception as e:
            self.logger.error(f"Error analyzing portfolio factors: {str(e)}")
            return None

    def _calculate_factor_attribution(self, factor_model: FactorModel, returns: pd.Series) -> Dict[str, float]:
        """Calculate factor risk attribution"""
        attribution = {}

        for exposure in factor_model.factor_exposures:
            factor_name = exposure.factor_name
            factor_exposure = exposure.exposure

            # Calculate contribution to total risk (simplified)
            total_factor_risk = sum(exp.exposure**2 for exp in factor_model.factor_exposures)
            if total_factor_risk > 0:
                attribution[factor_name] = (factor_exposure**2) / total_factor_risk
            else:
                attribution[factor_name] = 0

        return attribution

    def _calculate_factor_risk_budget(self, factor_model: FactorModel) -> Dict[str, float]:
        """Calculate factor risk budget allocation"""
        risk_budget = {}

        for exposure in factor_model.factor_exposures:
            factor_name = exposure.factor_name
            factor_exposure = abs(exposure.exposure)

            # Budget proportional to absolute exposure
            total_exposure = sum(abs(exp.exposure) for exp in factor_model.factor_exposures)
            if total_exposure > 0:
                risk_budget[factor_name] = factor_exposure / total_exposure
            else:
                risk_budget[factor_name] = 0

        return risk_budget

    def _calculate_performance_attribution(self, factor_model: FactorModel, returns: pd.Series) -> Dict[str, float]:
        """Calculate performance attribution to factors"""
        attribution = {}

        for exposure in factor_model.factor_exposures:
            factor_name = exposure.factor_name
            factor_exposure = exposure.exposure

            # Simplified performance attribution
            # In practice, this would use factor returns
            attribution[factor_name] = factor_exposure * 0.01  # Assume 1% factor return

        return attribution

    def _determine_factor_tilts(self, factor_model: FactorModel) -> Dict[str, str]:
        """Determine factor tilts based on exposures"""
        tilts = {}

        for exposure in factor_model.factor_exposures:
            factor_name = exposure.factor_name
            factor_exposure = exposure.exposure

            if factor_exposure > 0.5:
                tilts[factor_name] = "strong_long"
            elif factor_exposure > 0.1:
                tilts[factor_name] = "moderate_long"
            elif factor_exposure < -0.5:
                tilts[factor_name] = "strong_short"
            elif factor_exposure < -0.1:
                tilts[factor_name] = "moderate_short"
            else:
                tilts[factor_name] = "neutral"

        return tilts

    def _calculate_active_exposures(self, portfolio_model: FactorModel,
                                   benchmark_model: FactorModel) -> List[FactorExposure]:
        """Calculate active factor exposures vs benchmark"""
        active_exposures = []

        for port_exp in portfolio_model.factor_exposures:
            factor_name = port_exp.factor_name

            # Find corresponding benchmark exposure
            bench_exp = next((exp for exp in benchmark_model.factor_exposures
                             if exp.factor_name == factor_name), None)

            if bench_exp:
                active_exposure = port_exp.exposure - bench_exp.exposure

                # Calculate significance for active exposure
                active_t_stat = (active_exposure / np.sqrt(port_exp.t_statistic**2 + bench_exp.t_statistic**2))
                active_p_value = 2 * (1 - stats.norm.cdf(abs(active_t_stat)))

                active_exposures.append(FactorExposure(
                    factor_name=factor_name,
                    exposure=active_exposure,
                    t_statistic=active_t_stat,
                    p_value=active_p_value,
                    confidence_interval=(active_exposure - 1.96 * active_exposure / np.sqrt(len(portfolio_model.factor_exposures)),
                                        active_exposure + 1.96 * active_exposure / np.sqrt(len(portfolio_model.factor_exposures))),
                    is_significant=active_p_value < 0.05
                ))

        return active_exposures

    def perform_factor_momentum_analysis(self, factor_returns: pd.DataFrame) -> Dict[str, float]:
        """Analyze momentum in factor returns"""
        momentum_scores = {}

        try:
            for factor in factor_returns.columns:
                factor_series = factor_returns[factor]

                # Calculate various momentum metrics
                momentum_1m = factor_series.tail(21).sum()  # 1 month
                momentum_3m = factor_series.tail(63).sum()  # 3 months
                momentum_6m = factor_series.tail(126).sum()  # 6 months
                momentum_12m = factor_series.tail(252).sum()  # 12 months

                # Combine momentum scores
                combined_momentum = (0.4 * momentum_1m + 0.3 * momentum_3m +
                                   0.2 * momentum_6m + 0.1 * momentum_12m)

                momentum_scores[factor] = combined_momentum

        except Exception as e:
            self.logger.error(f"Error performing factor momentum analysis: {str(e)}")

        return momentum_scores

    def calculate_factor_correlations(self, factor_returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix of factor returns"""
        try:
            return factor_returns.corr()
        except Exception as e:
            self.logger.error(f"Error calculating factor correlations: {str(e)}")
            return pd.DataFrame()

    def cluster_securities_by_factors(self, factor_exposures: pd.DataFrame, n_clusters: int = 5) -> pd.DataFrame:
        """Cluster securities based on factor exposures"""
        try:
            # Standardize exposures
            scaler = StandardScaler()
            scaled_exposures = scaler.fit_transform(factor_exposures)

            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(scaled_exposures)

            # Create results DataFrame
            results = factor_exposures.copy()
            results['cluster'] = clusters

            return results

        except Exception as e:
            self.logger.error(f"Error clustering securities by factors: {str(e)}")
            return pd.DataFrame()

    def generate_factor_report(self, portfolio_analysis: PortfolioFactorAnalysis) -> str:
        """Generate comprehensive factor analysis report"""
        if not portfolio_analysis:
            return "No factor analysis available"

        report = f"""
Portfolio Factor Analysis Report
================================

Portfolio ID: {portfolio_analysis.portfolio_id}
Analysis Date: {portfolio_analysis.analysis_date.strftime('%Y-%m-%d')}
Model: {portfolio_analysis.factor_model.model_name}
Risk Explained: {portfolio_analysis.total_risk_explained:.1%}

Factor Exposures:
"""
        # Add factor exposures
        for exposure in portfolio_analysis.active_factor_exposures:
            report += f"- {exposure.factor_name}: {exposure.exposure:.3f} "
            report += f"(t-stat: {exposure.t_statistic:.2f}, p-value: {exposure.p_value:.3f})\n"

        # Add factor attribution
        report += "\nFactor Risk Attribution:\n"
        for factor, attribution in portfolio_analysis.factor_attribution.items():
            report += f"- {factor}: {attribution:.1%}\n"

        # Add factor tilts
        report += "\nFactor Tilts:\n"
        for factor, tilt in portfolio_analysis.factor_tilt.items():
            report += f"- {factor}: {tilt.replace('_', ' ').title()}\n"

        # Add risk budget
        report += "\nFactor Risk Budget:\n"
        for factor, budget in portfolio_analysis.risk_budget.items():
            report += f"- {factor}: {budget:.1%}\n"

        return report

    def export_factor_analysis(self, portfolio_analysis: PortfolioFactorAnalysis, format: str = "json") -> str:
        """Export factor analysis results"""
        try:
            if format.lower() == "json":
                import json
                data = {
                    "portfolio_id": portfolio_analysis.portfolio_id,
                    "analysis_date": portfolio_analysis.analysis_date.isoformat(),
                    "model_name": portfolio_analysis.factor_model.model_name,
                    "total_risk_explained": portfolio_analysis.total_risk_explained,
                    "factor_exposures": [
                        {
                            "factor_name": exp.factor_name,
                            "exposure": exp.exposure,
                            "t_statistic": exp.t_statistic,
                            "p_value": exp.p_value,
                            "is_significant": exp.is_significant
                        }
                        for exp in portfolio_analysis.active_factor_exposures
                    ],
                    "factor_attribution": portfolio_analysis.factor_attribution,
                    "factor_tilts": portfolio_analysis.factor_tilt,
                    "risk_budget": portfolio_analysis.risk_budget
                }
                return json.dumps(data, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            self.logger.error(f"Error exporting factor analysis: {str(e)}")
            return ""