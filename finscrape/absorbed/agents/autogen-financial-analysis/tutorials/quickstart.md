# AutoGen金融分析系统快速入门

## 1. 概述

欢迎使用AutoGen金融分析系统！本教程将帮助您快速了解系统的基本功能和使用方法，让您能够在短时间内开始使用系统进行金融分析。

## 2. 系统安装

在开始之前，您需要先安装AutoGen金融分析系统。如果您还没有安装，请按照以下步骤操作：

### 2.1 克隆项目代码

```bash
git clone https://github.com/your-username/autogen-financial-analysis.git
cd autogen-financial-analysis
```

### 2.2 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

### 2.4 配置环境变量

```bash
cp .env.example .env
# 使用文本编辑器打开.env文件，添加必要的配置
```

## 3. 快速开始：命令行方式

### 3.1 分析单个公司

使用系统分析单个公司是最基本的功能。以下示例展示如何分析苹果公司（AAPL）：

```bash
python -m src.main analyze AAPL
```

运行上述命令后，系统将自动从各种数据源收集AAPL的金融数据，进行综合分析，并生成分析报告。

分析完成后，您将看到类似以下输出：

```
分析完成: AAPL
综合评分: 85
评级: 买入
```

### 3.2 指定分析类型

系统支持三种不同的分析深度：`quick`（快速）、`comprehensive`（综合）和`detailed`（详细）。您可以使用`--type`参数指定分析类型：

```bash
# 快速分析（仅包含基本指标）
python -m src.main analyze AAPL --type quick

# 综合分析（包含详细的财务和风险分析）
python -m src.main analyze AAPL --type comprehensive

# 详细分析（包含所有可用指标和深入分析）
python -m src.main analyze AAPL --type detailed
```

### 3.3 导出分析报告

您可以将分析结果导出为多种格式，包括HTML、PDF、JSON和CSV：

```bash
python -m src.main analyze AAPL --export html,pdf,json
```

导出的报告将保存在`output/`目录下，您可以使用相应的应用程序打开查看。

### 3.4 分析投资组合

系统还支持分析多个股票组成的投资组合：

```bash
python -m src.main portfolio AAPL MSFT GOOG
```

这将分析苹果、微软和谷歌三只股票组成的投资组合，并提供投资组合级别的分析指标，如预期收益率、风险、夏普比率等。

您还可以为投资组合中的股票设置权重：

```bash
python -m src.main portfolio AAPL MSFT GOOG --weights AAPL=0.5,MSFT=0.3,GOOG=0.2
```

### 3.5 量化分析

系统提供强大的量化分析功能：

```bash
# 对单个股票进行量化分析
python -m src.main quant AAPL

# 使用特定因子进行分析
python -m src.main quant AAPL --factors momentum value growth

# 使用特定因子模型
python -m src.main quant AAPL --method carhart

# 导出量化分析报告
python -m src.main quant AAPL --export html,pdf,json
```

### 3.6 策略回测

您可以对量化策略进行历史回测：

```bash
# 运行动量策略回测
python -m src.main backtest --strategy momentum --start-date 2020-01-01 --end-date 2023-01-01

# 设置回测参数
python -m src.main backtest --strategy momentum --start-date 2020-01-01 --end-date 2023-01-01 --initial-capital 100000 --commission 0.001

# 导出回测报告
python -m src.main backtest --strategy momentum --start-date 2020-01-01 --end-date 2023-01-01 --export html,pdf
```

### 3.7 策略优化

优化量化策略参数：

```bash
# 优化策略参数
python -m src.main optimize --strategy momentum --param window=5,10,15,20

# 设置优化时间范围
python -m src.main optimize --strategy momentum --param window=5,10,15,20 --start-date 2020-01-01 --end-date 2023-01-01
```

### 3.8 投资组合优化

优化投资组合权重：

```bash
# 使用均值-方差优化方法
python -m src.main optimize-portfolio --symbols AAPL MSFT GOOG --method mean_variance

# 使用风险平价优化方法
python -m src.main optimize-portfolio --symbols AAPL MSFT GOOG --method risk_parity

# 设置风险厌恶系数
python -m src.main optimize-portfolio --symbols AAPL MSFT GOOG --method mean_variance --risk-aversion 1.5
```

## 4. 快速开始：Web界面方式

### 4.1 启动Web服务

首先，您需要启动系统的Web服务：

```bash
python -m src.api.app
```

启动成功后，您将看到类似以下输出：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 4.2 访问Web界面

打开您的浏览器，访问 `http://localhost:8000`，您将看到系统的Web界面。

### 4.3 使用Web界面进行分析

#### 4.3.1 公司分析

1. 在左侧导航栏中，点击"分析模块" -> "公司分析"
2. 在输入框中输入股票代码（例如：AAPL）
3. 选择分析类型（快速、综合或详细）
4. 选择要导出的报告格式（可选）
5. 点击"开始分析"按钮

系统将开始分析，并显示进度。分析完成后，您可以查看分析结果和下载报告。

#### 4.3.2 投资组合分析

1. 在左侧导航栏中，点击"分析模块" -> "投资组合分析"
2. 点击"添加股票"按钮，输入股票代码并设置权重（可选）
3. 重复步骤2，添加多个股票
4. 选择分析类型
5. 选择要导出的报告格式（可选）
6. 点击"开始分析"按钮

### 4.3.3 量化分析

1. 在左侧导航栏中，点击"分析模块" -> "量化分析"
2. 输入股票代码或选择投资组合
3. 选择分析因子和模型方法
4. 选择要导出的报告格式（可选）
5. 点击"开始分析"按钮

### 4.3.4 策略回测

1. 在左侧导航栏中，点击"分析模块" -> "策略回测"
2. 选择策略类型和回测参数
3. 设置回测时间范围和初始资金
4. 选择要导出的报告格式（可选）
5. 点击"开始回测"按钮

### 4.3.5 投资组合优化

1. 在左侧导航栏中，点击"分析模块" -> "投资组合优化"
2. 添加股票代码
3. 选择优化方法和参数
4. 选择要导出的报告格式（可选）
5. 点击"开始优化"按钮

## 5. 查看分析报告

### 5.1 命令行方式

分析完成后，报告将保存在`output/`目录下。您可以直接打开这些文件查看详细的分析结果。

### 5.2 Web界面方式

在Web界面中，您可以通过以下方式查看报告：

1. 在左侧导航栏中，点击"报告中心"
2. 您将看到所有已生成的报告列表
3. 点击报告名称查看详细内容
4. 使用报告页面上的下载按钮下载报告文件

## 6. 示例：分析苹果公司股票

让我们通过一个具体的示例来了解如何使用系统分析苹果公司（AAPL）的股票。

### 6.1 命令行分析

运行以下命令开始分析：

```bash
python -m src.main analyze AAPL --type comprehensive --export html,pdf
```

### 6.2 分析结果解读

分析完成后，您将看到类似以下输出：

```
分析完成: AAPL
综合评分: 85
评级: 买入
```

这表示系统对苹果公司的综合评分为85分，评级为"买入"。

### 6.3 详细报告查看

打开`output/`目录下的HTML或PDF报告，您将看到详细的分析结果，包括：

- **公司概览**: 基本信息、行业地位、竞争优势等
- **财务分析**: 盈利能力、偿债能力、运营效率、成长性等指标
- **风险评估**: 市场风险、信用风险、流动性风险等评估
- **投资建议**: 基于分析结果的投资建议和风险提示
- **图表分析**: 各种财务指标和股价走势的图表展示

## 7. 示例：分析投资组合

接下来，让我们分析一个由苹果（AAPL）、微软（MSFT）和谷歌（GOOG）组成的投资组合。

### 7.1 命令行分析

运行以下命令开始分析：

```bash
python -m src.main portfolio AAPL MSFT GOOG --weights AAPL=0.5,MSFT=0.3,GOOG=0.2 --export html
```

### 7.2 投资组合分析结果解读

分析完成后，您将看到类似以下输出：

```
投资组合分析完成: AAPL, MSFT, GOOG
预期收益率: 12.5%
```

### 7.3 详细报告查看

打开`output/`目录下的HTML报告，您将看到详细的投资组合分析结果，包括：

- **投资组合概览**: 组合构成、权重分配等
- **风险收益分析**: 预期收益率、波动率、夏普比率等
- **资产配置分析**: 行业分布、地区分布等
- **风险贡献分析**: 各资产对组合风险的贡献度
- **优化建议**: 基于分析结果的投资组合优化建议

## 8. 示例：量化分析

接下来，让我们对苹果公司（AAPL）进行量化分析。

### 8.1 命令行分析

运行以下命令开始分析：

```bash
python -m src.main quant AAPL --factors momentum value growth --method fama_french --export html,pdf
```

### 8.2 量化分析结果解读

分析完成后，您将看到类似以下输出：

```
量化分析完成: AAPL
预期收益率: 15.2%
投资组合风险: 18.5%
夏普比率: 0.82
```

### 8.3 详细报告查看

打开`output/`目录下的HTML或PDF报告，您将看到详细的量化分析结果，包括：

- **因子分析**: 各量化因子的暴露和显著性
- **投资组合优化**: 最优权重配置和风险调整收益
- **回测结果**: 策略历史表现和绩效指标
- **风险分析**: 各种风险度量和压力测试结果

## 9. 使用API接口

如果您希望将系统集成到其他应用程序中，可以使用系统提供的RESTful API接口。

### 9.1 创建分析任务

```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "analysis_type": "comprehensive",
    "export_formats": ["html", "pdf"]
  }'
```

### 9.2 查看任务状态

```bash
# 替换{task_id}为实际的任务ID
curl -X GET "http://localhost:8000/api/v1/analysis/{task_id}"
```

## 10. 常见问题解决

### 10.1 数据源连接问题

如果您遇到数据源连接问题，请检查：

- 您的网络连接是否正常
- `.env`文件中的API密钥是否正确
- 您的API密钥是否有足够的配额

### 10.2 分析结果不准确

如果您认为分析结果不准确，请考虑：

- 使用`--type detailed`参数进行更详细的分析
- 检查您输入的股票代码是否正确
- 注意系统提示的任何数据质量问题

### 10.3 系统性能问题

如果系统运行缓慢，您可以：

- 使用`--use-cache`参数利用缓存数据
- 对于大型投资组合，减少分析的股票数量
- 对于开发环境，关闭不必要的监控功能

## 11. 下一步学习

完成本快速入门教程后，您可以继续学习以下内容：

- [财务分析教程](financial-analysis.md): 深入了解系统的财务分析功能
- [风险评估教程](risk-assessment.md): 学习如何使用系统进行风险评估
- [量化分析教程](quantitative-analysis.md): 探索系统的量化分析功能
- [用户手册](../docs/user-manual.md): 系统功能的详细说明
- [API文档](../docs/api-documentation.md): API接口的详细说明

---

**注意**: 本系统仅供学习和研究使用，不构成投资建议。投资有风险，请谨慎决策。