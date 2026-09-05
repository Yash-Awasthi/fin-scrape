"""
Application configuration using Pydantic Settings
"""

from typing import List, Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Canairy"
    VERSION: str = "2.1.0"
    DESCRIPTION: str = "Early Warning System for Global Disruptions"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:5173",
        "https://canairy.onrender.com",
        "https://brown-man-bunker.onrender.com",
        "https://bunker-frontend.onrender.com",
        "https://canairy.xyz",
        "https://www.canairy.xyz",
        "https://canairy-dashboard.onrender.com"
    ]
    
    # Database
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # 5 minutes default
    CACHE_KEY_PREFIX: str = "canairy:"
    
    # API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    FRED_API_KEY: Optional[str] = None
    ACLED_API_KEY: Optional[str] = None
    ACLED_EMAIL: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PATH: str = "/metrics"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Data Collection
    COLLECTOR_TIMEOUT: int = 30
    COLLECTOR_RETRY_COUNT: int = 3
    COLLECTOR_RETRY_DELAY: int = 5
    
    # Alerts
    ALERT_CHECK_INTERVAL: int = 300  # 5 minutes
    ALERT_COOLDOWN_PERIOD: int = 3600  # 1 hour
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "alerts@canairy.com"
    
    # Twilio (SMS)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MESSAGE_QUEUE_SIZE: int = 100
    
    # Data Processing
    DATA_RETENTION_DAYS: int = 90
    AGGREGATION_INTERVAL: int = 3600  # 1 hour
    
    # Feature Flags
    ENABLE_NEWS_INTELLIGENCE: bool = True
    ENABLE_AUTO_ALERTS: bool = True
    ENABLE_PREDICTIONS: bool = False
    ENABLE_WEBSOCKET: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()

settings = get_settings()