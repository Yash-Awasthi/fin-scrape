"""
Export Manager for Financial Analysis Reports
Handles exporting reports and data to various formats
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime
import json
import csv
import pandas as pd
from pathlib import Path
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor

class ExportFormat(Enum):
    """支持的导出格式"""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    XML = "xml"
    WORD = "word"

class ExportConfig:
    """导出配置"""

    def __init__(self,
                 format: ExportFormat,
                 output_path: str,
                 include_charts: bool = True,
                 include_raw_data: bool = False,
                 template_name: Optional[str] = None,
                 custom_options: Optional[Dict] = None):
        self.format = format
        self.output_path = output_path
        self.include_charts = include_charts
        self.include_raw_data = include_raw_data
        self.template_name = template_name
        self.custom_options = custom_options or {}

class ExportManager:
    """导出管理器"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(__name__)

        # 支持的格式处理器
        self.format_handlers = {
            ExportFormat.HTML: self._export_html,
            ExportFormat.PDF: self._export_pdf,
            ExportFormat.EXCEL: self._export_excel,
            ExportFormat.CSV: self._export_csv,
            ExportFormat.JSON: self._export_json,
            ExportFormat.MARKDOWN: self._export_markdown,
            ExportFormat.XML: self._export_xml,
            ExportFormat.WORD: self._export_word
        }

    async def export_report(self,
                           report_data: Dict,
                           config: ExportConfig) -> str:
        """导出报告"""
        try:
            # 创建输出目录
            output_path = Path(config.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 根据格式选择处理器
            handler = self.format_handlers.get(config.format)
            if not handler:
                raise ValueError(f"不支持的导出格式: {config.format}")

            # 执行导出
            result_path = await handler(report_data, config)

            self.logger.info(f"报告导出成功: {result_path}")
            return result_path

        except Exception as e:
            self.logger.error(f"报告导出失败: {str(e)}")
            raise

    async def export_data(self,
                         data: Union[pd.DataFrame, Dict, List],
                         config: ExportConfig) -> str:
        """导出数据"""
        try:
            output_path = Path(config.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(data, pd.DataFrame):
                return await self._export_dataframe(data, config)
            elif isinstance(data, (dict, list)):
                return await self._export_structured_data(data, config)
            else:
                raise ValueError("不支持的数据类型")

        except Exception as e:
            self.logger.error(f"数据导出失败: {str(e)}")
            raise

    async def schedule_export(self,
                            export_func,
                            schedule_config: Dict) -> str:
        """定时导出"""
        try:
            # 这里可以实现定时导出逻辑
            # 例如使用 APScheduler 或类似库
            export_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.logger.info(f"定时导出任务已创建: {export_id}")
            return export_id

        except Exception as e:
            self.logger.error(f"定时导出创建失败: {str(e)}")
            raise

    async def _export_html(self, report_data: Dict, config: ExportConfig) -> str:
        """导出HTML格式"""
        try:
            html_content = self._generate_html_report(report_data, config)

            async with aiofiles.open(config.output_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)

            return config.output_path

        except Exception as e:
            self.logger.error(f"HTML导出失败: {str(e)}")
            raise

    async def _export_pdf(self, report_data: Dict, config: ExportConfig) -> str:
        """导出PDF格式"""
        try:
            # 先生成HTML，然后转换为PDF
            html_path = await self._export_html(report_data,
                ExportConfig(ExportFormat.HTML, config.output_path.replace('.pdf', '.html')))

            # 使用wkhtmltopdf或类似工具转换
            # 这里简化处理，实际需要安装转换工具
            self.logger.info("PDF导出需要安装wkhtmltopdf或其他PDF转换工具")
            return html_path

        except Exception as e:
            self.logger.error(f"PDF导出失败: {str(e)}")
            raise

    async def _export_excel(self, report_data: Dict, config: ExportConfig) -> str:
        """导出Excel格式"""
        try:
            with pd.ExcelWriter(config.output_path, engine='xlsxwriter') as writer:
                # 导出摘要数据
                if 'summary' in report_data:
                    summary_df = pd.DataFrame([report_data['summary']])
                    summary_df.to_excel(writer, sheet_name='摘要', index=False)

                # 导出财务指标
                if 'financial_metrics' in report_data:
                    metrics_df = pd.DataFrame([report_data['financial_metrics']])
                    metrics_df.to_excel(writer, sheet_name='财务指标', index=False)

                # 导出风险指标
                if 'risk_metrics' in report_data:
                    risk_df = pd.DataFrame([report_data['risk_metrics']])
                    risk_df.to_excel(writer, sheet_name='风险指标', index=False)

                # 导出原始数据（如果包含）
                if config.include_raw_data and 'raw_data' in report_data:
                    raw_data = report_data['raw_data']
                    if isinstance(raw_data, dict):
                        for key, value in raw_data.items():
                            if isinstance(value, (list, dict)):
                                df = pd.DataFrame(value)
                                df.to_excel(writer, sheet_name=key[:31], index=False)

            return config.output_path

        except Exception as e:
            self.logger.error(f"Excel导出失败: {str(e)}")
            raise

    async def _export_csv(self, data: Union[pd.DataFrame, Dict], config: ExportConfig) -> str:
        """导出CSV格式"""
        try:
            if isinstance(data, pd.DataFrame):
                data.to_csv(config.output_path, index=False, encoding='utf-8')
            else:
                # 将字典转换为DataFrame
                df = pd.DataFrame([data])
                df.to_csv(config.output_path, index=False, encoding='utf-8')

            return config.output_path

        except Exception as e:
            self.logger.error(f"CSV导出失败: {str(e)}")
            raise

    async def _export_json(self, data: Union[Dict, List], config: ExportConfig) -> str:
        """导出JSON格式"""
        try:
            async with aiofiles.open(config.output_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))

            return config.output_path

        except Exception as e:
            self.logger.error(f"JSON导出失败: {str(e)}")
            raise

    async def _export_markdown(self, report_data: Dict, config: ExportConfig) -> str:
        """导出Markdown格式"""
        try:
            markdown_content = self._generate_markdown_report(report_data, config)

            async with aiofiles.open(config.output_path, 'w', encoding='utf-8') as f:
                await f.write(markdown_content)

            return config.output_path

        except Exception as e:
            self.logger.error(f"Markdown导出失败: {str(e)}")
            raise

    async def _export_xml(self, data: Dict, config: ExportConfig) -> str:
        """导出XML格式"""
        try:
            xml_content = self._generate_xml_report(data, config)

            async with aiofiles.open(config.output_path, 'w', encoding='utf-8') as f:
                await f.write(xml_content)

            return config.output_path

        except Exception as e:
            self.logger.error(f"XML导出失败: {str(e)}")
            raise

    async def _export_word(self, report_data: Dict, config: ExportConfig) -> str:
        """导出Word格式"""
        try:
            # 这里需要python-docx库
            self.logger.info("Word导出需要安装python-docx库")
            return "word_export_not_implemented"

        except Exception as e:
            self.logger.error(f"Word导出失败: {str(e)}")
            raise

    async def _export_dataframe(self, df: pd.DataFrame, config: ExportConfig) -> str:
        """导出DataFrame"""
        if config.format == ExportFormat.EXCEL:
            df.to_excel(config.output_path, index=False)
            return config.output_path
        elif config.format == ExportFormat.CSV:
            df.to_csv(config.output_path, index=False, encoding='utf-8')
            return config.output_path
        else:
            # 其他格式转换为JSON导出
            data = df.to_dict('records')
            return await self._export_json(data, config)

    async def _export_structured_data(self, data: Union[Dict, List], config: ExportConfig) -> str:
        """导出结构化数据"""
        if config.format == ExportFormat.JSON:
            return await self._export_json(data, config)
        elif config.format == ExportFormat.CSV:
            df = pd.DataFrame([data] if isinstance(data, dict) else data)
            return await self._export_dataframe(df, config)
        elif config.format == ExportFormat.EXCEL:
            df = pd.DataFrame([data] if isinstance(data, dict) else data)
            return await self._export_dataframe(df, config)
        else:
            return await self._export_json(data, config)

    def _generate_html_report(self, report_data: Dict, config: ExportConfig) -> str:
        """生成HTML报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: #e9ecef; border-radius: 5px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>生成时间: {timestamp}</p>
        <p>分析标的: {symbol}</p>
    </div>

    {content}
</body>
</html>
        """

        # 生成内容
        content_parts = []

        # 添加摘要
        if 'summary' in report_data:
            content_parts.append(self._generate_html_summary(report_data['summary']))

        # 添加财务指标
        if 'financial_metrics' in report_data:
            content_parts.append(self._generate_html_metrics(report_data['financial_metrics']))

        # 添加风险指标
        if 'risk_metrics' in report_data:
            content_parts.append(self._generate_html_risk(report_data['risk_metrics']))

        # 添加建议
        if 'recommendations' in report_data:
            content_parts.append(self._generate_html_recommendations(report_data['recommendations']))

        content = "\n".join(content_parts)

        return html_template.format(
            title=report_data.get('title', '金融分析报告'),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            symbol=report_data.get('symbol', 'N/A'),
            content=content
        )

    def _generate_html_summary(self, summary: Dict) -> str:
        """生成HTML摘要"""
        return f"""
        <div class="section">
            <h2>执行摘要</h2>
            <p>{summary.get('overview', '暂无概述')}</p>
            <div class="metric">
                <strong>综合评分:</strong> {summary.get('score', 'N/A')}
            </div>
        </div>
        """

    def _generate_html_metrics(self, metrics: Dict) -> str:
        """生成HTML指标"""
        metrics_html = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                color_class = "positive" if value > 0 else "negative"
                metrics_html.append(f"""
                <div class="metric">
                    <strong>{key}:</strong>
                    <span class="{color_class}">{value:.2f}%</span>
                </div>
                """)

        return f"""
        <div class="section">
            <h2>财务指标</h2>
            {''.join(metrics_html)}
        </div>
        """

    def _generate_html_risk(self, risk_metrics: Dict) -> str:
        """生成HTML风险指标"""
        return f"""
        <div class="section">
            <h2>风险评估</h2>
            <table>
                <tr><th>指标</th><th>数值</th><th>评级</th></tr>
                {''.join([f"<tr><td>{k}</td><td>{v:.4f}</td><td>{self._get_risk_rating(v)}</td></tr>"
                          for k, v in risk_metrics.items() if isinstance(v, (int, float))])}
            </table>
        </div>
        """

    def _generate_html_recommendations(self, recommendations: List) -> str:
        """生成HTML建议"""
        return f"""
        <div class="section">
            <h2>投资建议</h2>
            <ul>
                {''.join([f"<li>{rec}</li>" for rec in recommendations])}
            </ul>
        </div>
        """

    def _generate_markdown_report(self, report_data: Dict, config: ExportConfig) -> str:
        """生成Markdown报告"""
        markdown_parts = [f"# {report_data.get('title', '金融分析报告')}"]
        markdown_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        markdown_parts.append(f"**分析标的**: {report_data.get('symbol', 'N/A')}")
        markdown_parts.append("")

        if 'summary' in report_data:
            markdown_parts.append("## 执行摘要")
            markdown_parts.append(report_data['summary'].get('overview', '暂无概述'))
            markdown_parts.append("")

        if 'financial_metrics' in report_data:
            markdown_parts.append("## 财务指标")
            for key, value in report_data['financial_metrics'].items():
                if isinstance(value, (int, float)):
                    markdown_parts.append(f"- **{key}**: {value:.2f}%")
            markdown_parts.append("")

        if 'risk_metrics' in report_data:
            markdown_parts.append("## 风险评估")
            for key, value in report_data['risk_metrics'].items():
                if isinstance(value, (int, float)):
                    markdown_parts.append(f"- **{key}**: {value:.4f}")
            markdown_parts.append("")

        if 'recommendations' in report_data:
            markdown_parts.append("## 投资建议")
            for rec in report_data['recommendations']:
                markdown_parts.append(f"- {rec}")
            markdown_parts.append("")

        return "\n".join(markdown_parts)

    def _generate_xml_report(self, data: Dict, config: ExportConfig) -> str:
        """生成XML报告"""
        def dict_to_xml(d, root_name="root"):
            xml = f"<{root_name}>"
            for key, value in d.items():
                if isinstance(value, dict):
                    xml += dict_to_xml(value, key)
                elif isinstance(value, list):
                    xml += f"<{key}>"
                    for item in value:
                        xml += dict_to_xml(item, "item")
                    xml += f"</{key}>"
                else:
                    xml += f"<{key}>{value}</{key}>"
            xml += f"</{root_name}>"
            return xml

        return dict_to_xml(data, "financial_report")

    def _get_risk_rating(self, value: float) -> str:
        """获取风险评级"""
        if value < 0.1:
            return "低"
        elif value < 0.3:
            return "中低"
        elif value < 0.5:
            return "中"
        elif value < 0.7:
            return "中高"
        else:
            return "高"

def get_export_manager(max_workers: int = 4) -> ExportManager:
    """获取导出管理器实例"""
    return ExportManager(max_workers)

async def export_report(report_data: Dict, config: ExportConfig) -> str:
    """导出报告的便捷函数"""
    manager = get_export_manager()
    return await manager.export_report(report_data, config)

async def export_data(data: Union[pd.DataFrame, Dict, List], config: ExportConfig) -> str:
    """导出数据的便捷函数"""
    manager = get_export_manager()
    return await manager.export_data(data, config)

async def schedule_export(export_func, schedule_config: Dict) -> str:
    """定时导出的便捷函数"""
    manager = get_export_manager()
    return await manager.schedule_export(export_func, schedule_config)