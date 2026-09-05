"""
Data Formatter
Advanced data formatting for tables, reports, and exports
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import json
import csv
import io

logger = logging.getLogger(__name__)


class DataFormat(Enum):
    """Data output formats"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    XML = "xml"
    PARQUET = "parquet"


class TableStyle(Enum):
    """Table styling options"""
    DEFAULT = "default"
    MINIMAL = "minimal"
    STRIPED = "striped"
    BORDERED = "bordered"
    GRID = "grid"
    FANCY = "fancy"


class Alignment(Enum):
    """Text alignment options"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class CellFormat:
    """Cell formatting configuration"""
    data_type: str = "string"  # string, number, currency, percentage, date
    decimals: int = 2
    currency_symbol: str = "$"
    percentage_multiplier: float = 100
    date_format: str = "%Y-%m-%d"
    alignment: Alignment = Alignment.LEFT
    font_weight: str = "normal"
    color: Optional[str] = None
    background_color: Optional[str] = None
    custom_format: Optional[str] = None


@dataclass
class TableConfig:
    """Table configuration"""
    title: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    data: Union[pd.DataFrame, List[Dict[str, Any]], List[List[Any]]]
    style: TableStyle = TableStyle.DEFAULT
    column_formats: Dict[str, CellFormat] = field(default_factory=dict)
    row_formats: Dict[int, CellFormat] = field(default_factory=dict)
    conditional_formats: List[Dict[str, Any]] = field(default_factory=list)
    total_row: bool = False
    header_row: bool = True
    stripe_rows: bool = True
    border: bool = True
    width: Optional[int] = None
    css_class: Optional[str] = None


class DataFormatter:
    """Advanced data formatting system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # CSS styles for different table styles
        self.css_styles = self._load_css_styles()

        # Number formatters
        self.number_formatters = {
            'currency': self._format_currency,
            'percentage': self._format_percentage,
            'number': self._format_number,
            'date': self._format_date,
            'string': self._format_string
        }

        logger.info("Data Formatter initialized")

    def _load_css_styles(self) -> Dict[str, str]:
        """Load CSS styles for different table styles"""
        return {
            'default': """
            .default-table {
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
            }
            .default-table th, .default-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .default-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .default-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            """,
            'minimal': """
            .minimal-table {
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
            }
            .minimal-table th, .minimal-table td {
                padding: 8px;
                text-align: left;
            }
            """,
            'striped': """
            .striped-table {
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
            }
            .striped-table th, .striped-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .striped-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .striped-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            """,
            'bordered': """
            .bordered-table {
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
            }
            .bordered-table th, .bordered-table td {
                border: 2px solid #333;
                padding: 8px;
                text-align: left;
            }
            .bordered-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            """,
            'grid': """
            .grid-table {
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
            }
            .grid-table th, .grid-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .grid-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .grid-table td {
                border: 1px solid #ddd;
            }
            """,
            'fancy': """
            .fancy-table {
                border-collapse: collapse;
                width: 100%;
                font-family: Georgia, serif;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .fancy-table th, .fancy-table td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            .fancy-table th {
                background: linear-gradient(to bottom, #f2f2f2, #e6e6e6);
                font-weight: bold;
                text-transform: uppercase;
            }
            .fancy-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .fancy-table tr:hover {
                background-color: #f5f5f5;
            }
            """
        }

    def format_table(self, config: TableConfig, output_format: DataFormat = DataFormat.HTML) -> str:
        """Format table according to configuration"""
        try:
            # Convert data to DataFrame if needed
            df = self._convert_to_dataframe(config)

            # Apply formatting
            formatted_df = self._apply_formatting(df, config)

            # Generate output
            if output_format == DataFormat.HTML:
                return self._generate_html_table(formatted_df, config)
            elif output_format == DataFormat.MARKDOWN:
                return self._generate_markdown_table(formatted_df, config)
            elif output_format == DataFormat.CSV:
                return self._generate_csv_table(formatted_df, config)
            elif output_format == DataFormat.JSON:
                return self._generate_json_table(formatted_df, config)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

        except Exception as e:
            logger.error(f"Table formatting failed: {e}")
            raise

    def _convert_to_dataframe(self, config: TableConfig) -> pd.DataFrame:
        """Convert various data formats to DataFrame"""
        if isinstance(config.data, pd.DataFrame):
            return config.data.copy()
        elif isinstance(config.data, list):
            if len(config.data) == 0:
                return pd.DataFrame()
            elif isinstance(config.data[0], dict):
                return pd.DataFrame(config.data)
            elif isinstance(config.data[0], list):
                if config.headers:
                    return pd.DataFrame(config.data, columns=config.headers)
                else:
                    return pd.DataFrame(config.data)
            else:
                # Single column
                return pd.DataFrame(config.data, columns=['Value'])

        raise ValueError("Unsupported data format")

    def _apply_formatting(self, df: pd.DataFrame, config: TableConfig) -> pd.DataFrame:
        """Apply formatting to DataFrame"""
        formatted_df = df.copy()

        # Apply column formatting
        for column, format_config in config.column_formats.items():
            if column in formatted_df.columns:
                formatted_df[column] = formatted_df[column].apply(
                    lambda x: self._format_value(x, format_config)
                )

        # Apply conditional formatting
        for condition in config.conditional_formats:
            formatted_df = self._apply_conditional_formatting(formatted_df, condition)

        return formatted_df

    def _format_value(self, value: Any, format_config: CellFormat) -> str:
        """Format a single value"""
        try:
            if pd.isna(value):
                return ""

            formatter = self.number_formatters.get(format_config.data_type, self._format_string)
            return formatter(value, format_config)

        except Exception as e:
            logger.warning(f"Failed to format value {value}: {e}")
            return str(value)

    def _format_currency(self, value: Any, format_config: CellFormat) -> str:
        """Format currency value"""
        try:
            num_value = float(value)
            return f"{format_config.currency_symbol}{num_value:,.{format_config.decimals}f}"
        except:
            return str(value)

    def _format_percentage(self, value: Any, format_config: CellFormat) -> str:
        """Format percentage value"""
        try:
            num_value = float(value) * format_config.percentage_multiplier
            return f"{num_value:.{format_config.decimals}f}%"
        except:
            return str(value)

    def _format_number(self, value: Any, format_config: CellFormat) -> str:
        """Format number value"""
        try:
            num_value = float(value)
            return f"{num_value:,.{format_config.decimals}f}"
        except:
            return str(value)

    def _format_date(self, value: Any, format_config: CellFormat) -> str:
        """Format date value"""
        try:
            if isinstance(value, str):
                date_obj = datetime.strptime(value, "%Y-%m-%d")
            elif isinstance(value, (int, float)):
                date_obj = datetime.fromtimestamp(value)
            else:
                date_obj = value

            return date_obj.strftime(format_config.date_format)
        except:
            return str(value)

    def _format_string(self, value: Any, format_config: CellFormat) -> str:
        """Format string value"""
        return str(value)

    def _apply_conditional_formatting(self, df: pd.DataFrame, condition: Dict[str, Any]) -> pd.DataFrame:
        """Apply conditional formatting to DataFrame"""
        try:
            column = condition.get('column')
            condition_type = condition.get('type')
            value = condition.get('value')
            format_config = condition.get('format')

            if column not in df.columns:
                return df

            if condition_type == 'greater_than':
                mask = df[column] > value
            elif condition_type == 'less_than':
                mask = df[column] < value
            elif condition_type == 'equal':
                mask = df[column] == value
            elif condition_type == 'between':
                min_val, max_val = value
                mask = (df[column] >= min_val) & (df[column] <= max_val)
            else:
                return df

            # Apply formatting to matching rows
            for idx in df[mask].index:
                if idx not in df.columns:
                    df.loc[idx, column] = self._format_value(df.loc[idx, column], format_config)

            return df

        except Exception as e:
            logger.error(f"Conditional formatting failed: {e}")
            return df

    def _generate_html_table(self, df: pd.DataFrame, config: TableConfig) -> str:
        """Generate HTML table"""
        html_parts = []

        # Add CSS
        css_class = config.css_class or f"{config.style.value}-table"
        html_parts.append(f"<style>{self.css_styles[config.style.value]}</style>")

        # Add title
        if config.title:
            html_parts.append(f"<h2>{config.title}</h2>")

        # Start table
        html_parts.append(f'<table class="{css_class}">')

        # Add header
        if config.header_row:
            html_parts.append("<thead><tr>")
            for column in df.columns:
                html_parts.append(f"<th>{column}</th>")
            html_parts.append("</tr></thead>")

        # Add body
        html_parts.append("<tbody>")
        for _, row in df.iterrows():
            html_parts.append("<tr>")
            for value in row:
                html_parts.append(f"<td>{value}</td>")
            html_parts.append("</tr>")
        html_parts.append("</tbody>")

        # Add total row if requested
        if config.total_row:
            html_parts.append("<tfoot><tr>")
            for column in df.columns:
                if pd.api.types.is_numeric_dtype(df[column]):
                    total = df[column].sum()
                    html_parts.append(f"<td><strong>{total:,.2f}</strong></td>")
                else:
                    html_parts.append("<td><strong>Total</strong></td>")
            html_parts.append("</tr></tfoot>")

        html_parts.append("</table>")

        return '\n'.join(html_parts)

    def _generate_markdown_table(self, df: pd.DataFrame, config: TableConfig) -> str:
        """Generate Markdown table"""
        md_parts = []

        # Add title
        if config.title:
            md_parts.append(f"## {config.title}")
            md_parts.append("")

        # Add table headers
        headers = "| " + " | ".join(df.columns) + " |"
        md_parts.append(headers)

        # Add separator
        separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
        md_parts.append(separator)

        # Add rows
        for _, row in df.iterrows():
            row_str = "| " + " | ".join(str(value) for value in row) + " |"
            md_parts.append(row_str)

        # Add total row if requested
        if config.total_row:
            total_parts = []
            for column in df.columns:
                if pd.api.types.is_numeric_dtype(df[column]):
                    total = df[column].sum()
                    total_parts.append(f"**{total:,.2f}**")
                else:
                    total_parts.append("**Total**")
            total_str = "| " + " | ".join(total_parts) + " |"
            md_parts.append(total_str)

        return '\n'.join(md_parts)

    def _generate_csv_table(self, df: pd.DataFrame, config: TableConfig) -> str:
        """Generate CSV table"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        if config.header_row:
            writer.writerow(df.columns)

        # Write data
        for _, row in df.iterrows():
            writer.writerow(row.tolist())

        return output.getvalue()

    def _generate_json_table(self, df: pd.DataFrame, config: TableConfig) -> str:
        """Generate JSON table"""
        data = {
            'title': config.title,
            'headers': df.columns.tolist(),
            'data': df.to_dict('records'),
            'style': config.style.value,
            'generated_at': datetime.now().isoformat()
        }

        return json.dumps(data, indent=2, default=str)

    def format_data(self, data: Any, format_type: str = "string", **kwargs) -> str:
        """Format data with specified type"""
        format_config = CellFormat(data_type=format_type, **kwargs)
        return self._format_value(data, format_config)

    def export_data(self, data: Union[pd.DataFrame, List[Dict]],
                    filename: str, format: DataFormat = DataFormat.CSV,
                    **kwargs) -> str:
        """Export data to file"""
        try:
            config = TableConfig(data=data, **kwargs)

            if format == DataFormat.CSV:
                content = self._generate_csv_table(pd.DataFrame(data), config)
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    f.write(content)
            elif format == DataFormat.EXCEL:
                df = pd.DataFrame(data)
                df.to_excel(filename, index=False)
            elif format == DataFormat.JSON:
                content = self._generate_json_table(pd.DataFrame(data), config)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif format == DataFormat.HTML:
                content = self._generate_html_table(pd.DataFrame(data), config)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif format == DataFormat.MARKDOWN:
                content = self._generate_markdown_table(pd.DataFrame(data), config)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif format == DataFormat.PARQUET:
                df = pd.DataFrame(data)
                df.to_parquet(filename)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            logger.info(f"Data exported to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Data export failed: {e}")
            raise

    def create_financial_table(self, financial_data: Dict[str, Any],
                              table_type: str = "ratios") -> TableConfig:
        """Create financial table configuration"""
        if table_type == "ratios":
            headers = ["Ratio", "Value", "Benchmark", "Percentile"]
            data = []
            for ratio_name, ratio_data in financial_data.items():
                data.append([
                    ratio_name,
                    ratio_data.get('value', 0),
                    ratio_data.get('benchmark', 0),
                    ratio_data.get('percentile', 0)
                ])

            column_formats = {
                "Value": CellFormat(data_type="number", decimals=2),
                "Benchmark": CellFormat(data_type="number", decimals=2),
                "Percentile": CellFormat(data_type="percentage", decimals=0)
            }

            return TableConfig(
                title="Financial Ratios Analysis",
                headers=headers,
                data=data,
                style=TableStyle.BORDERED,
                column_formats=column_formats,
                total_row=False
            )

        elif table_type == "metrics":
            headers = ["Metric", "Current", "Previous", "Change"]
            data = []
            for metric_name, metric_data in financial_data.items():
                data.append([
                    metric_name,
                    metric_data.get('current', 0),
                    metric_data.get('previous', 0),
                    metric_data.get('change', 0)
                ])

            column_formats = {
                "Current": CellFormat(data_type="currency", decimals=2),
                "Previous": CellFormat(data_type="currency", decimals=2),
                "Change": CellFormat(data_type="percentage", decimals=1)
            }

            return TableConfig(
                title="Financial Metrics",
                headers=headers,
                data=data,
                style=TableStyle.GRID,
                column_formats=column_formats,
                total_row=False
            )

        else:
            raise ValueError(f"Unknown table type: {table_type}")


# Global instances
_data_formatter: Optional[DataFormatter] = None


def get_data_formatter(config: Dict[str, Any] = None) -> DataFormatter:
    """Get or create the global data formatter instance"""
    global _data_formatter
    if _data_formatter is None:
        _data_formatter = DataFormatter(config)
    return _data_formatter


def format_table(config: TableConfig, output_format: DataFormat = DataFormat.HTML) -> str:
    """Format a table using the global formatter"""
    formatter = get_data_formatter()
    return formatter.format_table(config, output_format)


def format_data(data: Any, format_type: str = "string", **kwargs) -> str:
    """Format data using the global formatter"""
    formatter = get_data_formatter()
    return formatter.format_data(data, format_type, **kwargs)


def export_data(data: Union[pd.DataFrame, List[Dict]],
                filename: str, format: DataFormat = DataFormat.CSV,
                **kwargs) -> str:
    """Export data using the global formatter"""
    formatter = get_data_formatter()
    return formatter.export_data(data, filename, format, **kwargs)