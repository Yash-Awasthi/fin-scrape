"""
Test Data Collection and Processing Modules
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta


class TestDataCollector:
    """测试数据收集器"""

    @pytest.fixture
    def mock_api_keys(self):
        """模拟API密钥"""
        return {
            "yahoo_finance": "test_key",
            "alpha_vantage": "test_key"
        }

    @pytest.fixture
    def mock_cache_manager(self):
        """模拟缓存管理器"""
        with patch('src.data.data_collector.CacheManager') as mock:
            cache_manager = AsyncMock()
            cache_manager.get_cached_data.return_value = None
            cache_manager.set_cached_data = AsyncMock()
            mock.return_value = cache_manager
            yield cache_manager

    @pytest.mark.asyncio
    async def test_collect_comprehensive_data(self, mock_api_keys, mock_cache_manager):
        """测试综合数据收集"""
        from src.data.data_collector import EnterpriseDataCollector

        # 模拟数据源
        with patch('src.data.data_collector.YahooFinanceSource') as mock_yahoo, \
             patch('src.data.data_collector.AlphaVantageSource') as mock_alpha:

            mock_yahoo_instance = AsyncMock()
            mock_yahoo.return_value = mock_yahoo_instance
            mock_yahoo_instance.fetch_data.return_value = {
                'financial_statements': {},
                'market_data': {},
                'source': 'yahoo_finance'
            }

            mock_alpha_instance = AsyncMock()
            mock_alpha.return_value = mock_alpha_instance
            mock_alpha_instance.fetch_data.return_value = {
                'financial_statements': {},
                'source': 'alpha_vantage'
            }

            collector = EnterpriseDataCollector(mock_api_keys, "redis://localhost:6379")

            result = await collector.collect_comprehensive_data("AAPL")

            # 验证结果
            assert 'financial_statements' in result
            assert 'market_data' in result
            assert 'data_quality' in result
            assert 'sources' in result
            assert len(result['sources']) > 0

    @pytest.mark.asyncio
    async def test_collect_with_cache(self, mock_api_keys, mock_cache_manager):
        """测试带缓存的数据收集"""
        from src.data.data_collector import EnterpriseDataCollector

        # 模拟缓存命中
        cached_data = {
            'financial_statements': {'test': 'data'},
            'market_data': {'test': 'market'},
            'data_quality': {'completeness': 0.9},
            'sources': ['cache']
        }
        mock_cache_manager.get_cached_data.return_value = cached_data

        collector = EnterpriseDataCollector(mock_api_keys, "redis://localhost:6379")

        result = await collector.collect_comprehensive_data("AAPL", use_cache=True)

        # 验证缓存数据被返回
        assert result == cached_data
        mock_cache_manager.get_cached_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_merge_and_validate_data(self):
        """测试数据合并和验证"""
        from src.data.data_collector import EnterpriseDataCollector

        collector = EnterpriseDataCollector({}, "redis://localhost:6379")

        # 模拟多个数据源的结果
        results = [
            {
                'financial_statements': {'income': 'data1'},
                'market_data': {'price': 'data1'},
                'source': 'yahoo_finance'
            },
            {
                'financial_statements': {'balance': 'data2'},
                'market_data': {'volume': 'data2'},
                'source': 'alpha_vantage'
            },
            Exception("测试错误")
        ]

        merged_data = collector._merge_and_validate_data(results)

        # 验证合并结果
        assert 'income' in merged_data['financial_statements']
        assert 'balance' in merged_data['financial_statements']
        assert 'price' in merged_data['market_data']
        assert 'volume' in merged_data['market_data']
        assert len(merged_data['sources']) == 2

    def test_calculate_data_quality(self):
        """测试数据质量计算"""
        from src.data.data_collector import EnterpriseDataCollector

        collector = EnterpriseDataCollector({}, "redis://localhost:6379")

        # 测试完整数据
        complete_data = {
            'financial_statements': {},
            'market_data': {},
            'sources': ['yahoo_finance', 'alpha_vantage']
        }

        quality = collector._calculate_data_quality(complete_data)

        assert 'completeness' in quality
        assert 'accuracy' in quality
        assert 'consistency' in quality
        assert 'overall_score' in quality
        assert quality['completeness'] == 1.0
        assert quality['accuracy'] == 1.0


class TestFinancialAnalyzer:
    """测试财务分析器"""

    @pytest.fixture
    def analyzer(self):
        """创建财务分析器实例"""
        from src.analysis.financial_analyzer import AdvancedFinancialAnalyzer
        return AdvancedFinancialAnalyzer()

    def test_calculate_comprehensive_metrics(self, analyzer):
        """测试综合财务指标计算"""
        # 模拟财务数据
        financial_data = {
            'financial_statements': {
                'income_statement': pd.DataFrame({
                    '2023': [1000, 200, 150, 50],
                    '2022': [900, 180, 135, 45]
                }, index=['Total Revenue', 'Net Income', 'Gross Profit', 'EBIT'])
            },
            'balance_sheet': pd.DataFrame({
                '2023': [5000, 2000, 1000, 500, 800],
                '2022': [4500, 1800, 900, 450, 700]
            }, index=['Total Assets', 'Total Stockholder Equity', 'Total Debt', 'Total Current Assets', 'Total Current Liabilities'])
            },
            'cash_flow': pd.DataFrame({
                '2023': [300, 100, 50],
                '2022': [250, 80, 40]
            }, index=['Operating Cash Flow', 'Investing Cash Flow', 'Capital Expenditure'])
        }

        metrics = analyzer.calculate_comprehensive_metrics(financial_data)

        # 验证指标计算
        assert hasattr(metrics, 'roe')
        assert hasattr(metrics, 'roa')
        assert hasattr(metrics, 'debt_ratio')
        assert hasattr(metrics, 'gross_margin')
        assert hasattr(metrics, 'net_margin')

        # 验证计算结果合理性
        assert 0 <= metrics.roe <= 100
        assert 0 <= metrics.roa <= 100
        assert 0 <= metrics.debt_ratio <= 100

    def test_perform_dupont_analysis(self, analyzer):
        """测试杜邦分析"""
        # 模拟财务数据
        financial_data = {
            'financial_statements': {
                'income_statement': pd.DataFrame({
                    '2023': [1000, 200]
                }, index=['Total Revenue', 'Net Income'])
            },
            'balance_sheet': pd.DataFrame({
                '2023': [5000, 2000]
            }, index=['Total Assets', 'Total Stockholder Equity'])
            }
        }

        dupont_result = analyzer.perform_dupont_analysis(financial_data)

        # 验证杜邦分析结果
        assert 'roe' in dupont_result
        assert 'net_profit_margin' in dupont_result
        assert 'asset_turnover' in dupont_result
        assert 'equity_multiplier' in dupont_result
        assert 'decomposition' in dupont_result

        # 验证杜邦恒等式
        roe = dupont_result['roe']
        npm = dupont_result['net_profit_margin']
        at = dupont_result['asset_turnover']
        em = dupont_result['equity_multiplier']

        assert abs(roe - (npm * at * em)) < 0.01  # 允许小的浮点误差


class TestRiskAnalyzer:
    """测试风险分析器"""

    @pytest.fixture
    def analyzer(self):
        """创建风险分析器实例"""
        from src.risk.risk_analyzer import AdvancedRiskAnalyzer
        return AdvancedRiskAnalyzer()

    def test_calculate_var(self, analyzer):
        """测试VaR计算"""
        # 模拟收益率数据
        returns = pd.Series(np.random.normal(0, 0.02, 1000))

        var_95 = analyzer.calculate_var(returns, 0.95)
        var_99 = analyzer.calculate_var(returns, 0.99)

        # 验证VaR计算
        assert var_95 > 0
        assert var_99 > 0
        assert var_99 > var_95  # 99% VaR应该大于95% VaR

    def test_calculate_expected_shortfall(self, analyzer):
        """测试期望损失计算"""
        # 模拟收益率数据
        returns = pd.Series(np.random.normal(0, 0.02, 1000))

        es = analyzer.calculate_expected_shortfall(returns, 0.95)

        # 验证期望损失计算
        assert es > 0

    def test_calculate_comprehensive_risk_metrics(self, analyzer):
        """测试综合风险指标计算"""
        # 模拟价格数据
        dates = pd.date_range('2023-01-01', periods=252)
        prices = pd.Series(np.random.lognormal(0, 0.02, 252), index=dates)

        market_data = pd.DataFrame({'Close': prices})

        risk_metrics = analyzer.calculate_comprehensive_risk_metrics(market_data)

        # 验证风险指标
        assert hasattr(risk_metrics, 'var_95')
        assert hasattr(risk_metrics, 'var_99')
        assert hasattr(risk_metrics, 'expected_shortfall')
        assert hasattr(risk_metrics, 'volatility')
        assert hasattr(risk_metrics, 'sharpe_ratio')
        assert hasattr(risk_metrics, 'max_drawdown')

        # 验证指标合理性
        assert risk_metrics.var_95 > 0
        assert risk_metrics.var_99 > 0
        assert risk_metrics.volatility > 0
        assert risk_metrics.max_drawdown <= 0  # 最大回撤应该是负数

    def test_perform_stress_testing(self, analyzer):
        """测试压力测试"""
        # 模拟价格数据
        dates = pd.date_range('2023-01-01', periods=100)
        prices = pd.Series(np.random.lognormal(0, 0.02, 100), index=dates)

        market_data = pd.DataFrame({'Close': prices})

        # 压力测试场景
        scenarios = [
            {"name": "market_crash", "shock_factor": 0.7},
            {"name": "recession", "shock_factor": 0.8},
            {"name": "interest_rate_hike", "shock_factor": 0.9}
        ]

        results = analyzer.perform_stress_testing(market_data, scenarios)

        # 验证压力测试结果
        assert len(results) == len(scenarios)
        for scenario_name in scenarios:
            assert scenario_name["name"] in results
            assert "var_95" in results[scenario_name["name"]]
            assert "volatility" in results[scenario_name["name"]]
            assert "shock_factor" in results[scenario_name["name"]]


class TestQuantAnalyzer:
    """测试量化分析器"""

    @pytest.fixture
    def analyzer(self):
        """创建量化分析器实例"""
        from src.quant.portfolio_optimizer import QuantitativeAnalyzer
        return QuantitativeAnalyzer()

    def test_build_factor_model(self, analyzer):
        """测试因子模型构建"""
        # 模拟股票数据
        dates = pd.date_range('2023-01-01', periods=100)
        stock_prices = pd.Series(np.random.lognormal(0, 0.02, 100), index=dates)

        stock_data = pd.DataFrame({'Close': stock_prices})

        # 模拟因子数据
        factor_data = {
            'market': pd.DataFrame({'returns': np.random.normal(0.01, 0.02, 100)}),
            'size': pd.DataFrame({'returns': np.random.normal(0.005, 0.015, 100)}),
            'value': pd.DataFrame({'returns': np.random.normal(0.008, 0.018, 100)})
        }

        with patch('sklearn.ensemble.RandomForestRegressor') as mock_model, \
             patch('sklearn.preprocessing.StandardScaler') as mock_scaler:

            mock_model_instance = Mock()
            mock_model_instance.fit.return_value = None
            mock_model_instance.score.return_value = 0.8
            mock_model_instance.feature_importances_ = np.array([0.5, 0.3, 0.2])
            mock_model.return_value = mock_model_instance

            mock_scaler_instance = Mock()
            mock_scaler_instance.fit_transform.return_value = np.random.random((100, 3))
            mock_scaler.return_value = mock_scaler_instance

            result = analyzer.build_factor_model(stock_data, factor_data)

            # 验证因子模型结果
            assert 'model' in result
            assert 'scaler' in result
            assert 'feature_importance' in result
            assert 'r_squared' in result
            assert 'factor_exposures' in result

    def test_optimize_portfolio(self, analyzer):
        """测试投资组合优化"""
        # 模拟收益率数据
        dates = pd.date_range('2023-01-01', periods=100)
        returns_data = pd.DataFrame({
            'AAPL': np.random.normal(0.001, 0.02, 100),
            'MSFT': np.random.normal(0.0015, 0.025, 100),
            'GOOG': np.random.normal(0.0008, 0.022, 100)
        }, index=dates)

        with patch('numpy.random.random') as mock_random:
            # 模拟随机权重生成
            mock_random.return_value = np.array([0.4, 0.35, 0.25])

            result = analyzer.optimize_portfolio(returns_data)

            # 验证优化结果
            assert 'optimal_weights' in result
            assert 'optimal_return' in result
            assert 'optimal_volatility' in result
            assert 'sharpe_ratio' in result
            assert 'efficient_frontier' in result

            # 验证权重和为1
            weights = result['optimal_weights']
            assert abs(sum(weights.values()) - 1.0) < 0.01


class TestDataValidator:
    """测试数据验证器"""

    @pytest.fixture
    def validator(self):
        """创建数据验证器实例"""
        from src.data.data_validator import DataValidator
        return DataValidator()

    def test_validate_financial_data(self, validator):
        """测试财务数据验证"""
        # 有效的财务数据
        valid_data = {
            'income_statement': pd.DataFrame({
                '2023': [1000, 200],
                '2022': [900, 180]
            }, index=['Revenue', 'Net Income']),
            'balance_sheet': pd.DataFrame({
                '2023': [5000, 2000],
                '2022': [4500, 1800]
            }, index=['Assets', 'Equity'])
        }

        validation_result = validator.validate_financial_data(valid_data)

        # 验证结果
        assert 'is_valid' in validation_result
        assert 'completeness_score' in validation_result
        assert 'consistency_score' in validation_result
        assert 'errors' in validation_result
        assert 'warnings' in validation_result

    def test_validate_market_data(self, validator):
        """测试市场数据验证"""
        # 有效的市场数据
        dates = pd.date_range('2023-01-01', periods=100)
        market_data = pd.DataFrame({
            'Open': np.random.uniform(100, 200, 100),
            'High': np.random.uniform(100, 200, 100),
            'Low': np.random.uniform(100, 200, 100),
            'Close': np.random.uniform(100, 200, 100),
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)

        validation_result = validator.validate_market_data(market_data)

        # 验证结果
        assert 'is_valid' in validation_result
        assert 'data_quality_score' in validation_result
        assert 'missing_data_points' in validation_result

    def test_validate_api_response(self, validator):
        """测试API响应验证"""
        # 有效的API响应
        valid_response = {
            'status': 'success',
            'data': {'price': 150.25, 'volume': 1000000},
            'timestamp': '2023-01-01T00:00:00Z'
        }

        validation_result = validator.validate_api_response(valid_response)

        # 验证结果
        assert 'is_valid' in validation_result
        assert 'response_time' in validation_result
        assert 'data_integrity' in validation_result


# 集成测试
class TestDataCollectionIntegration:
    """数据收集集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_data_collection(self):
        """端到端数据收集测试"""
        # 这个测试需要实际的数据源，在实际CI/CD中可能需要mock
        pass

    @pytest.mark.asyncio
    async def test_data_pipeline_with_caching(self):
        """带缓存的数据管道测试"""
        # 测试数据收集、缓存、验证的完整流程
        pass