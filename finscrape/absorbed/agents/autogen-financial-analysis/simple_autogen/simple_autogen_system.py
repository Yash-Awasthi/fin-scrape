"""
简约版AutoGen系统核心实现
专注于突出AutoGen框架的智能体协作功能
"""

import autogen
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 基础数据模型
@dataclass
class BasicFinancialMetrics:
    """基础财务指标"""
    roe: float = 0.0  # 净资产收益率
    roa: float = 0.0  # 总资产收益率
    debt_ratio: float = 0.0  # 资产负债率
    gross_margin: float = 0.0  # 毛利率
    net_margin: float = 0.0  # 净利率
    current_ratio: float = 0.0  # 流动比率

    def to_dict(self) -> Dict:
        return {
            'roe': self.roe,
            'roa': self.roa,
            'debt_ratio': self.debt_ratio,
            'gross_margin': self.gross_margin,
            'net_margin': self.net_margin,
            'current_ratio': self.current_ratio
        }

@dataclass
class BasicRiskMetrics:
    """基础风险指标"""
    volatility: float = 0.0  # 波动率
    var_95: float = 0.0  # 95% VaR
    max_drawdown: float = 0.0  # 最大回撤

    def to_dict(self) -> Dict:
        return {
            'volatility': self.volatility,
            'var_95': self.var_95,
            'max_drawdown': self.max_drawdown
        }

# 简化的数据收集器
class SimpleDataCollector:
    """简化的数据收集器, 仅使用Yahoo Finance"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def collect_stock_data(self, symbol: str, period: str = "1y") -> Dict:
        """收集股票数据"""
        try:
            self.logger.info(f"开始收集 {symbol} 的数据...")
            stock = yf.Ticker(symbol)

            # 获取历史价格数据
            hist = stock.history(period=period)

            # 获取财务报表
            financials = stock.financials
            balance_sheet = stock.balance_sheet

            # 获取公司基本信息
            info = stock.info

            self.logger.info(f"成功收集 {symbol} 的数据")
            return {
                'symbol': symbol,
                'price_data': hist,
                'financials': financials,
                'balance_sheet': balance_sheet,
                'info': info,
                'collection_time': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"数据收集失败 {symbol}: {str(e)}")
            return {}

# 简化的财务分析器
class SimpleFinancialAnalyzer:
    """简化的财务分析器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_basic_metrics(self, data: Dict) -> BasicFinancialMetrics:
        """计算基础财务指标"""
        metrics = BasicFinancialMetrics()
        try:
            financials = data.get('financials', pd.DataFrame())
            balance_sheet = data.get('balance_sheet', pd.DataFrame())

            if not financials.empty and not balance_sheet.empty:
                # 确保我们使用最新的数据
                latest_year = financials.columns[0] if not financials.columns.empty else None
                latest_year_bs = balance_sheet.columns[0] if not balance_sheet.columns.empty else None

                if latest_year and latest_year_bs:
                    # 净利润
                    net_income = financials.loc['Net Income'].get(latest_year, 0)
                    # 总收入
                    total_revenue = financials.loc['Total Revenue'].get(latest_year, 0)
                    # 毛利
                    gross_profit = financials.loc['Gross Profit'].get(latest_year, 0)
                    # 总资产
                    total_assets = balance_sheet.loc['Total Assets'].get(latest_year_bs, 0)
                    # 总负债
                    total_liabilities = balance_sheet.loc['Total Liabilities'].get(latest_year_bs, 0)
                    # 净资产
                    shareholders_equity = balance_sheet.loc['Total Stockholder Equity'].get(latest_year_bs, 0)
                    # 流动资产
                    current_assets = balance_sheet.loc['Current Assets'].get(latest_year_bs, 0)
                    # 流动负债
                    current_liabilities = balance_sheet.loc['Current Liabilities'].get(latest_year_bs, 0)

                    # 计算比率
                    if shareholders_equity != 0:
                        metrics.roe = (net_income / shareholders_equity * 100) if net_income != 0 else 0
                    if total_assets != 0:
                        metrics.roa = (net_income / total_assets * 100) if net_income != 0 else 0
                    if total_assets != 0:
                        metrics.debt_ratio = (total_liabilities / total_assets * 100) if total_liabilities != 0 else 0
                    if total_revenue != 0:
                        metrics.gross_margin = (gross_profit / total_revenue * 100) if gross_profit != 0 else 0
                        metrics.net_margin = (net_income / total_revenue * 100) if net_income != 0 else 0
                    if current_liabilities != 0:
                        metrics.current_ratio = current_assets / current_liabilities if current_assets != 0 else 0

        except Exception as e:
            self.logger.error(f"财务指标计算失败: {str(e)}")

        return metrics

# 简化的风险分析器
class SimpleRiskAnalyzer:
    """简化的风险分析器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_risk_metrics(self, data: Dict) -> BasicRiskMetrics:
        """计算基础风险指标"""
        risk_metrics = BasicRiskMetrics()
        try:
            price_data = data.get('price_data', pd.DataFrame())
            if not price_data.empty:
                # 计算日收益率
                returns = price_data['Close'].pct_change().dropna()
                
                if len(returns) > 0:
                    # 计算波动率（年化）
                    risk_metrics.volatility = returns.std() * np.sqrt(252)
                    
                    # 计算95% VaR
                    risk_metrics.var_95 = np.percentile(returns, 5)
                    
                    # 计算最大回撤
                    cumulative = (1 + returns).cumprod()
                    rolling_max = cumulative.cummax()
                    drawdown = (cumulative / rolling_max) - 1
                    risk_metrics.max_drawdown = drawdown.min()

        except Exception as e:
            self.logger.error(f"风险指标计算失败: {str(e)}")

        return risk_metrics

# 智能体工厂类 - 专注于创建专业角色的智能体
class AutoGenAgentFactory:
    """AutoGen智能体工厂"""
    
    def __init__(self, llm_config: Dict):
        self.llm_config = llm_config
    
    def create_data_analyst_agent(self) -> autogen.AssistantAgent:
        """创建数据分析师智能体"""
        return autogen.AssistantAgent(
            name="data_analyst",
            system_message="""
你是一位专业的数据分析师, 擅长:
1. 分析和解读金融数据
2. 提取关键财务指标和市场信号
3. 识别数据中的趋势和异常
4. 为后续分析提供数据洞察

请基于提供的数据, 提取关键信息并准备分析素材.
""",
            llm_config=self.llm_config
        )
    
    def create_financial_analyst_agent(self) -> autogen.AssistantAgent:
        """创建财务分析师智能体"""
        return autogen.AssistantAgent(
            name="financial_analyst",
            system_message="""
你是一位资深的财务分析师, 具备以下专业能力:
1. 深度财务分析(盈利能力, 偿债能力, 运营能力, 成长能力)
2. 财务比率解读和行业对比
3. 识别财务健康状况和潜在风险
4. 提供专业的财务评估意见

请基于数据分析师提供的信息, 进行深入的财务分析.
""",
            llm_config=self.llm_config
        )
    
    def create_risk_analyst_agent(self) -> autogen.AssistantAgent:
        """创建风险分析师智能体"""
        return autogen.AssistantAgent(
            name="risk_analyst",
            system_message="""
你是一位专业的风险分析师, 专注于:
1. 评估投资风险和回报
2. 解读风险指标(波动率, VaR, 最大回撤等)
3. 分析潜在风险因素和影响
4. 提供风险缓解建议

请基于数据分析师提供的信息, 进行全面的风险评估.
""",
            llm_config=self.llm_config
        )
    
    def create_investment_advisor_agent(self) -> autogen.AssistantAgent:
        """创建投资顾问智能体"""
        return autogen.AssistantAgent(
            name="investment_advisor",
            system_message="""
你是一位经验丰富的投资顾问, 擅长:
1. 综合财务分析和风险评估结果
2. 提供投资建议和决策支持
3. 评估投资价值和潜在回报
4. 给出明确的投资评级和目标价格

请基于财务分析师和风险分析师的分析结果, 提供综合的投资建议.
""",
            llm_config=self.llm_config
        )
    
    def create_user_proxy_agent(self) -> autogen.UserProxyAgent:
        """创建用户代理智能体"""
        return autogen.UserProxyAgent(
            name="user_proxy",
            system_message="用户代理，负责协调和管理智能体团队完成投资分析任务",
            code_execution_config=False,
            human_input_mode="NEVER"
        )

# 智能体编排器 - 负责组织智能体协作流程
class AgentOrchestrator:
    """智能体编排器"""
    
    def __init__(self, agents: Dict[str, autogen.Agent]):
        self.agents = agents
        self.conversation_history = {}
    
    def orchestrate_analysis(self, symbol: str, analysis_data: Dict) -> Dict:
        """编排智能体协作分析流程"""
        user_proxy = self.agents['user_proxy']
        data_analyst = self.agents['data_analyst']
        financial_analyst = self.agents['financial_analyst']
        risk_analyst = self.agents['risk_analyst']
        investment_advisor = self.agents['investment_advisor']
        
        # 1. 数据分析师首先分析原始数据
        user_proxy.initiate_chat(
            data_analyst,
            message=f"请分析{symbol}的财务数据，提取关键信息：\n" +
                   f"公司名称: {analysis_data['company_name']}\n" +
                   f"财务指标: {analysis_data['financial_metrics']}\n" +
                   f"风险指标: {analysis_data['risk_metrics']}\n" +
                   f"行业: {analysis_data.get('sector', '未知')}"
        )
        
        # 保存对话历史
        self.conversation_history['data_analysis'] = user_proxy.chat_messages[data_analyst]
        
        # 2. 财务分析师基于数据分析师的发现进行深入财务分析
        user_proxy.initiate_chat(
            financial_analyst,
            message=f"基于数据分析师的发现，请对{symbol}进行深入的财务分析：\n" +
                   f"{data_analyst.last_message()['content']}"
        )
        
        self.conversation_history['financial_analysis'] = user_proxy.chat_messages[financial_analyst]
        
        # 3. 风险分析师基于数据分析师的发现进行风险评估
        user_proxy.initiate_chat(
            risk_analyst,
            message=f"基于数据分析师的发现，请对{symbol}进行全面的风险评估：\n" +
                   f"{data_analyst.last_message()['content']}"
        )
        
        self.conversation_history['risk_analysis'] = user_proxy.chat_messages[risk_analyst]
        
        # 4. 投资顾问整合所有分析结果，提供综合建议
        user_proxy.initiate_chat(
            investment_advisor,
            message=f"请整合以下分析结果，为{symbol}提供综合的投资建议：\n" +
                   f"1. 财务分析：{financial_analyst.last_message()['content']}\n" +
                   f"2. 风险评估：{risk_analyst.last_message()['content']}\n" +
                   f"3. 公司基本信息：{analysis_data['company_name']}，{analysis_data.get('sector', '未知')}行业"
        )
        
        self.conversation_history['investment_advice'] = user_proxy.chat_messages[investment_advisor]
        
        # 返回完整的分析结果
        return {
            'data_analysis': data_analyst.last_message()['content'],
            'financial_analysis': financial_analyst.last_message()['content'],
            'risk_analysis': risk_analyst.last_message()['content'],
            'investment_advice': investment_advisor.last_message()['content'],
            'conversation_history': self.conversation_history
        }

# 简约版AutoGen系统
class SimpleAutoGenSystem:
    """简约版AutoGen系统 - 突出智能体协作的核心优势"""

    def __init__(self, openai_api_key: str):
        """初始化系统"""
        self.openai_api_key = openai_api_key
        self.data_collector = SimpleDataCollector()
        self.financial_analyzer = SimpleFinancialAnalyzer()
        self.risk_analyzer = SimpleRiskAnalyzer()
        
        # 配置基础LLM设置
        self.llm_config = {
            "config_list": [
                {
                    "model": "gpt-3.5-turbo",
                    "api_key": self.openai_api_key
                }
            ],
            "temperature": 0.1
        }

    def create_agents(self) -> Dict[str, autogen.Agent]:
        """使用智能体工厂创建AutoGen智能体团队"""
        factory = AutoGenAgentFactory(self.llm_config)
        
        return {
            'user_proxy': factory.create_user_proxy_agent(),
            'data_analyst': factory.create_data_analyst_agent(),
            'financial_analyst': factory.create_financial_analyst_agent(),
            'risk_analyst': factory.create_risk_analyst_agent(),
            'investment_advisor': factory.create_investment_advisor_agent()
        }

    def analyze_stock(self, symbol: str) -> Dict:
        """分析指定股票 - 通过智能体协作完成"""
        logger.info(f"开始分析股票 {symbol} - 启动AutoGen智能体协作")

        # 1. 收集数据
        data = self.data_collector.collect_stock_data(symbol)
        if not data:
            return {"error": "无法收集数据", "symbol": symbol}

        # 2. 计算财务和风险指标
        financial_metrics = self.financial_analyzer.calculate_basic_metrics(data)
        risk_metrics = self.risk_analyzer.calculate_risk_metrics(data)

        # 3. 创建智能体团队
        agents = self.create_agents()
        
        # 4. 准备分析数据
        analysis_data = {
            'symbol': symbol,
            'company_name': data.get('info', {}).get('longName', symbol),
            'financial_metrics': financial_metrics.to_dict(),
            'risk_metrics': risk_metrics.to_dict(),
            'sector': data.get('info', {}).get('sector', ''),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 5. 使用智能体编排器启动多智能体协作分析流程
        orchestrator = AgentOrchestrator(agents)
        collaboration_results = orchestrator.orchestrate_analysis(symbol, analysis_data)

        # 6. 整理综合结果
        result = {
            'symbol': symbol,
            'company_name': analysis_data['company_name'],
            'financial_metrics': analysis_data['financial_metrics'],
            'risk_metrics': analysis_data['risk_metrics'],
            'data_analysis': collaboration_results['data_analysis'],
            'financial_analysis': collaboration_results['financial_analysis'],
            'risk_analysis': collaboration_results['risk_analysis'],
            'investment_advice': collaboration_results['investment_advice'],
            'analysis_date': analysis_data['analysis_date'],
            'autogen_collaboration_summary': "AutoGen多智能体协作分析完成：数据分析师、财务分析师、风险分析师和投资顾问共同协作完成了完整的股票分析流程"
        }

        logger.info(f"完成股票 {symbol} 的AutoGen智能体协作分析")
        return result