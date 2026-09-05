# AutoGen金融分析系统用户手册

## 1. 系统简介

AutoGen金融分析系统是一个基于微软AutoGen框架的企业级金融分析平台，通过多Agent架构提供全面的财务分析、风险评估和量化投资分析功能。本手册将帮助您快速上手并充分利用系统的各项功能。

## 2. 系统要求

- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+, CentOS 8+)
- **Python版本**: 3.8或更高版本
- **数据库**: Redis 6.0+, PostgreSQL 12+
- **浏览器**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **内存要求**: 至少4GB RAM，推荐8GB或更多
- **硬盘空间**: 至少10GB可用空间

## 3. 安装与配置

### 3.1 快速安装

1. **克隆项目代码**
   ```bash
   git clone https://github.com/your-username/autogen-financial-analysis.git
   cd autogen-financial-analysis
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖包**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 使用文本编辑器打开.env文件，添加必要的API密钥
   ```

### 3.2 Docker部署

如果您希望使用Docker部署系统，可以按照以下步骤操作：

```bash
# 构建并启动所有服务
 docker-compose up -d

# 查看服务状态
 docker-compose ps

# 查看日志
 docker-compose logs -f
```

### 3.3 配置文件说明

系统的主要配置文件为`config.yaml`，您可以根据需要进行修改：

```yaml
# AutoGen配置
autogen:
  gpt_model: "gpt-4"
  temperature: 0.7
  max_tokens: 4000

# 数据源配置
data_sources:
  yahoo_finance:
    timeout: 30
    retry_count: 3
  alpha_vantage:
    api_key: "${ALPHA_VANTAGE_API_KEY}"
    calls_per_minute: 5
```

## 4. 系统界面

### 4.1 命令行界面

系统提供了功能强大的命令行界面，您可以通过以下命令使用系统的各项功能：

#### 基本用法
```bash
# 分析单个公司
python -m src.main analyze AAPL

# 分析投资组合
python -m src.main portfolio AAPL MSFT GOOG

# 交互模式
python -m src.main interactive
```

#### 高级选项
```bash
# 指定分析类型
python -m src.main analyze AAPL --type comprehensive

# 导出报告
python -m src.main analyze AAPL --format html,pdf

# 自定义配置
python -m src.main analyze AAPL --config custom_config.yaml
```

### 4.2 Web界面

系统还提供了友好的Web界面，您可以通过以下步骤访问：

1. 启动Web服务
   ```bash
   python -m src.api.app
   ```

2. 在浏览器中访问 `http://localhost:8000`

Web界面主要包括以下几个部分：
- **仪表盘**: 显示系统概览和常用功能
- **分析模块**: 进行公司分析和投资组合分析
- **报告中心**: 查看和管理生成的分析报告
- **系统设置**: 配置系统参数

## 5. 功能使用指南

### 5.1 公司分析

公司分析功能允许您深入了解单个公司的财务状况、风险水平和投资价值。

#### 使用方法
1. 在命令行中运行：
   ```bash
   python -m src.main analyze [股票代码] [选项]
   ```

2. 或在Web界面中，导航至"分析模块" -> "公司分析"，输入股票代码并点击"开始分析"。

#### 分析类型
- **快速分析 (quick)**: 提供基本的财务指标和风险评估
- **综合分析 (comprehensive)**: 提供全面的财务分析、风险评估和投资建议
- **详细分析 (detailed)**: 包含所有可用指标和深度分析

### 5.2 投资组合分析

投资组合分析功能帮助您评估一组股票的整体表现、风险水平和优化潜力。

#### 使用方法
1. 在命令行中运行：
   ```bash
   python -m src.main portfolio [股票代码1] [股票代码2] ... [选项]
   ```

2. 或在Web界面中，导航至"分析模块" -> "投资组合分析"，添加股票并设置权重（可选），然后点击"开始分析"。

#### 设置权重
您可以通过`--weights`参数为投资组合中的股票设置权重：
```bash
python -m src.main portfolio AAPL MSFT GOOG --weights AAPL=0.5,MSFT=0.3,GOOG=0.2
```

### 5.3 报告导出

系统支持将分析结果导出为多种格式，方便您分享和存档。

#### 支持的格式
- HTML: 适合在浏览器中查看，包含交互式图表
- PDF: 适合打印和存档
- JSON: 适合与其他系统集成
- CSV: 适合数据导入和进一步分析

#### 导出方法
```bash
python -m src.main analyze AAPL --format html,pdf,json
```

## 6. 报告解读

系统生成的报告包含丰富的分析指标和图表，下面介绍一些关键指标的解读方法。

### 6.1 财务分析报告

- **盈利能力指标**
  - **ROE (净资产收益率)**: 衡量公司利用股东权益创造利润的能力，越高越好
  - **ROA (资产收益率)**: 衡量公司利用总资产创造利润的能力
  - **毛利率**: 衡量公司产品或服务的盈利能力
  - **净利率**: 衡量公司最终盈利能力

- **偿债能力指标**
  - **资产负债率**: 衡量公司的长期偿债能力，越低风险越小
  - **流动比率**: 衡量公司的短期偿债能力，通常应大于1
  - **速动比率**: 更严格的短期偿债能力指标，通常应大于0.5

- **运营效率指标**
  - **总资产周转率**: 衡量公司资产的使用效率
  - **存货周转率**: 衡量公司存货管理效率

### 6.2 风险评估报告

- **市场风险指标**
  - **VaR (在险价值)**: 在给定置信水平下，特定时间段内可能发生的最大损失
  - **CVaR (条件在险价值)**: 超过VaR阈值时的预期损失
  - **Beta系数**: 衡量股票相对于市场的波动性

- **信用风险指标**
  - **Z-Score**: 预测公司破产风险的指标
  - **Altman模型**: 更复杂的破产预测模型

### 6.3 投资组合分析报告

- **有效前沿**: 显示在给定风险水平下可以获得的最高预期收益
- **夏普比率**: 衡量风险调整后收益，越高越好
- **最大回撤**: 衡量投资组合的历史最大损失
- **相关系数**: 显示资产之间的相关性，低相关性有助于分散风险

## 7. API接口使用

系统提供了RESTful API接口，方便与其他系统集成。

### 7.1 创建分析任务

```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "analysis_type": "comprehensive",
    "export_formats": ["html", "pdf"]
  }'
```

### 7.2 查看任务状态

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/{task_id}"
```

### 7.3 WebSocket实时更新

系统还提供了WebSocket接口，用于获取分析任务的实时更新：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('任务更新:', data);
};
```

## 8. 常见问题解答

**Q: 如何获取API密钥？**
A: 请访问各数据源官方网站申请API密钥，例如Yahoo Finance、Alpha Vantage等。

**Q: 系统支持哪些股票市场？**
A: 目前支持美股、A股、港股等主要市场。

**Q: 如何提高分析速度？**
A: 您可以确保Redis缓存服务正在运行，系统会自动利用缓存数据来显著提高分析速度。

**Q: 分析结果的准确性如何？**
A: 系统基于公开的财务数据和市场数据进行分析，结果仅供参考，不构成投资建议。

**Q: 如何处理分析失败的情况？**
A: 如果分析失败，系统会生成详细的错误日志，请检查日志并根据提示解决问题。常见的问题包括数据源连接问题、API密钥无效或股票代码错误等。

## 9. 联系与支持

如果您在使用过程中遇到问题或有任何建议，请通过以下方式联系我们：

- GitHub Issues: [问题反馈](https://github.com/your-username/autogen-financial-analysis/issues)
- 邮件支持: support@example.com
- 文档中心: [在线文档](https://docs.autogen-financial.com)

---

**注意**: 本系统仅供学习和研究使用，不构成投资建议。投资有风险，请谨慎决策。