"""
Report Generator
Advanced report generation with templates, sections, and automated formatting
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import jinja2
import markdown
import pdfkit
from pathlib import Path
import base64
import io

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Report output formats"""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    EXCEL = "excel"
    WORD = "word"


class ReportType(Enum):
    """Report types"""
    FINANCIAL = "financial"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    ANALYSIS = "analysis"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


@dataclass
class ReportSection:
    """Report section definition"""
    title: str
    content: str
    section_type: str = "text"
    data: Optional[Dict[str, Any]] = None
    charts: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass
class ReportTemplate:
    """Report template definition"""
    name: str
    description: str
    sections: List[ReportSection]
    template_file: Optional[str] = None
    style_config: Dict[str, Any] = field(default_factory=dict)
    data_requirements: List[str] = field(default_factory=list)


@dataclass
class ReportConfig:
    """Report generation configuration"""
    title: str
    author: str
    report_type: ReportType
    format: ReportFormat
    template: Optional[str] = None
    output_path: str = "reports"
    include_charts: bool = True
    include_tables: bool = True
    include_appendix: bool = False
    branding: Dict[str, Any] = field(default_factory=dict)
    custom_css: Optional[str] = None
    header_footer: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    """Advanced report generation system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Template engine
        self.template_loader = jinja2.FileSystemLoader(
            self.config.get('template_dir', 'templates')
        )
        self.jinja_env = jinja2.Environment(
            loader=self.template_loader,
            autoescape=True,
            extensions=['jinja2.ext.do']
        )

        # Report templates
        self.templates: Dict[str, ReportTemplate] = {}
        self._load_default_templates()

        # Output settings
        self.output_dir = Path(self.config.get('output_dir', 'reports'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Default styling
        self.default_styles = self._load_default_styles()

        # Markdown processor
        self.md_processor = markdown.Markdown(extensions=['tables', 'fenced_code'])

        logger.info("Report Generator initialized")

    def _load_default_templates(self):
        """Load default report templates"""
        # Financial analysis template
        self.templates['financial'] = ReportTemplate(
            name="Financial Analysis Report",
            description="Comprehensive financial analysis with ratios and trends",
            sections=[
                ReportSection(
                    title="Executive Summary",
                    content="Analysis overview and key findings",
                    section_type="summary"
                ),
                ReportSection(
                    title="Financial Performance",
                    content="Revenue, profit, and growth metrics",
                    section_type="performance",
                    data_requirements=['revenue', 'profit', 'growth']
                ),
                ReportSection(
                    title="Financial Ratios",
                    content="Key financial ratios and benchmarks",
                    section_type="ratios",
                    data_requirements=['ratios']
                ),
                ReportSection(
                    title="Trend Analysis",
                    content="Historical trends and projections",
                    section_type="trends",
                    data_requirements=['historical_data']
                ),
                ReportSection(
                    title="Recommendations",
                    content="Strategic recommendations",
                    section_type="recommendations"
                )
            ]
        )

        # Risk analysis template
        self.templates['risk'] = ReportTemplate(
            name="Risk Analysis Report",
            description="Comprehensive risk assessment and mitigation strategies",
            sections=[
                ReportSection(
                    title="Risk Overview",
                    content="Summary of key risk factors",
                    section_type="overview"
                ),
                ReportSection(
                    title="Market Risk",
                    content="Market risk analysis and VaR calculations",
                    section_type="market_risk",
                    data_requirements=['var_data', 'market_risk']
                ),
                ReportSection(
                    title="Credit Risk",
                    content="Credit risk assessment",
                    section_type="credit_risk",
                    data_requirements=['credit_data']
                ),
                ReportSection(
                    title="Operational Risk",
                    content="Operational risk factors",
                    section_type="operational_risk",
                    data_requirements=['operational_data']
                ),
                ReportSection(
                    title="Risk Mitigation",
                    content="Risk mitigation strategies",
                    section_type="mitigation"
                )
            ]
        )

        # Portfolio analysis template
        self.templates['portfolio'] = ReportTemplate(
            name="Portfolio Analysis Report",
            description="Portfolio performance, allocation, and optimization",
            sections=[
                ReportSection(
                    title="Portfolio Overview",
                    content="Portfolio summary and key metrics",
                    section_type="overview"
                ),
                ReportSection(
                    title="Asset Allocation",
                    content="Current allocation and recommendations",
                    section_type="allocation",
                    data_requirements=['allocation_data']
                ),
                ReportSection(
                    title="Performance Analysis",
                    content="Returns, risk metrics, and benchmarks",
                    section_type="performance",
                    data_requirements=['performance_data']
                ),
                ReportSection(
                    title="Risk Analysis",
                    content="Portfolio risk metrics",
                    section_type="risk",
                    data_requirements=['risk_metrics']
                ),
                ReportSection(
                    title="Optimization Suggestions",
                    content="Portfolio optimization recommendations",
                    section_type="optimization"
                )
            ]
        )

    def _load_default_styles(self) -> Dict[str, str]:
        """Load default CSS styles"""
        return {
            'main': """
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }

            .header {
                border-bottom: 3px solid #007acc;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }

            .title {
                color: #007acc;
                font-size: 28px;
                font-weight: bold;
            }

            .section {
                margin-bottom: 30px;
            }

            .section-title {
                color: #0056b3;
                font-size: 22px;
                border-bottom: 2px solid #e0e0e0;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }

            .metric-card {
                background: #f8f9fa;
                border-left: 4px solid #007acc;
                padding: 15px;
                margin: 10px 0;
                border-radius: 4px;
            }

            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #007acc;
            }

            .metric-label {
                color: #666;
                font-size: 14px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }

            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }

            th {
                background-color: #007acc;
                color: white;
                font-weight: bold;
            }

            tr:nth-child(even) {
                background-color: #f8f9fa;
            }

            .chart-container {
                margin: 20px 0;
                text-align: center;
            }

            .recommendation {
                background: #e8f4f8;
                border-left: 4px solid #17a2b8;
                padding: 15px;
                margin: 10px 0;
            }

            .footer {
                border-top: 1px solid #ddd;
                padding-top: 20px;
                margin-top: 40px;
                font-size: 12px;
                color: #666;
                text-align: center;
            }
            """,
            'print': """
            @media print {
                body {
                    font-size: 12px;
                    line-height: 1.4;
                }

                .no-print {
                    display: none;
                }

                .page-break {
                    page-break-before: always;
                }
            }
            """
        }

    def generate_report(self, config: ReportConfig, data: Dict[str, Any]) -> str:
        """Generate a complete report"""
        logger.info(f"Generating {config.report_type.value} report: {config.title}")

        # Get template
        template = self._get_template(config.template or config.report_type.value)

        # Validate data requirements
        self._validate_data_requirements(template, data)

        # Generate sections
        sections = self._generate_sections(template, data)

        # Generate complete report
        report_content = self._assemble_report(config, sections, data)

        # Format output
        output_path = self._save_report(config, report_content)

        logger.info(f"Report generated: {output_path}")
        return output_path

    def _get_template(self, template_name: str) -> ReportTemplate:
        """Get report template"""
        if template_name in self.templates:
            return self.templates[template_name]

        # Load custom template from file
        template_file = self.config.get('template_dir', 'templates') / f"{template_name}.yaml"
        if template_file.exists():
            return self._load_template_from_file(template_file)

        raise ValueError(f"Template not found: {template_name}")

    def _load_template_from_file(self, template_file: Path) -> ReportTemplate:
        """Load template from YAML file"""
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)

        sections = []
        for section_data in template_data.get('sections', []):
            sections.append(ReportSection(**section_data))

        return ReportTemplate(
            name=template_data['name'],
            description=template_data.get('description', ''),
            sections=sections,
            template_file=template_data.get('template_file'),
            style_config=template_data.get('style_config', {}),
            data_requirements=template_data.get('data_requirements', [])
        )

    def _validate_data_requirements(self, template: ReportTemplate, data: Dict[str, Any]):
        """Validate that required data is available"""
        missing_requirements = []
        for requirement in template.data_requirements:
            if requirement not in data:
                missing_requirements.append(requirement)

        if missing_requirements:
            logger.warning(f"Missing required data: {missing_requirements}")

    def _generate_sections(self, template: ReportTemplate, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate report sections from template"""
        sections = []

        for template_section in template.sections:
            section_data = self._generate_section_content(template_section, data)
            sections.append(section_data)

        return sections

    def _generate_section_content(self, section: ReportSection, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content for a specific section"""
        section_data = {
            'title': section.title,
            'content': section.content,
            'type': section.section_type,
            'data': section.data or {},
            'charts': section.charts,
            'tables': section.tables,
            'metadata': section.metadata
        }

        # Process section based on type
        if section.section_type == 'performance':
            section_data.update(self._generate_performance_section(data))
        elif section.section_type == 'ratios':
            section_data.update(self._generate_ratios_section(data))
        elif section.section_type == 'trends':
            section_data.update(self._generate_trends_section(data))
        elif section.section_type == 'risk':
            section_data.update(self._generate_risk_section(data))
        elif section.section_type == 'allocation':
            section_data.update(self._generate_allocation_section(data))

        return section_data

    def _generate_performance_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance metrics section"""
        metrics = {}

        if 'revenue' in data:
            metrics['revenue'] = {
                'current': data['revenue'].get('current', 0),
                'previous': data['revenue'].get('previous', 0),
                'growth': self._calculate_growth(data['revenue'].get('current', 0), data['revenue'].get('previous', 0))
            }

        if 'profit' in data:
            metrics['profit'] = {
                'current': data['profit'].get('current', 0),
                'margin': data['profit'].get('margin', 0)
            }

        return {
            'metrics': metrics,
            'charts': ['revenue_trend', 'profit_margin'],
            'tables': ['performance_summary']
        }

    def _generate_ratios_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial ratios section"""
        ratios = data.get('ratios', {})

        # Categorize ratios
        ratio_categories = {
            'liquidity': ['current_ratio', 'quick_ratio', 'cash_ratio'],
            'profitability': ['gross_margin', 'net_margin', 'roe', 'roa'],
            'leverage': ['debt_to_equity', 'debt_ratio', 'interest_coverage'],
            'efficiency': ['asset_turnover', 'inventory_turnover', 'receivables_turnover']
        }

        categorized_ratios = {}
        for category, ratio_names in ratio_categories.items():
            categorized_ratios[category] = {
                name: ratios.get(name, 0)
                for name in ratio_names
                if name in ratios
            }

        return {
            'ratio_categories': categorized_ratios,
            'charts': ['ratio_comparison', 'ratio_trends'],
            'tables': ['ratio_analysis']
        }

    def _generate_trends_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend analysis section"""
        historical_data = data.get('historical_data', [])

        trends = {}
        for metric in ['revenue', 'profit', 'assets']:
            if metric in historical_data[0] if historical_data else []:
                trends[metric] = self._calculate_trend([item[metric] for item in historical_data])

        return {
            'trends': trends,
            'charts': ['historical_trends', 'growth_rates'],
            'tables': ['trend_analysis']
        }

    def _generate_risk_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk analysis section"""
        risk_metrics = data.get('risk_metrics', {})

        return {
            'var_data': risk_metrics.get('var', {}),
            'sharpe_ratio': risk_metrics.get('sharpe_ratio', 0),
            'beta': risk_metrics.get('beta', 0),
            'charts': ['risk_distribution', 'var_analysis'],
            'tables': ['risk_metrics']
        }

    def _generate_allocation_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate asset allocation section"""
        allocation = data.get('allocation_data', {})

        return {
            'current_allocation': allocation.get('current', {}),
            'recommended_allocation': allocation.get('recommended', {}),
            'charts': ['allocation_pie', 'allocation_comparison'],
            'tables': ['allocation_summary']
        }

    def _calculate_growth(self, current: float, previous: float) -> float:
        """Calculate growth percentage"""
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """Calculate trend metrics"""
        if not values:
            return {'trend': 0, 'volatility': 0}

        # Simple linear regression for trend
        n = len(values)
        if n < 2:
            return {'trend': 0, 'volatility': 0}

        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        # Calculate slope (trend)
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0

        # Calculate volatility (standard deviation)
        variance = sum((v - y_mean) ** 2 for v in values) / (n - 1) if n > 1 else 0
        volatility = variance ** 0.5

        return {
            'trend': slope,
            'volatility': volatility,
            'mean': y_mean,
            'min': min(values),
            'max': max(values)
        }

    def _assemble_report(self, config: ReportConfig, sections: List[Dict[str, Any]], data: Dict[str, Any]) -> str:
        """Assemble complete report content"""
        template_vars = {
            'title': config.title,
            'author': config.author,
            'date': datetime.now().strftime('%B %d, %Y'),
            'sections': sections,
            'data': data,
            'branding': config.branding,
            'metadata': config.metadata
        }

        # Use Jinja2 template if available
        if config.template:
            try:
                template = self.jinja_env.get_template(f"{config.template}.html")
                return template.render(**template_vars)
            except:
                logger.warning(f"Template {config.template} not found, using default")

        # Generate HTML report
        return self._generate_html_report(template_vars)

    def _generate_html_report(self, template_vars: Dict[str, Any]) -> str:
        """Generate HTML report content"""
        html_parts = []

        # Header
        html_parts.append(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{template_vars['title']}</title>
            <style>
                {self.default_styles['main']}
                {self.default_styles['print']}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 class="title">{template_vars['title']}</h1>
                <p>Generated by {template_vars['author']} on {template_vars['date']}</p>
            </div>
        """)

        # Sections
        for section in template_vars['sections']:
            html_parts.append(f"""
            <div class="section">
                <h2 class="section-title">{section['title']}</h2>
                <div class="section-content">
                    {self._render_section_content(section)}
                </div>
            </div>
            """)

        # Footer
        html_parts.append("""
            <div class="footer">
                <p>This report was generated automatically by the AutoGen Financial Analysis System.</p>
            </div>
        </body>
        </html>
        """)

        return '\n'.join(html_parts)

    def _render_section_content(self, section: Dict[str, Any]) -> str:
        """Render section content based on type"""
        content = []

        # Add markdown content
        if section.get('content'):
            content.append(self.md_processor.convert(section['content']))

        # Add metrics
        if 'metrics' in section:
            for metric_name, metric_data in section['metrics'].items():
                content.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{self._format_value(metric_data.get('current', 0))}</div>
                    <div class="metric-label">{metric_name.replace('_', ' ').title()}</div>
                </div>
                """)

        # Add charts placeholder
        if section.get('charts'):
            for chart_name in section['charts']:
                content.append(f'<div class="chart-container" id="chart-{chart_name}"></div>')

        # Add tables placeholder
        if section.get('tables'):
            for table_name in section['tables']:
                content.append(f'<div class="table-container" id="table-{table_name}"></div>')

        return '\n'.join(content)

    def _format_value(self, value: Any) -> str:
        """Format numeric values for display"""
        if isinstance(value, (int, float)):
            if abs(value) >= 1000000:
                return f"${value/1000000:.2f}M"
            elif abs(value) >= 1000:
                return f"${value/1000:.2f}K"
            else:
                return f"${value:.2f}"
        return str(value)

    def _save_report(self, config: ReportConfig, content: str) -> str:
        """Save report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{config.title.replace(' ', '_').lower()}_{timestamp}.{config.format.value}"
        filepath = self.output_dir / filename

        if config.format == ReportFormat.HTML:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        elif config.format == ReportFormat.PDF:
            # Convert HTML to PDF
            try:
                pdfkit.from_string(content, str(filepath))
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                # Fallback to HTML
                filepath = filepath.with_suffix('.html')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
        elif config.format == ReportFormat.MARKDOWN:
            # Convert HTML to Markdown
            md_content = self._html_to_markdown(content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
        elif config.format == ReportFormat.JSON:
            # Save as structured data
            report_data = {
                'config': {
                    'title': config.title,
                    'author': config.author,
                    'type': config.report_type.value,
                    'generated': datetime.now().isoformat()
                },
                'content': content,
                'metadata': config.metadata
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)

        return str(filepath)

    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to Markdown (simplified)"""
        # This is a simplified conversion
        # In production, use a proper HTML to Markdown converter
        import re

        # Remove HTML tags and structure
        content = re.sub(r'<[^>]+>', '', html_content)
        content = re.sub(r'\s+', ' ', content).strip()

        # Add basic markdown structure
        lines = content.split('\n')
        md_lines = []
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('Generated by'):
                    continue
                md_lines.append(line)

        return '\n\n'.join(md_lines)

    def generate_financial_report(self, company_data: Dict[str, Any], output_format: ReportFormat = ReportFormat.HTML) -> str:
        """Generate financial analysis report"""
        config = ReportConfig(
            title=f"Financial Analysis Report - {company_data.get('company_name', 'Unknown')}",
            author="AutoGen Financial System",
            report_type=ReportType.FINANCIAL,
            format=output_format
        )

        return self.generate_report(config, company_data)

    def generate_risk_report(self, risk_data: Dict[str, Any], output_format: ReportFormat = ReportFormat.HTML) -> str:
        """Generate risk analysis report"""
        config = ReportConfig(
            title="Risk Analysis Report",
            author="AutoGen Financial System",
            report_type=ReportType.RISK,
            format=output_format
        )

        return self.generate_report(config, risk_data)

    def generate_portfolio_report(self, portfolio_data: Dict[str, Any], output_format: ReportFormat = ReportFormat.HTML) -> str:
        """Generate portfolio analysis report"""
        config = ReportConfig(
            title=f"Portfolio Analysis Report - {portfolio_data.get('portfolio_name', 'Unknown')}",
            author="AutoGen Financial System",
            report_type=ReportType.PORTFOLIO,
            format=output_format
        )

        return self.generate_report(config, portfolio_data)

    def add_custom_template(self, template: ReportTemplate):
        """Add a custom report template"""
        self.templates[template.name] = template
        logger.info(f"Added custom template: {template.name}")

    def get_available_templates(self) -> List[str]:
        """Get list of available templates"""
        return list(self.templates.keys())


# Global instances
_report_generator: Optional[ReportGenerator] = None


def get_report_generator(config: Dict[str, Any] = None) -> ReportGenerator:
    """Get or create the global report generator instance"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator(config)
    return _report_generator


def generate_report(config: ReportConfig, data: Dict[str, Any]) -> str:
    """Generate a report using the global generator"""
    generator = get_report_generator()
    return generator.generate_report(config, data)


def generate_financial_report(company_data: Dict[str, Any], output_format: ReportFormat = ReportFormat.HTML) -> str:
    """Generate financial report"""
    generator = get_report_generator()
    return generator.generate_financial_report(company_data, output_format)


def generate_risk_report(risk_data: Dict[str, Any], output_format: ReportFormat = ReportFormat.HTML) -> str:
    """Generate risk report"""
    generator = get_report_generator()
    return generator.generate_risk_report(risk_data, output_format)


def generate_portfolio_report(portfolio_data: Dict[str, Any], output_format: ReportFormat = ReportFormat.HTML) -> str:
    """Generate portfolio report"""
    generator = get_report_generator()
    return generator.generate_portfolio_report(portfolio_data, output_format)