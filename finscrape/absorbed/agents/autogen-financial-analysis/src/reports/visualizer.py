"""
Visualizer
Advanced data visualization with charts, dashboards, and interactive plots
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Chart types"""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    PIE = "pie"
    HEATMAP = "heatmap"
    CANDLESTICK = "candlestick"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    CONTOUR = "contour"
    SURFACE = "surface"


class VisualizationTheme(Enum):
    """Visualization themes"""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    FINANCIAL = "financial"
    MINIMAL = "minimal"


@dataclass
class ChartConfig:
    """Chart configuration"""
    title: str
    chart_type: ChartType
    data: Union[pd.DataFrame, Dict[str, Any]]
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    theme: VisualizationTheme = VisualizationTheme.DEFAULT
    width: int = 800
    height: int = 600
    show_legend: bool = True
    interactive: bool = True
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    custom_colors: Optional[List[str]] = None
    layout_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    title: str
    charts: List[ChartConfig]
    layout: str = "grid"  # grid, vertical, horizontal
    theme: VisualizationTheme = VisualizationTheme.DEFAULT
    width: int = 1200
    height: int = 800
    show_controls: bool = True
    auto_refresh: bool = False
    refresh_interval: int = 300  # seconds


class Visualizer:
    """Advanced data visualization system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.default_theme = VisualizationTheme(self.config.get('default_theme', 'default'))

        # Color schemes
        self.color_schemes = {
            'financial': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'corporate': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E'],
            'minimal': ['#333333', '#666666', '#999999', '#cccccc', '#eeeeee'],
            'vibrant': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']
        }

        # Theme configurations
        self.theme_configs = self._load_theme_configs()

        logger.info("Visualizer initialized")

    def _load_theme_configs(self) -> Dict[str, Dict]:
        """Load theme configurations"""
        return {
            'default': {
                'template': 'plotly_white',
                'colorway': self.color_schemes['financial'],
                'font': {'family': 'Arial, sans-serif', 'size': 12},
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
            },
            'dark': {
                'template': 'plotly_dark',
                'colorway': self.color_schemes['financial'],
                'font': {'family': 'Arial, sans-serif', 'size': 12, 'color': 'white'},
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
            },
            'light': {
                'template': 'plotly_white',
                'colorway': self.color_schemes['minimal'],
                'font': {'family': 'Arial, sans-serif', 'size': 12},
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
            },
            'financial': {
                'template': 'plotly_white',
                'colorway': self.color_schemes['financial'],
                'font': {'family': 'Arial, sans-serif', 'size': 12},
                'margin': {'l': 80, 'r': 80, 't': 80, 'b': 80},
                'xaxis': {'gridcolor': '#e0e0e0'},
                'yaxis': {'gridcolor': '#e0e0e0'}
            }
        }

    def create_chart(self, config: ChartConfig) -> go.Figure:
        """Create a chart based on configuration"""
        try:
            theme_config = self.theme_configs.get(config.theme.value, self.theme_configs['default'])

            if config.chart_type == ChartType.LINE:
                fig = self._create_line_chart(config, theme_config)
            elif config.chart_type == ChartType.BAR:
                fig = self._create_bar_chart(config, theme_config)
            elif config.chart_type == ChartType.SCATTER:
                fig = self._create_scatter_chart(config, theme_config)
            elif config.chart_type == ChartType.PIE:
                fig = self._create_pie_chart(config, theme_config)
            elif config.chart_type == ChartType.HEATMAP:
                fig = self._create_heatmap_chart(config, theme_config)
            elif config.chart_type == ChartType.CANDLESTICK:
                fig = self._create_candlestick_chart(config, theme_config)
            elif config.chart_type == ChartType.HISTOGRAM:
                fig = self._create_histogram_chart(config, theme_config)
            elif config.chart_type == ChartType.BOX:
                fig = self._create_box_chart(config, theme_config)
            else:
                raise ValueError(f"Unsupported chart type: {config.chart_type}")

            # Apply theme and layout
            fig.update_layout(
                template=theme_config['template'],
                **theme_config,
                **config.layout_options
            )

            # Add annotations
            for annotation in config.annotations:
                fig.add_annotation(annotation)

            return fig

        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            raise

    def _create_line_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create line chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = px.line(
                config.data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
                width=config.width,
                height=config.height,
                color_discrete_sequence=config.custom_colors or theme_config['colorway']
            )
        else:
            # Handle dict data
            fig = go.Figure()
            for key, values in config.data.items():
                fig.add_trace(go.Scatter(
                    x=list(range(len(values))),
                    y=values,
                    mode='lines',
                    name=key,
                    line=dict(color=(config.custom_colors or theme_config['colorway'])[list(config.data.keys()).index(key) % len(theme_config['colorway'])])
                ))

        return fig

    def _create_bar_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create bar chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = px.bar(
                config.data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
                width=config.width,
                height=config.height,
                color_discrete_sequence=config.custom_colors or theme_config['colorway']
            )
        else:
            # Handle dict data
            fig = go.Figure()
            categories = list(config.data.keys())
            values = list(config.data.values())

            fig.add_trace(go.Bar(
                x=categories,
                y=values,
                marker_color=config.custom_colors or theme_config['colorway']
            ))

        return fig

    def _create_scatter_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create scatter chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = px.scatter(
                config.data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
                width=config.width,
                height=config.height,
                color_discrete_sequence=config.custom_colors or theme_config['colorway']
            )
        else:
            # Handle dict data
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=config.data.get('x', []),
                y=config.data.get('y', []),
                mode='markers',
                marker_color=config.custom_colors or theme_config['colorway']
            ))

        return fig

    def _create_pie_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create pie chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = px.pie(
                config.data,
                values=config.y_column,
                names=config.x_column,
                title=config.title,
                width=config.width,
                height=config.height,
                color_discrete_sequence=config.custom_colors or theme_config['colorway']
            )
        else:
            # Handle dict data
            fig = go.Figure()
            labels = list(config.data.keys())
            values = list(config.data.values())

            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                marker_colors=config.custom_colors or theme_config['colorway']
            ))

        return fig

    def _create_heatmap_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create heatmap chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = px.imshow(
                config.data,
                title=config.title,
                width=config.width,
                height=config.height,
                color_continuous_scale=config.custom_colors or 'RdYlBu_r'
            )
        else:
            # Handle dict data
            fig = go.Figure()
            fig.add_trace(go.Heatmap(
                z=config.data.get('z', []),
                x=config.data.get('x', []),
                y=config.data.get('y', []),
                colorscale=config.custom_colors or 'RdYlBu_r'
            ))

        return fig

    def _create_candlestick_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create candlestick chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = go.Figure(data=go.Candlestick(
                x=config.data.index,
                open=config.data['Open'],
                high=config.data['High'],
                low=config.data['Low'],
                close=config.data['Close']
            ))
        else:
            # Handle dict data
            fig = go.Figure(data=go.Candlestick(
                x=config.data.get('x', []),
                open=config.data.get('open', []),
                high=config.data.get('high', []),
                low=config.data.get('low', []),
                close=config.data.get('close', [])
            ))

        fig.update_layout(
            title=config.title,
            width=config.width,
            height=config.height,
            **theme_config
        )

        return fig

    def _create_histogram_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create histogram chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = px.histogram(
                config.data,
                x=config.x_column,
                title=config.title,
                width=config.width,
                height=config.height,
                color_discrete_sequence=config.custom_colors or theme_config['colorway']
            )
        else:
            # Handle dict data
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=config.data.get('x', []),
                marker_color=config.custom_colors or theme_config['colorway'][0]
            ))

        return fig

    def _create_box_chart(self, config: ChartConfig, theme_config: Dict) -> go.Figure:
        """Create box chart"""
        if isinstance(config.data, pd.DataFrame):
            fig = px.box(
                config.data,
                y=config.y_column,
                x=config.x_column,
                title=config.title,
                width=config.width,
                height=config.height,
                color_discrete_sequence=config.custom_colors or theme_config['colorway']
            )
        else:
            # Handle dict data
            fig = go.Figure()
            fig.add_trace(go.Box(
                y=config.data.get('y', []),
                marker_color=config.custom_colors or theme_config['colorway'][0]
            ))

        return fig

    def create_dashboard(self, config: DashboardConfig) -> Dict[str, Any]:
        """Create dashboard configuration"""
        dashboard = {
            'title': config.title,
            'layout': config.layout,
            'theme': config.theme.value,
            'width': config.width,
            'height': config.height,
            'show_controls': config.show_controls,
            'auto_refresh': config.auto_refresh,
            'refresh_interval': config.refresh_interval,
            'charts': [],
            'created_at': datetime.now().isoformat()
        }

        # Create all charts
        for chart_config in config.charts:
            try:
                fig = self.create_chart(chart_config)
                chart_data = {
                    'config': chart_config.__dict__,
                    'plot_data': fig.to_dict(),
                    'html': fig.to_html(include_plotlyjs='cdn')
                }
                dashboard['charts'].append(chart_data)
            except Exception as e:
                logger.error(f"Failed to create chart {chart_config.title}: {e}")

        return dashboard

    def save_chart(self, fig: go.Figure, filename: str, format: str = 'html'):
        """Save chart to file"""
        try:
            if format.lower() == 'html':
                fig.write_html(filename)
            elif format.lower() == 'png':
                fig.write_image(filename)
            elif format.lower() == 'pdf':
                fig.write_image(filename)
            elif format.lower() == 'json':
                with open(filename, 'w') as f:
                    json.dump(fig.to_dict(), f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Chart saved to {filename}")

        except Exception as e:
            logger.error(f"Failed to save chart: {e}")
            raise

    def export_dashboard(self, dashboard: Dict[str, Any], filename: str):
        """Export dashboard to HTML file"""
        try:
            html_content = self._generate_dashboard_html(dashboard)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Dashboard exported to {filename}")

        except Exception as e:
            logger.error(f"Failed to export dashboard: {e}")
            raise

    def _generate_dashboard_html(self, dashboard: Dict[str, Any]) -> str:
        """Generate HTML for dashboard"""
        html_parts = [
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{dashboard['title']}</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .dashboard-header {{ text-align: center; margin-bottom: 30px; }}
                    .chart-container {{ margin-bottom: 30px; }}
                    .controls {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="dashboard-header">
                    <h1>{dashboard['title']}</h1>
                    <p>Generated on {dashboard['created_at']}</p>
                </div>
            """
        ]

        if dashboard['show_controls']:
            html_parts.append("""
                <div class="controls">
                    <button onclick="refreshDashboard()">Refresh</button>
                </div>
            """)

        for chart in dashboard['charts']:
            html_parts.append(f"""
                <div class="chart-container">
                    <h3>{chart['config']['title']}</h3>
                    <div id="chart-{hash(chart['config']['title'])}"></div>
                </div>
            """)

        html_parts.append("""
                <script>
                    function refreshDashboard() {
                        location.reload();
                    }
                </script>
            """)

        # Add individual chart scripts
        for chart in dashboard['charts']:
            chart_title = chart['config']['title']
            chart_id = f"chart-{hash(chart_title)}"
            plot_data = chart['plot_data']

            html_parts.append(f"""
                <script>
                    Plotly.newPlot('{chart_id}', {json.dumps(plot_data['data'])}, {json.dumps(plot_data['layout'])});
                </script>
            """)

        html_parts.append("""
            </body>
            </html>
        """)

        return '\n'.join(html_parts)

    def create_financial_dashboard(self, data: Dict[str, Any]) -> DashboardConfig:
        """Create a comprehensive financial dashboard"""
        charts = []

        # Price trend chart
        if 'price_data' in data:
            price_chart = ChartConfig(
                title="Price Trend",
                chart_type=ChartType.LINE,
                data=data['price_data'],
                x_column='Date',
                y_column='Close',
                theme=VisualizationTheme.FINANCIAL
            )
            charts.append(price_chart)

        # Financial ratios chart
        if 'financial_ratios' in data:
            ratios_chart = ChartConfig(
                title="Financial Ratios",
                chart_type=ChartType.BAR,
                data=data['financial_ratios'],
                x_column='ratio',
                y_column='value',
                theme=VisualizationTheme.FINANCIAL
            )
            charts.append(ratios_chart)

        # Portfolio allocation chart
        if 'portfolio_allocation' in data:
            allocation_chart = ChartConfig(
                title="Portfolio Allocation",
                chart_type=ChartType.PIE,
                data=data['portfolio_allocation'],
                x_column='asset',
                y_column='percentage',
                theme=VisualizationTheme.FINANCIAL
            )
            charts.append(allocation_chart)

        # Risk metrics chart
        if 'risk_metrics' in data:
            risk_chart = ChartConfig(
                title="Risk Metrics",
                chart_type=ChartType.BAR,
                data=data['risk_metrics'],
                x_column='metric',
                y_column='value',
                theme=VisualizationTheme.FINANCIAL
            )
            charts.append(risk_chart)

        return DashboardConfig(
            title="Financial Analysis Dashboard",
            charts=charts,
            theme=VisualizationTheme.FINANCIAL,
            width=1400,
            height=900
        )


# Global instances
_visualizer: Optional[Visualizer] = None


def get_visualizer(config: Dict[str, Any] = None) -> Visualizer:
    """Get or create the global visualizer instance"""
    global _visualizer
    if _visualizer is None:
        _visualizer = Visualizer(config)
    return _visualizer


def create_chart(config: ChartConfig) -> go.Figure:
    """Create a chart using the global visualizer"""
    visualizer = get_visualizer()
    return visualizer.create_chart(config)


def create_dashboard(config: DashboardConfig) -> Dict[str, Any]:
    """Create a dashboard using the global visualizer"""
    visualizer = get_visualizer()
    return visualizer.create_dashboard(config)


def save_chart(fig: go.Figure, filename: str, format: str = 'html'):
    """Save a chart using the global visualizer"""
    visualizer = get_visualizer()
    return visualizer.save_chart(fig, filename, format)


def export_dashboard(dashboard: Dict[str, Any], filename: str):
    """Export a dashboard using the global visualizer"""
    visualizer = get_visualizer()
    return visualizer.export_dashboard(dashboard, filename)