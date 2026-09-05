# Canairy System Architecture

## Overview

Canairy is a distributed early warning system built with a microservices architecture that prioritizes reliability, real-time data processing, and user safety. The system monitors 22 global indicators through specialized data collectors, processes them through an intelligent backend, and presents actionable intelligence through a responsive React dashboard.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              User Layer                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  React Dashboard │ Mobile PWA │ API Clients │ Notification Services     │
└─────────────────┬───────────────────────────┬───────────────────────────┘
                  │                           │
┌─────────────────▼───────────────────────────▼───────────────────────────┐
│                           API Gateway (REST/WebSocket)                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Authentication │ Rate Limiting │ Request Routing │ WebSocket Manager    │
└─────────────────┬───────────────────────────┬───────────────────────────┘
                  │                           │
┌─────────────────▼───────────────────────────▼───────────────────────────┐
│                          Core Services Layer                             │
├─────────────────────────────────────────────────────────────────────────┤
│  Risk Engine │ Alert Manager │ News Intelligence │ Historical Analysis   │
└─────────────────┬───────────────────────────┬───────────────────────────┘
                  │                           │
┌─────────────────▼───────────────────────────▼───────────────────────────┐
│                         Data Processing Layer                            │
├─────────────────────────────────────────────────────────────────────────┤
│  Data Collectors │ ETL Pipeline │ Time Series Engine │ Cache Layer      │
└─────────────────┬───────────────────────────┬───────────────────────────┘
                  │                           │
┌─────────────────▼───────────────────────────▼───────────────────────────┐
│                          Storage Layer                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Primary) │ Redis (Cache) │ InfluxDB (Time Series) │ S3     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Architecture

#### React Dashboard
- **Framework**: React 18.2 with TypeScript
- **State Management**: Zustand for global state
- **Routing**: React Router v6
- **Styling**: Tailwind CSS with custom dark theme
- **Charts**: Chart.js with react-chartjs-2
- **Animations**: Framer Motion
- **Build Tool**: Vite for fast HMR and optimized builds

```typescript
// Component Structure
src/
├── components/
│   ├── charts/         # Data visualization components
│   ├── core/           # Reusable UI components
│   ├── dashboard/      # Dashboard-specific panels
│   ├── indicators/     # Indicator cards and modals
│   └── news/           # News feed and sidebar
├── services/           # API clients and utilities
├── store/              # Global state management
└── types/              # TypeScript definitions
```

#### Key Frontend Features
- **Real-time Updates**: WebSocket connection for live data
- **Progressive Web App**: Offline capability and mobile optimization
- **Responsive Design**: Adaptive layouts for all screen sizes
- **Dark Theme**: Reduces eye strain during extended monitoring
- **Performance**: Code splitting and lazy loading for fast initial load

### 2. Backend Architecture

#### API Gateway
- **Framework**: FastAPI (Python) / Express (Node.js)
- **Protocol**: REST with WebSocket support
- **Authentication**: JWT tokens with refresh mechanism
- **Rate Limiting**: Per-user and per-endpoint limits
- **Documentation**: OpenAPI/Swagger auto-generated

#### Core Services

##### Risk Engine
```python
class RiskEngine:
    """
    Calculates threat levels and phase transitions
    """
    def calculate_hopi_score(indicators: List[Indicator]) -> float:
        # Weighted scoring algorithm
        pass
    
    def determine_phase(hopi_score: float, indicators: List[Indicator]) -> Phase:
        # Phase transition logic
        pass
    
    def generate_alerts(current_state: SystemState, previous_state: SystemState) -> List[Alert]:
        # Alert generation based on state changes
        pass
```

##### Alert Manager
- Manages alert lifecycle (creation, delivery, acknowledgment)
- Supports multiple channels (email, SMS, push, webhook)
- Implements alert fatigue prevention
- Tracks alert history and user preferences

##### News Intelligence Service
- Aggregates news from multiple sources
- Uses NLP to match articles to indicators
- Calculates credibility scores
- Implements smart caching to reduce API costs

### 3. Data Layer

#### Data Collectors
Each indicator has a dedicated collector that:
- Fetches data from primary and fallback sources
- Validates and normalizes data
- Handles API failures gracefully
- Implements exponential backoff for retries

```python
# Example Collector Structure
class TreasuryTailCollector(BaseCollector):
    primary_source = "https://api.treasurydirect.gov/"
    fallback_sources = ["alpha_vantage", "manual_entry"]
    
    async def collect(self) -> IndicatorData:
        try:
            data = await self.fetch_primary()
        except SourceUnavailable:
            data = await self.fetch_fallback()
        
        return self.normalize(data)
```

#### Time Series Engine
- **Storage**: InfluxDB for efficient time series data
- **Retention**: Configurable per indicator (1 year default)
- **Aggregation**: Automatic downsampling for historical data
- **Performance**: Sub-second queries for dashboard charts

### 4. Infrastructure

#### Database Schema

```sql
-- Core Tables
CREATE TABLE indicators (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    critical BOOLEAN DEFAULT FALSE,
    thresholds JSONB
);

CREATE TABLE indicator_values (
    id BIGSERIAL PRIMARY KEY,
    indicator_id UUID REFERENCES indicators(id),
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC,
    status VARCHAR(20),
    metadata JSONB,
    INDEX idx_indicator_time (indicator_id, timestamp DESC)
);

CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    indicator_id UUID REFERENCES indicators(id),
    level VARCHAR(20) NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    user_acknowledged UUID
);
```

#### Caching Strategy
- **Redis**: Hot data and session storage
- **CDN**: Static assets and API responses
- **Local Storage**: Client-side caching for offline mode
- **TTL Strategy**: 
  - Live data: 60 seconds
  - News: 5 minutes
  - Historical data: 1 hour

### 5. Security Architecture

#### Data Security
- **Encryption at Rest**: AES-256 for database
- **Encryption in Transit**: TLS 1.3 minimum
- **API Keys**: Encrypted storage with rotation support
- **PII Protection**: No personal data stored

#### Authentication & Authorization
```javascript
// JWT Token Structure
{
  "sub": "user_id",
  "iat": 1609459200,
  "exp": 1609545600,
  "scope": ["read", "write"],
  "tier": "premium"
}
```

#### Security Headers
```nginx
# Nginx Configuration
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Content-Security-Policy "default-src 'self'";
add_header Strict-Transport-Security "max-age=31536000";
```

### 6. Deployment Architecture

#### Container Strategy
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    image: canairy/frontend:latest
    ports:
      - "3005:80"
    
  backend:
    image: canairy/backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    
  collectors:
    image: canairy/collectors:latest
    deploy:
      replicas: 3
    
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    
  influxdb:
    image: influxdb:2.7
```

#### Scaling Strategy
- **Horizontal Scaling**: Collectors and API servers
- **Vertical Scaling**: Database and cache layers
- **Auto-scaling**: Based on CPU and request metrics
- **Load Balancing**: Round-robin with health checks

### 7. Monitoring & Observability

#### Metrics Collection
- **Prometheus**: System and application metrics
- **Grafana**: Visualization and dashboards
- **Custom Metrics**:
  - Indicator update frequency
  - Alert delivery success rate
  - API response times
  - Data source availability

#### Logging Architecture
```python
# Structured Logging
logger.info("indicator_updated", {
    "indicator_id": "treasury_tail",
    "old_value": 2.3,
    "new_value": 2.8,
    "threshold_crossed": True,
    "alert_generated": True
})
```

#### Health Checks
```python
# Health Check Endpoints
GET /health/live    # Kubernetes liveness
GET /health/ready   # Kubernetes readiness
GET /health/startup # Initialization status
```

### 8. Disaster Recovery

#### Backup Strategy
- **Database**: Daily snapshots with 30-day retention
- **Time Series**: Continuous replication to secondary
- **Configuration**: Version controlled in Git
- **Recovery Time Objective (RTO)**: < 1 hour
- **Recovery Point Objective (RPO)**: < 15 minutes

#### Failover Process
1. Primary region failure detected
2. DNS failover to secondary region (< 5 minutes)
3. Read replica promoted to primary
4. Collectors resume from last checkpoint
5. Users notified of brief disruption

## Performance Optimization

### Frontend Optimization
- **Code Splitting**: Route-based lazy loading
- **Asset Optimization**: WebP images, compressed fonts
- **Service Worker**: Offline functionality
- **Virtual Scrolling**: For large data sets
- **Memoization**: Expensive calculations cached

### Backend Optimization
- **Connection Pooling**: Database and Redis
- **Query Optimization**: Indexed queries, prepared statements
- **Batch Processing**: Bulk inserts for time series
- **Async Operations**: Non-blocking I/O throughout
- **Circuit Breakers**: Prevent cascade failures

## Future Architecture Enhancements

### Planned Improvements
1. **GraphQL API**: More efficient data fetching
2. **Event Sourcing**: Complete audit trail
3. **Machine Learning Pipeline**: Predictive alerts
4. **Multi-Region Active-Active**: Global availability
5. **Kubernetes Operators**: Automated operations

### Scalability Targets
- Support 100,000+ concurrent users
- Process 1M+ indicator updates per minute
- Deliver alerts within 10 seconds of detection
- Maintain 99.95% uptime SLA

## Development Workflow

### Local Development
```bash
# Start all services locally
docker-compose up -d

# Run frontend with hot reload
npm run dev

# Run backend with auto-reload
uvicorn main:app --reload

# Run tests
npm test
pytest
```

### CI/CD Pipeline
1. **Code Push**: Triggers GitHub Actions
2. **Tests**: Unit, integration, and E2E tests
3. **Build**: Docker images created
4. **Security Scan**: Vulnerability scanning
5. **Deploy**: Staged rollout to production
6. **Monitor**: Automated rollback on errors

## Conclusion

The Canairy architecture is designed for reliability, scalability, and maintainability. By separating concerns across multiple layers and using modern cloud-native patterns, the system can evolve to meet growing demands while maintaining its core mission of keeping families safe.