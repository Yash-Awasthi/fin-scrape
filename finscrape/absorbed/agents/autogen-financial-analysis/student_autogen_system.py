"""
学生级AutoGen金融分析系统
简化版，适合学习使用
"""

import autogen
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio
import logging
from datetime import datetime, timedelta

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
    """简化的数据收集器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def collect_stock_data(self, symbol: str, period: str = "2y") -> Dict:
        """收集股票数据"""
        try:
            stock = yf.Ticker(symbol)

            # 获取历史价格数据
            hist = stock.history(period=period)

            # 获取财务报表
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow

            return {
                'symbol': symbol,
                'price_data': hist,
                'financials': financials,
                'balance_sheet': balance_sheet,
                'cashflow': cashflow,
                'info': stock.info,
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
        try:
            financials = data.get('financials', pd.DataFrame())
            balance_sheet = data.get('balance_sheet', pd.DataFrame())

            if financials.empty or balance_sheet.empty:
                return BasicFinancialMetrics()

            # 获取最新年度数据
            latest_year = financials.columns[0] if len(financials.columns) > 0 else None
            if latest_year is None:
                return BasicFinancialMetrics()

            # 提取关键数据（使用安全的数据获取方法）
            def get_safe_value(df, key, year, default=0.0):
                try:
                    if key in df.index and year in df.columns:
                        value = df.loc[key, year]
                        return float(value) if pd.notna(value) else default
                    return default
                except:
                    return default

            revenue = get_safe_value(financials, 'Total Revenue', latest_year)
            net_income = get_safe_value(financials, 'Net Income', latest_year)
            gross_profit = get_safe_value(financials, 'Gross Profit', latest_year)

            total_assets = get_safe_value(balance_sheet, 'Total Assets', latest_year)
            total_equity = get_safe_value(balance_sheet, 'Total Stockholder Equity', latest_year)
            total_debt = get_safe_value(balance_sheet, 'Total Debt', latest_year)
            current_assets = get_safe_value(balance_sheet, 'Total Current Assets', latest_year)
            current_liabilities = get_safe_value(balance_sheet, 'Total Current Liabilities', latest_year)

            # 计算财务比率
            roe = (net_income / total_equity * 100) if total_equity != 0 else 0
            roa = (net_income / total_assets * 100) if total_assets != 0 else 0
            debt_ratio = (total_debt / total_assets * 100) if total_assets != 0 else 0
            gross_margin = (gross_profit / revenue * 100) if revenue != 0 else 0
            net_margin = (net_income / revenue * 100) if revenue != 0 else 0
            current_ratio = current_assets / current_liabilities if current_liabilities != 0 else 0

            return BasicFinancialMetrics(
                roe=roe, roa=roa, debt_ratio=debt_ratio,
                gross_margin=gross_margin, net_margin=net_margin,
                current_ratio=current_ratio
            )

        except Exception as e:
            self.logger.error(f"财务指标计算失败: {str(e)}")
            return BasicFinancialMetrics()

# 简化的风险分析器
class SimpleRiskAnalyzer:
    """简化的风险分析器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_basic_risk(self, data: Dict) -> BasicRiskMetrics:
        """计算基础风险指标"""
        try:
            price_data = data.get('price_data', pd.DataFrame())

            if price_data.empty:
                return BasicRiskMetrics()

            # 计算收益率
            returns = price_data['Close'].pct_change().dropna()

            if len(returns) == 0:
                return BasicRiskMetrics()

            # 计算波动率（年化）
            volatility = returns.std() * np.sqrt(252)

            # 计算VaR（95%置信度）
            var_95 = np.percentile(returns, 5)

            # 计算最大回撤
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            return BasicRiskMetrics(
                volatility=volatility,
                var_95=abs(var_95),
                max_drawdown=abs(max_drawdown)
            )

        except Exception as e:
            self.logger.error(f"风险指标计算失败: {str(e)}")
            return BasicRiskMetrics()

# 简化的AutoGen智能体配置
class SimpleAutoGenConfig:
    """简化的AutoGen配置"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_config = {
            "config_list": [{
                "model": "gpt-3.5-turbo",
                "api_key": api_key
            }],
            "temperature": 0.1,
            "max_tokens": 2000
        }

    def create_agents(self) -> Dict[str, autogen.AssistantAgent]:
        """创建简化的智能体"""
        agents = {}

        # 数据收集智能体
        agents['data_collector'] = autogen.AssistantAgent(
            name="data_collector",
            system_message="""你是一个数据收集助手，擅长：
1. 使用yfinance收集股票数据
2. 获取历史价格和财务报表
3. 整理和验证数据完整性

请确保数据的准确性和完整性。""",
            llm_config=self.base_config,
            max_consecutive_auto_reply=5
        )

        # 财务分析智能体
        agents['financial_analyst'] = autogen.AssistantAgent(
            name="financial_analyst",
            system_message="""你是一个财务分析助手，专注于：
1. 计算基础财务比率（ROE、ROA、负债率等）
2. 分析公司的盈利能力和偿债能力
3. 识别财务优势和风险点

请使用简单易懂的语言进行分析。""",
            llm_config=self.base_config,
            max_consecutive_auto_reply=8
        )

        # 报告生成智能体
        agents['report_generator'] = autogen.AssistantAgent(
            name="report_generator",
            system_message="""你是一个报告生成助手，负责：
1. 整理分析结果
2. 生成简洁的投资建议
3. 提供风险提示

请生成清晰、简洁的分析报告。""",
            llm_config=self.base_config,
            max_consecutive_auto_reply=5
        )

        return agents

# 简化的报告生成器
class SimpleReportGenerator:
    """简化的报告生成器"""

    def generate_report(self, symbol: str, financial_metrics: BasicFinancialMetrics,
                       risk_metrics: BasicRiskMetrics, company_info: Dict) -> str:
        """生成分析报告"""

        company_name = company_info.get('shortName', symbol)
        sector = company_info.get('sector', '未知')

        report = f"""
# {company_name} ({symbol}) 简易分析报告

## 公司基本信息
- **行业**: {sector}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 财务指标分析
- **净资产收益率 (ROE)**: {financial_metrics.roe:.2f}%
- **总资产收益率 (ROA)**: {financial_metrics.roa:.2f}%
- **资产负债率**: {financial_metrics.debt_ratio:.2f}%
- **毛利率**: {financial_metrics.gross_margin:.2f}%
- **净利率**: {financial_metrics.net_margin:.2f}%
- **流动比率**: {financial_metrics.current_ratio:.2f}

## 风险指标分析
- **年化波动率**: {risk_metrics.volatility:.2f}%
- **95% VaR**: {risk_metrics.var_95:.2f}%
- **最大回撤**: {risk_metrics.max_drawdown:.2f}%

## 简要评价
{self._generate_evaluation(financial_metrics, risk_metrics)}

## 投资建议
{self._generate_recommendation(financial_metrics, risk_metrics)}

---
*注：此报告为简化版分析，仅供参考学习使用*
"""
        return report

    def _generate_evaluation(self, financial: BasicFinancialMetrics, risk: BasicRiskMetrics) -> str:
        """生成简要评价"""
        evaluations = []

        # 盈利能力评价
        if financial.roe > 15:
            evaluations.append("公司盈利能力优秀")
        elif financial.roe > 10:
            evaluations.append("公司盈利能力良好")
        else:
            evaluations.append("公司盈利能力有待提升")

        # 偿债能力评价
        if financial.debt_ratio < 30:
            evaluations.append("财务杠杆较低，偿债能力强")
        elif financial.debt_ratio < 60:
            evaluations.append("财务杠杆适中")
        else:
            evaluations.append("财务杠杆较高，需关注偿债风险")

        # 风险评价
        if risk.volatility < 20:
            evaluations.append("价格波动相对较小")
        elif risk.volatility < 35:
            evaluations.append("价格波动适中")
        else:
            evaluations.append("价格波动较大，风险较高")

        return "；".join(evaluations) + "。"

    def _generate_recommendation(self, financial: BasicFinancialMetrics, risk: BasicRiskMetrics) -> str:
        """生成投资建议"""
        score = 0

        # 盈利能力评分
        if financial.roe > 15:
            score += 2
        elif financial.roe > 10:
            score += 1

        # 财务健康评分
        if financial.debt_ratio < 30:
            score += 2
        elif financial.debt_ratio < 60:
            score += 1

        # 风险评分
        if risk.volatility < 20:
            score += 2
        elif risk.volatility < 35:
            score += 1

        if score >= 5:
            return "基本面良好，可考虑关注"
        elif score >= 3:
            return "基本面一般，建议谨慎观察"
        else:
            return "基本面较弱，建议回避"

# 主分析系统
class StudentAutoGenSystem:
    """学生级AutoGen金融分析系统"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.config = SimpleAutoGenConfig(api_key)
        self.agents = self.config.create_agents()

        self.data_collector = SimpleDataCollector()
        self.financial_analyzer = SimpleFinancialAnalyzer()
        self.risk_analyzer = SimpleRiskAnalyzer()
        self.report_generator = SimpleReportGenerator()

        # 创建用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False
        )

        self.logger = logging.getLogger(__name__)

    def analyze_stock(self, symbol: str) -> Dict:
        """分析股票"""
        try:
            logger.info(f"开始分析 {symbol}")

            # 1. 数据收集
            data = self.data_collector.collect_stock_data(symbol)
            if not data:
                return {"status": "error", "message": "数据收集失败"}

            # 2. 财务分析
            financial_metrics = self.financial_analyzer.calculate_basic_metrics(data)

            # 3. 风险分析
            risk_metrics = self.risk_analyzer.calculate_basic_risk(data)

            # 4. 生成报告
            company_info = data.get('info', {})
            report = self.report_generator.generate_report(
                symbol, financial_metrics, risk_metrics, company_info
            )

            # 5. 使用AutoGen进行智能分析
            ai_analysis = self._get_ai_analysis(symbol, financial_metrics, risk_metrics)

            return {
                "status": "success",
                "symbol": symbol,
                "financial_metrics": financial_metrics.to_dict(),
                "risk_metrics": risk_metrics.to_dict(),
                "report": report,
                "ai_analysis": ai_analysis,
                "analysis_time": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"分析失败 {symbol}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_ai_analysis(self, symbol: str, financial: BasicFinancialMetrics, risk: BasicRiskMetrics) -> str:
        """获取AI智能体分析"""
        try:
            # 创建分析任务
            analysis_prompt = f"""
            请对股票 {symbol} 进行简单分析：

            财务指标：
            - ROE: {financial.roe:.2f}%
            - ROA: {financial.roa:.2f}%
            - 资产负债率: {financial.debt_ratio:.2f}%
            - 毛利率: {financial.gross_margin:.2f}%

            风险指标：
            - 波动率: {risk.volatility:.2f}%
            - VaR: {risk.var_95:.2f}%
            - 最大回撤: {risk.max_drawdown:.2f}%

            请提供简单的投资建议和风险提示。
            """

            # 让财务分析智能体进行分析
            self.user_proxy.initiate_chat(
                self.agents['financial_analyst'],
                message=analysis_prompt
            )

            # 获取对话结果
            chat_history = self.user_proxy.chat_messages[self.agents['financial_analyst']]
            if chat_history:
                return chat_history[-1]['content']

            return "AI分析暂不可用"

        except Exception as e:
            self.logger.error(f"AI分析失败: {str(e)}")
            return "AI分析失败"

# 使用示例
def main():
    """主函数示例"""
    # API密钥配置
    api_key = "your-openai-api-key"  # 请替换为您的API密钥

    # 创建分析系统
    system = StudentAutoGenSystem(api_key)

    # 分析示例股票
    symbol = "AAPL"  # 苹果公司
    result = system.analyze_stock(symbol)

    if result["status"] == "success":
        print("分析完成！")
        print("=" * 50)
        print(result["report"])
        print("=" * 50)
        print("AI分析结果:")
        print(result["ai_analysis"])
    else:
        print(f"分析失败: {result['message']}")

if __name__ == "__main__":
    main()