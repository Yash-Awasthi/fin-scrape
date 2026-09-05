"""
Agent Factory
Factory pattern for creating specialized financial analysis agents
"""

import autogen
import logging
from typing import Dict, Optional, Any
from .agent_types import AgentRole, AgentConfig, AgentPerformance


class FinancialAgentFactory:
    """Factory for creating financial analysis agents"""

    def __init__(self, base_llm_config: Dict[str, Any]):
        self.base_llm_config = base_llm_config
        self.logger = logging.getLogger(__name__)
        self.agent_performance: Dict[str, AgentPerformance] = {}

    def create_agent(self, config: AgentConfig) -> autogen.AssistantAgent:
        """Create an agent from configuration"""
        try:
            agent = autogen.AssistantAgent(**config.to_dict())

            # Initialize performance tracking
            self.agent_performance[config.name] = AgentPerformance(
                agent_name=config.name,
                last_activity=self._get_current_timestamp()
            )

            self.logger.info(f"Created agent: {config.name} with role {config.role.value}")
            return agent

        except Exception as e:
            self.logger.error(f"Failed to create agent {config.name}: {str(e)}")
            raise

    def create_data_collector(self) -> autogen.AssistantAgent:
        """Create data collection agent"""
        config = AgentConfig(
            name="data_collector",
            role=AgentRole.DATA_COLLECTOR,
            system_message="""You are a professional data engineer specializing in financial data collection.

Your responsibilities include:
1. Multi-source data API integration (Yahoo Finance, Alpha Vantage, Quandl, Bloomberg)
2. Real-time data stream processing and validation
3. Data quality assessment and anomaly detection
4. Data format standardization and ETL pipeline management
5. Historical data retrieval and time series preparation

Always ensure:
- Data accuracy and completeness
- Proper handling of missing values and outliers
- Consistent data formats across different sources
- Compliance with data provider terms of service
- Efficient caching and retrieval strategies

Provide detailed data quality metrics and source reliability assessments.""",
            llm_config=self._get_optimized_config(temperature=0.1),
            max_consecutive_auto_reply=15
        )
        return self.create_agent(config)

    def create_financial_analyst(self) -> autogen.AssistantAgent:
        """Create financial analysis agent"""
        config = AgentConfig(
            name="financial_analyst",
            role=AgentRole.FINANCIAL_ANALYST,
            system_message="""You are a senior financial analyst with expertise in comprehensive financial statement analysis.

Your core competencies include:
1. Financial ratio analysis (profitability, liquidity, efficiency, solvency)
2. Cash flow analysis and quality assessment
3. Trend analysis and growth rate evaluation
4. DuPont analysis and performance decomposition
5. Cross-sectional and time-series benchmarking
6. Financial forecasting and valuation modeling
7. Industry analysis and competitive positioning

Methodology requirements:
- Apply rigorous financial analysis standards
- Consider both quantitative and qualitative factors
- Identify key value drivers and business model risks
- Assess management efficiency and capital allocation decisions
- Evaluate accounting quality and earnings sustainability
- Provide context-aware benchmark comparisons

Always provide detailed methodology notes, assumptions, and confidence levels for your analyses.""",
            llm_config=self._get_optimized_config(temperature=0.2),
            max_consecutive_auto_reply=25
        )
        return self.create_agent(config)

    def create_risk_analyst(self) -> autogen.AssistantAgent:
        """Create risk analysis agent"""
        config = AgentConfig(
            name="risk_analyst",
            role=AgentRole.RISK_ANALYST,
            system_message="""You are a specialized risk analyst focusing on comprehensive financial risk assessment.

Your expertise covers:
1. Market risk analysis (VaR, CVaR, beta, volatility)
2. Credit risk evaluation and default probability modeling
3. Liquidity risk assessment and funding analysis
4. Operational risk identification and scenario analysis
5. Regulatory compliance risk assessment
6. Stress testing and sensitivity analysis
7. Portfolio risk decomposition and concentration analysis

Technical requirements:
- Apply advanced statistical and econometric methods
- Consider both normal and extreme market conditions
- Model correlations and tail dependencies
- Assess risk factor exposures and sensitivities
- Develop appropriate risk metrics and limits frameworks
- Provide early warning indicators and risk monitoring

Always quantify risk exposures with appropriate confidence intervals and provide actionable risk management recommendations.""",
            llm_config=self._get_optimized_config(temperature=0.1),
            max_consecutive_auto_reply=20
        )
        return self.create_agent(config)

    def create_quantitative_analyst(self) -> autogen.AssistantAgent:
        """Create quantitative analysis agent"""
        config = AgentConfig(
            name="quantitative_analyst",
            role=AgentRole.QUANTITATIVE_ANALYST,
            system_message="""You are a quantitative analyst specializing in advanced financial modeling and statistical analysis.

Your domain expertise includes:
1. Statistical modeling and machine learning applications
2. Time series analysis and forecasting
3. Factor model construction and validation
4. Portfolio optimization and asset allocation
5. Algorithmic trading strategy development
6. Backtesting framework design and performance evaluation
7. Derivative pricing and risk-neutral modeling
8. Monte Carlo simulation and numerical methods

Technical standards:
- Apply rigorous mathematical and statistical methods
- Ensure model robustness and overfitting prevention
- Implement proper cross-validation and out-of-sample testing
- Consider transaction costs and market impact
- Develop realistic assumptions and constraints
- Provide comprehensive performance attribution analysis
- Document model limitations and risk factors

Always provide detailed methodology, statistical significance testing, and practical implementation considerations.""",
            llm_config=self._get_optimized_config(temperature=0.1),
            max_consecutive_auto_reply=30
        )
        return self.create_agent(config)

    def create_report_generator(self) -> autogen.AssistantAgent:
        """Create report generation agent"""
        config = AgentConfig(
            name="report_generator",
            role=AgentRole.REPORT_GENERATOR,
            system_message="""You are a financial reporting specialist focused on creating comprehensive analysis reports.

Your responsibilities include:
1. Synthesizing analysis results from multiple agents
2. Creating structured, professional financial reports
3. Developing executive summaries and key insights
4. Designing data visualizations and charts
5. Ensuring report clarity and actionable recommendations
6. Maintaining professional formatting and presentation
7. Adapting content for different stakeholder audiences

Quality standards:
- Ensure accuracy and consistency across all report sections
- Present complex analysis in accessible, understandable formats
- Highlight key findings and actionable recommendations
- Support conclusions with appropriate evidence and analysis
- Maintain objectivity and balanced perspective
- Include appropriate disclaimers and limitations

Always tailor reports to the specific needs of the intended audience and provide clear, actionable insights.""",
            llm_config=self._get_optimized_config(temperature=0.3),
            max_consecutive_auto_reply=15
        )
        return self.create_agent(config)

    def create_validator(self) -> autogen.AssistantAgent:
        """Create validation agent"""
        config = AgentConfig(
            name="validator",
            role=AgentRole.VALIDATOR,
            system_message="""You are a quality assurance and validation specialist for financial analysis.

Your core responsibilities include:
1. Validating data quality and consistency across sources
2. Reviewing analytical methodologies and assumptions
3. Cross-checking calculations and results
4. Ensuring compliance with financial analysis standards
5. Identifying potential biases or errors in analysis
6. Verifying that conclusions are supported by evidence
7. Assessing overall analysis quality and reliability

Validation methodology:
- Apply systematic quality control procedures
- Cross-validate results using multiple approaches
- Identify outliers and anomalies requiring investigation
- Ensure proper statistical methods and significance testing
- Verify that models are appropriate for the data and context
- Check that conclusions logically follow from the analysis

Provide detailed validation reports with specific quality metrics and recommendations for improvement.""",
            llm_config=self._get_optimized_config(temperature=0.1),
            max_consecutive_auto_reply=15
        )
        return self.create_agent(config)

    def _get_optimized_config(self, temperature: float = 0.1) -> Dict[str, Any]:
        """Get optimized LLM configuration"""
        config = self.base_llm_config.copy()
        config.update({
            "temperature": temperature,
            "max_tokens": 8000,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        })
        return config

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for performance tracking"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_agent_performance(self, agent_name: str) -> Optional[AgentPerformance]:
        """Get performance metrics for a specific agent"""
        return self.agent_performance.get(agent_name)

    def get_all_performance_metrics(self) -> Dict[str, AgentPerformance]:
        """Get performance metrics for all agents"""
        return self.agent_performance.copy()