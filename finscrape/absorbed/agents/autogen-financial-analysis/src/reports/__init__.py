"""
Report Generation and Visualization System
Comprehensive report generation with charts, graphs, and automated formatting
"""

from .report_generator import (
    ReportFormat, ReportTemplate, ReportSection, ReportConfig,
    ReportGenerator, get_report_generator, generate_report,
    generate_financial_report, generate_risk_report, generate_portfolio_report
)
from .visualizer import (
    ChartType, VisualizationTheme, ChartConfig, DashboardConfig,
    Visualizer, get_visualizer, create_chart, create_dashboard,
    save_chart, export_dashboard
)
from .data_formatter import (
    DataFormat, TableStyle, Alignment, CellFormat,
    DataFormatter, get_data_formatter, format_table,
    format_data, export_data
)
from .report_templates import (
    FinancialReportTemplate, RiskReportTemplate, PortfolioReportTemplate,
    AnalysisReportTemplate, ExecutiveReportTemplate, get_template
)
from .export_manager import (
    ExportFormat, ExportConfig, ExportManager, get_export_manager,
    export_report, export_data, schedule_export
)

__all__ = [
    # Report Generator
    "ReportFormat",
    "ReportTemplate",
    "ReportSection",
    "ReportConfig",
    "ReportGenerator",
    "get_report_generator",
    "generate_report",
    "generate_financial_report",
    "generate_risk_report",
    "generate_portfolio_report",

    # Visualizer
    "ChartType",
    "VisualizationTheme",
    "ChartConfig",
    "DashboardConfig",
    "Visualizer",
    "get_visualizer",
    "create_chart",
    "create_dashboard",
    "save_chart",
    "export_dashboard",

    # Data Formatter
    "DataFormat",
    "TableStyle",
    "Alignment",
    "CellFormat",
    "DataFormatter",
    "get_data_formatter",
    "format_table",
    "format_data",
    "export_data",

    # Report Templates
    "FinancialReportTemplate",
    "RiskReportTemplate",
    "PortfolioReportTemplate",
    "AnalysisReportTemplate",
    "ExecutiveReportTemplate",
    "get_template",

    # Export Manager
    "ExportFormat",
    "ExportConfig",
    "ExportManager",
    "get_export_manager",
    "export_report",
    "export_data",
    "schedule_export"
]