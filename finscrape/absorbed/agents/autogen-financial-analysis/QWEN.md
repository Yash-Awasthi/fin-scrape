# AutoGen Financial Analysis System - Project Context

## Project Overview

This is an enterprise-grade financial analysis system built with Microsoft's AutoGen framework. The system uses a multi-agent architecture to provide comprehensive financial analysis, risk assessment, and quantitative investment analysis capabilities.

### Key Features

- **Multi-source Data Collection**: Integrates data from Yahoo Finance, Alpha Vantage, and Quandl
- **Intelligent Financial Analysis**: Multi-agent collaborative analysis based on AutoGen
- **Risk Assessment**: VaR calculation, stress testing, Monte Carlo simulation
- **Quantitative Analysis**: Factor models, portfolio optimization, machine learning predictions
- **Real-time Monitoring**: System performance monitoring and alerting
- **Data Visualization**: Interactive charts and report generation

### Technology Stack

- **Core**: Python 3.8+, AutoGen framework
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Financial Data**: yfinance, alpha-vantage
- **Async and Web**: FastAPI, Uvicorn, aiohttp
- **Data Storage**: PostgreSQL, Redis
- **Monitoring**: Prometheus, Grafana
- **Security**: Cryptography, JWT, RBAC

## Project Structure

```
autogen-financial-analysis/
├── src/                 # Source code
│   ├── agents/          # AutoGen agents
│   ├── analysis/        # Financial analysis modules
│   ├── api/             # REST API and WebSocket
│   ├── cache/           # Cache management
│   ├── config/          # Configuration management
│   ├── data/            # Data collection and processing
│   ├── monitoring/      # System monitoring
│   ├── performance/     # Performance management
│   ├── quant/           # Quantitative analysis
│   ├── reports/         # Report generation and visualization
│   ├── security/        # Security management
│   └── main.py          # Main application entry
├── tests/               # Test cases
├── docs/                # Documentation
├── web/                 # Web interface
├── k8s/                 # Kubernetes deployment files
├── requirements.txt     # Python dependencies
├── config.yaml          # Main configuration
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Docker build file
├── nginx.conf           # Nginx configuration
└── prometheus.yml       # Prometheus configuration
```

## Building and Running

### Development Environment

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/your-username/autogen-financial-analysis.git
   cd autogen-financial-analysis
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env file to add necessary API keys
   ```

2. **Run Development Server**:
   ```bash
   python -m src.api.app --reload
   ```

3. **Start Dependencies**:
   ```bash
   redis-server
   sudo systemctl start postgresql
   ```

### Docker Deployment

1. **Build and Start All Services**:
   ```bash
   docker-compose up -d
   ```

2. **View Service Status**:
   ```bash
   docker-compose ps
   ```

3. **View Logs**:
   ```bash
   docker-compose logs -f
   ```

### Kubernetes Deployment

1. **Deploy to K8s**:
   ```bash
   kubectl apply -f k8s/
   ```

2. **View Deployment Status**:
   ```bash
   kubectl get pods -n autogen-financial
   ```

## CLI Usage

### Basic Commands

1. **Analyze Single Company**:
   ```bash
   python -m src.main analyze AAPL
   ```

2. **Analyze Portfolio**:
   ```bash
   python -m src.main portfolio AAPL MSFT GOOG
   ```

3. **Interactive Mode**:
   ```bash
   python -m src.main interactive
   ```

### Advanced Options

1. **Specify Analysis Type**:
   ```bash
   python -m src.main analyze AAPL --type comprehensive
   ```

2. **Export Report**:
   ```bash
   python -m src.main analyze AAPL --export html,pdf
   ```

3. **Use Cache**:
   ```bash
   python -m src.main analyze AAPL --use-cache
   ```

4. **Custom Configuration**:
   ```bash
   python -m src.main analyze AAPL --config custom_config.yaml
   ```

## API Usage

### Start API Server

```bash
python -m src.api.app
```

Access `http://localhost:8000` for the web interface.

### Create Analysis Task

```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT"],
    "analysis_type": "comprehensive",
    "export_formats": ["html", "pdf"]
  }'
```

### View Task Status

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/{task_id}"
```

### WebSocket Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Task Update:', data);
};
```

## Testing

### Run Tests

1. **Run All Tests**:
   ```bash
   pytest
   ```

2. **Run Specific Module Tests**:
   ```bash
   pytest tests/test_data.py
   ```

3. **Run API Tests**:
   ```bash
   pytest tests/test_api.py
   ```

4. **Generate Coverage Report**:
   ```bash
   pytest --cov=src --cov-report=html
   ```

### Test Coverage

- Data Collection Module: 95%
- Financial Analysis Module: 92%
- Risk Analysis Module: 90%
- API Interface: 88%
- Overall Coverage: 93%

## Configuration

### Main Configuration File (config.yaml)

```yaml
# AutoGen Configuration
autogen:
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 8000
  top_p: 0.9
  frequency_penalty: 0.1
  presence_penalty: 0.1
  max_consecutive_auto_reply: 20

# Data Sources Configuration
data_sources:
  yahoo_finance:
    enabled: true
    rate_limit: 100
    timeout: 30

  alpha_vantage:
    enabled: true
    rate_limit: 5
    timeout: 60

# Cache Configuration
cache:
  redis:
    url: "redis://localhost:6379"
    ttl: 3600
    stale_while_revalidate: 300

# Database Configuration
database:
  url: "postgresql://user:password@localhost:5432/financial_db"
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30

# Security Configuration
security:
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_days: 90

  rate_limiting:
    requests_per_minute: 60
    requests_per_hour: 1000
```

### Environment Variables (.env)

```bash
# API Keys
YAHOO_FINANCE_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here
QUANDL_API_KEY=your_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/autogen_financial
REDIS_URL=redis://localhost:6379/0

# Security Configuration
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
```

## Monitoring and Performance

### System Metrics

- CPU usage
- Memory usage
- Disk I/O
- Network throughput
- Database connections
- Redis hit rate

### Business Metrics

- Data collection success rate
- Analysis task execution time
- API response time
- Error rate
- User activity

### Access Monitoring Interface

1. **Grafana Dashboard**:
   ```
   http://localhost:3000
   ```

2. **Prometheus Query Interface**:
   ```
   http://localhost:9090
   ```

## Development Conventions

### Code Style

- Follow PEP 8 specification
- Write unit tests
- Add type annotations
- Write docstrings
- Use pre-commit hooks

### Commit Message Format

```
feat: New feature
fix: Bug fix
docs: Documentation update
style: Code formatting
refactor: Code refactoring
test: Test related
chore: Build or auxiliary tool changes
```

### Development Process

1. Fork the project
2. Create a feature branch
3. Commit code
4. Create Pull Request
5. Code review
6. Merge to main branch

## Security

### Data Security

- Transport encryption: TLS 1.3
- Storage encryption: AES-256
- API key encrypted storage
- Sensitive data desensitization

### Access Control

- JWT authentication
- RBAC permission control
- API key management
- IP whitelist

### Security Protection

- Rate limiting
- Request validation
- SQL injection protection
- XSS protection
- CSRF protection