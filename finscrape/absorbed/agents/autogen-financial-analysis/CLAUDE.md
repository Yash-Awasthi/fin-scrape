# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a comprehensive AutoGen-based financial analysis system. The main content is a detailed Chinese language text file (`AutoGen_demo.txt`) that demonstrates enterprise-level financial data analysis workflows using Microsoft's AutoGen framework.

## Key Components

### Core Architecture
- **Multi-Agent System**: The code implements a sophisticated multi-agent architecture with specialized agents for:
  - Data collection (Yahoo Finance, Alpha Vantage, Quandl)
  - Financial analysis (ratio calculations, DuPont analysis)
  - Risk assessment (VaR, stress testing, scenario analysis)
  - Quantitative analysis (factor models, portfolio optimization)
  - Report generation

### Technical Stack
- **Primary Language**: Python with comprehensive async/await patterns
- **Key Libraries**:
  - `autogen` - Microsoft's AutoGen framework
  - `pandas`, `numpy` - Data analysis and numerical computing
  - `yfinance` - Financial data retrieval
  - `scikit-learn`, `scipy` - Statistical analysis and machine learning
  - `plotly` - Data visualization
  - `aiohttp`, `asyncio` - Asynchronous operations
  - `redis` - Caching layer
  - `sqlalchemy` - Database operations

### Main Classes and Functions

1. **Agent Architecture**:
   - `FinancialAgentFactory` - Creates specialized analysis agents
   - `AgentOrchestrator` - Manages agent workflows
   - `EnterpriseAutoGenConfig` - Enterprise-level configuration

2. **Data Processing**:
   - `EnterpriseDataCollector` - Multi-source data collection with caching
   - `DataSource` - Abstract base class for data sources
   - `DataCacheManager` - Redis-based caching system

3. **Analysis Engines**:
   - `AdvancedFinancialAnalyzer` - Comprehensive financial metrics calculation
   - `AdvancedRiskAnalyzer` - Risk metrics and stress testing
   - `QuantitativeAnalyzer` - Factor models and portfolio optimization

4. **Supporting Infrastructure**:
   - `PerformanceOptimizer` - Async performance optimization
   - `SystemMonitor` - Prometheus-based monitoring
   - `SecurityManager` - Data encryption and security
   - `ErrorHandler` - Advanced error handling with retry logic

## Development Commands

This is a documentation/learning project with no build system. Key commands for development:

```bash
# Install dependencies
pip install autogen pandas numpy yfinance scikit-learn scipy plotly aiohttp redis sqlalchemy

# Run analysis examples
python -c "from autogen_demo import execute_enterprise_analysis; asyncio.run(execute_enterprise_analysis('AAPL', api_keys))"
```

## Code Architecture Notes

### Design Patterns
- **Factory Pattern**: Used extensively for creating specialized agents
- **Strategy Pattern**: Different data sources and analysis strategies
- **Observer Pattern**: Configuration management and monitoring
- **Decorator Pattern**: Request tracking and error handling

### Key Features
- **Async-First Design**: All I/O operations use async/await for performance
- **Multi-Source Data Integration**: Supports multiple financial data APIs
- **Enterprise-Grade Error Handling**: Comprehensive error recovery and logging
- **Performance Optimization**: Caching, rate limiting, and parallel processing
- **Security Focus**: Data encryption, access control, and input validation

### Code Style
- Follows Python best practices with comprehensive type hints
- Extensive use of dataclasses for structured data
- Comprehensive logging and error handling
- Modular design with clear separation of concerns

## Working with This Codebase

1. **Understanding the Content**: The main file is a comprehensive tutorial in Chinese covering AutoGen applications in financial analysis
2. **Code Examples**: Contains numerous production-ready code examples for financial data processing
3. **Scalability**: The architecture is designed for enterprise-scale deployments
4. **Extensibility**: Modular design allows easy addition of new data sources and analysis methods

## Important Considerations

- This is educational content demonstrating advanced AutoGen applications
- The code requires API keys for various financial data services
- Some implementation details are simplified for educational purposes
- Production deployment would require additional security and compliance measures