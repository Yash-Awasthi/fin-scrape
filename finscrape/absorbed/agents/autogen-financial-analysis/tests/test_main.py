"""
Test Main Application
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.main import AutoGenFinancialAnalysisSystem


class TestAutoGenFinancialAnalysisSystem:
    """测试主应用程序类"""

    @pytest.fixture
    def system(self):
        """创建测试系统实例"""
        return AutoGenFinancialAnalysisSystem()

    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器"""
        with patch('src.main.ConfigurationManager') as mock:
            config_manager = Mock()
            config_manager.get.return_value = {}
            mock.return_value = config_manager
            yield config_manager

    @pytest.mark.asyncio
    async def test_system_initialization(self, system, mock_config_manager):
        """测试系统初始化"""
        # 模拟各个组件
        with patch('src.main.LoggingSystem') as mock_logging, \
             patch('src.main.SystemMonitor') as mock_monitor, \
             patch('src.main.SecurityManager') as mock_security, \
             patch('src.main.ErrorHandler') as mock_error, \
             patch('src.main.PerformanceManager') as mock_perf, \
             patch('src.main.CacheManager') as mock_cache, \
             patch('src.main.EnterpriseDataCollector') as mock_data, \
             patch('src.main.AdvancedFinancialAnalyzer') as mock_financial, \
             patch('src.main.AdvancedRiskAnalyzer') as mock_risk, \
             patch('src.main.QuantitativeAnalyzer') as mock_quant, \
             patch('src.main.get_report_generator') as mock_report_gen, \
             patch('src.main.get_visualizer') as mock_viz, \
             patch('src.main.get_data_formatter') as mock_formatter, \
             patch('src.main.get_export_manager') as mock_export, \
             patch('src.main.FinancialAgentFactory') as mock_factory, \
             patch('src.main.AgentOrchestrator') as mock_orchestrator:

            # 设置模拟对象
            mock_monitor_instance = Mock()
            mock_monitor.return_value = mock_monitor_instance
            mock_monitor_instance.start_monitoring = Mock()

            mock_data_instance = AsyncMock()
            mock_data.return_value = mock_data_instance

            await system.initialize()

            # 验证初始化调用
            mock_monitor_instance.start_monitoring.assert_called_once()
            assert system.logger is not None
            assert system.system_monitor == mock_monitor_instance

    @pytest.mark.asyncio
    async def test_analyze_company(self, system):
        """测试公司分析功能"""
        # 模拟依赖
        system.data_collector = AsyncMock()
        system.financial_analyzer = Mock()
        system.risk_analyzer = Mock()
        system.quant_analyzer = Mock()
        system.export_manager = AsyncMock()
        system.logger = Mock()

        # 模拟返回数据
        mock_data = {
            'market_data': {'price_history': Mock()},
            'data_quality': {'completeness': 0.9}
        }
        system.data_collector.collect_comprehensive_data.return_value = mock_data

        mock_financial_metrics = Mock()
        mock_financial_metrics.to_dict.return_value = {'roe': 15.0}
        system.financial_analyzer.calculate_comprehensive_metrics.return_value = mock_financial_metrics

        mock_risk_metrics = Mock()
        mock_risk_metrics.to_dict.return_value = {'var_95': 0.05}
        system.risk_analyzer.calculate_comprehensive_risk_metrics.return_value = mock_risk_metrics

        # 执行分析
        result = await system.analyze_company('AAPL')

        # 验证调用
        system.data_collector.collect_comprehensive_data.assert_called_once_with('AAPL')
        system.financial_analyzer.calculate_comprehensive_metrics.assert_called_once()
        system.risk_analyzer.calculate_comprehensive_risk_metrics.assert_called_once()

        # 验证结果
        assert result['symbol'] == 'AAPL'
        assert 'financial_metrics' in result
        assert 'risk_metrics' in result

    @pytest.mark.asyncio
    async def test_analyze_portfolio(self, system):
        """测试投资组合分析功能"""
        system.data_collector = AsyncMock()
        system.financial_analyzer = Mock()
        system.risk_analyzer = Mock()
        system.quant_analyzer = Mock()
        system.logger = Mock()

        # 模拟单个公司分析
        with patch.object(system, 'analyze_company', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                'symbol': 'AAPL',
                'financial_metrics': {'roe': 15.0},
                'risk_metrics': {'var_95': 0.05}
            }

            # 执行投资组合分析
            result = await system.analyze_portfolio(['AAPL', 'MSFT'])

            # 验证调用
            assert mock_analyze.call_count == 2
            assert 'portfolio_symbols' in result
            assert 'individual_analyses' in result

    def test_generate_summary(self, system):
        """测试摘要生成功能"""
        financial_metrics = {'roe': 20.0, 'roa': 10.0, 'debt_ratio': 50.0}
        risk_metrics = {'volatility': 25.0}

        summary = system._generate_summary(financial_metrics, risk_metrics)

        assert 'score' in summary
        assert 'rating' in summary
        assert 'overview' in summary

    def test_generate_recommendations(self, system):
        """测试建议生成功能"""
        financial_metrics = {'roe': 25.0, 'debt_ratio': 30.0}
        risk_metrics = {'volatility': 20.0}

        recommendations = system._generate_recommendations(financial_metrics, risk_metrics)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_cleanup(self, system):
        """测试资源清理功能"""
        system.system_monitor = Mock()
        system.cache_manager = AsyncMock()
        system.logger = Mock()

        await system.cleanup()

        system.system_monitor.stop_monitoring.assert_called_once()
        system.cache_manager.close.assert_called_once()

    def test_get_rating(self, system):
        """测试评级功能"""
        assert system._get_rating(85) == "优秀"
        assert system._get_rating(65) == "良好"
        assert system._get_rating(45) == "一般"
        assert system._get_rating(25) == "较差"