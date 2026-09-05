"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Enums
class ThreatLevel(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"
    CRITICAL = "critical"

class IndicatorCategory(str, Enum):
    FINANCIAL = "financial"
    GEOPOLITICAL = "geopolitical"
    SUPPLY_CHAIN = "supply_chain"
    CYBER = "cyber"
    SOCIAL = "social"
    AI_TECH = "ai_tech"
    ENERGY = "energy"
    DEFENSE = "defense"

class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DataSource(str, Enum):
    API = "api"
    SCRAPER = "scraper"
    MANUAL = "manual"
    CALCULATED = "calculated"

# Base Models
class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Indicator Models
class IndicatorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    category: IndicatorCategory
    description: Optional[str] = None
    unit: Optional[str] = None
    source: DataSource
    collection_frequency: int = Field(default=3600, ge=60)  # seconds
    
class IndicatorDataPoint(BaseModel):
    timestamp: datetime
    value: float
    raw_value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('value')
    def validate_value(cls, v):
        if v is None or (isinstance(v, float) and not float('-inf') < v < float('inf')):
            raise ValueError('Invalid value')
        return v

class IndicatorThreshold(BaseModel):
    green_max: float
    amber_max: float
    red_max: float
    inverse: bool = False  # If true, lower values are worse
    
    @validator('amber_max')
    def validate_amber(cls, v, values):
        if 'green_max' in values and v <= values['green_max']:
            raise ValueError('Amber threshold must be greater than green')
        return v
    
    @validator('red_max')
    def validate_red(cls, v, values):
        if 'amber_max' in values and v <= values['amber_max']:
            raise ValueError('Red threshold must be greater than amber')
        return v

class IndicatorStatus(BaseModel):
    indicator_id: str
    name: str
    category: IndicatorCategory
    current_value: float
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    threat_level: ThreatLevel
    last_updated: datetime
    next_update: datetime
    threshold: IndicatorThreshold
    trend: List[IndicatorDataPoint] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

class IndicatorCreate(IndicatorBase):
    threshold: IndicatorThreshold

class IndicatorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    collection_frequency: Optional[int] = None
    threshold: Optional[IndicatorThreshold] = None

class IndicatorResponse(IndicatorBase, TimestampMixin):
    id: str
    status: IndicatorStatus
    enabled: bool = True
    error_count: int = 0
    last_error: Optional[str] = None

# Alert Models
class AlertBase(BaseModel):
    indicator_id: str
    title: str = Field(..., min_length=1, max_length=200)
    message: str
    priority: AlertPriority
    threat_level: ThreatLevel
    
class AlertCreate(AlertBase):
    recipients: Optional[List[str]] = None
    channels: List[str] = Field(default_factory=lambda: ["dashboard"])

class AlertResponse(AlertBase, TimestampMixin):
    id: str
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    sent_channels: List[str] = Field(default_factory=list)

# HOPI Score Models
class HOPIComponent(BaseModel):
    category: IndicatorCategory
    weight: float = Field(..., ge=0, le=1)
    score: float = Field(..., ge=0, le=100)
    indicators: List[str] = Field(default_factory=list)
    threat_level: ThreatLevel

class HOPIScore(BaseModel):
    total_score: float = Field(..., ge=0, le=100)
    threat_level: ThreatLevel
    phase: int = Field(..., ge=0, le=9)
    phase_name: str
    components: List[HOPIComponent]
    recommendations: List[str] = Field(default_factory=list)
    last_calculated: datetime = Field(default_factory=datetime.utcnow)
    next_calculation: datetime

# News Models
class NewsArticle(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    url: str
    source: str
    published_at: datetime
    relevance_score: float = Field(..., ge=0, le=1)
    categories: List[IndicatorCategory] = Field(default_factory=list)
    sentiment: Optional[float] = Field(None, ge=-1, le=1)
    entities: List[str] = Field(default_factory=list)
    threat_indicators: List[str] = Field(default_factory=list)

class NewsIntelligence(BaseModel):
    articles: List[NewsArticle]
    summary: str
    threat_assessment: ThreatLevel
    key_trends: List[str]
    recommended_actions: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Analytics Models
class TimeSeriesData(BaseModel):
    label: str
    data: List[Dict[str, Any]]
    color: Optional[str] = None

class AnalyticsChart(BaseModel):
    title: str
    type: str  # line, bar, pie, etc.
    datasets: List[TimeSeriesData]
    options: Optional[Dict[str, Any]] = None

class AnalyticsReport(BaseModel):
    period_start: datetime
    period_end: datetime
    summary: str
    charts: List[AnalyticsChart]
    insights: List[str]
    predictions: Optional[List[Dict[str, Any]]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# System Models
class SystemStatus(BaseModel):
    operational: bool
    version: str
    uptime_seconds: int
    active_collectors: int
    failed_collectors: int
    last_check: datetime
    database_status: str
    cache_status: str
    queue_status: Optional[str] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, bool]
    metrics: Optional[Dict[str, Any]] = None

# WebSocket Models
class WSMessage(BaseModel):
    event: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WSSubscription(BaseModel):
    client_id: str
    channels: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Response Wrappers
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)