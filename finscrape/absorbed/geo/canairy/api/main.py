"""
FastAPI Backend for Canairy Early Warning System
Enhanced version with proper architecture
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Optional

try:
    from api.core.config import settings
    from api.core.logging import setup_logging
    from api.routers import indicators, alerts, news, analytics, health
    from api.middleware.rate_limit import RateLimitMiddleware
    from api.middleware.cache import CacheMiddleware
    from api.core.cache import cache_manager
    _FULL_MODE = True
    logger = setup_logging(__name__)
except ImportError:
    _FULL_MODE = False
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning("Running in lite mode — some dependencies missing")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    if _FULL_MODE:
        logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
        await cache_manager.initialize()
        logger.info("All services initialized successfully")
    else:
        logger.info("Starting Canairy (lite mode)")
    yield
    if _FULL_MODE:
        logger.info("Shutting down application")
        await cache_manager.close()

# Create FastAPI app
if _FULL_MODE:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Early Warning System for Global Disruptions",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    app.add_middleware(CacheMiddleware)
    app.include_router(health.router, tags=["health"])
    app.include_router(indicators.router, prefix="/api/v1/indicators", tags=["indicators"])
    app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
    app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
else:
    app = FastAPI(
        title="Canairy",
        version="2.1.0",
        description="Early Warning System for Global Disruptions (lite)",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/api/v1/hopi", tags=["hopi"])
async def get_hopi_score():
    return {
      "score": 75.5,
      "confidence": 0.85,
      "phase": 3,
      "targetPhase": 4,
      "domains": {
        "economy": { "score": 80, "weight": 0.3, "indicators": ["econ_01_treasury_tail"], "criticalAlerts": [] },
        "global_conflict": { "score": 70, "weight": 0.2, "indicators": ["civil_01_acled_protests"], "criticalAlerts": ["civil_01_acled_protests"] },
        "energy": { "score": 60, "weight": 0.2, "indicators": ["oil_01_russian_brics"], "criticalAlerts": [] },
        "ai_tech": { "score": 90, "weight": 0.15, "indicators": ["labor_ai_01_layoffs"], "criticalAlerts": [] },
        "domestic_control": { "score": 50, "weight": 0.15, "indicators": ["power_01_ai_surveillance"], "criticalAlerts": [] }
      },
      "timestamp": "2025-09-01T12:00:00Z"
    }

@app.get("/api/v1/status", tags=["status"])
async def get_system_status():
    return {
      "operational": True,
      "lastUpdate": "2025-09-01T12:00:00Z",
      "activeAlerts": 2,
      "dataQuality": 0.95,
      "message": "All systems nominal, 2 active alerts."
    }

@app.get("/api/v1/phase", tags=["phase"])
async def get_current_phase():
    return {
      "number": 3,
      "name": "Air, health, mobile",
      "description": "Focus on immediate personal and family safety measures.",
      "triggers": ["1 red anywhere or 2 ambers sustained 7 days"],
      "actions": ["HEPA on", "N95 cache verified", "C1000 moved to shelter as UPS"],
      "color": "#FFC107"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
        }
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/api/docs" if settings.DEBUG else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )