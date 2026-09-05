"""
FastAPI入口
"""
import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.core.logging_config import setup_logging
from backend.core.rate_limiter import limiter
from backend.db.database import create_all_tables
from backend.routers.annotations import router as annotations_router
from backend.routers.api import router as api_router
from backend.routers.pipeline import router as pipeline_router
from backend.routers.auth import router as auth_router

setup_logging()

logger = logging.getLogger("main")

_HEALTH_DEPS_TTL_SECONDS = 20
_health_deps_cache = {
    "ts": 0.0,
    "deps": {
        "local_proxy_7897": False,
        "claude_api_relay": False,
    },
}


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = ConnectionManager()


async def _probe_dependency_status():
    """快速探测依赖是否可达"""
    import httpx

    proxy_ok = False
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", 7897), timeout=1.0
        )
        writer.close()
        await writer.wait_closed()
        proxy_ok = True
    except Exception:
        pass

    api_ok = False
    api_base = settings.ANTHROPIC_BASE_URL.rstrip("/")
    probe_url = api_base.replace("/v1", "") or api_base
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(probe_url)
            api_ok = resp.status_code < 500
    except Exception:
        pass

    return {
        "local_proxy_7897": proxy_ok,
        "claude_api_relay": api_ok,
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("[startup] initializing database...")
    create_all_tables()
    from backend.db.database import SessionLocal
    from backend.services.analogy_engine import seed_cases_from_json
    from backend.services.task_manager import set_event_loop
    set_event_loop(asyncio.get_event_loop())
    try:
        _seed_db = SessionLocal()
        seeded = seed_cases_from_json(_seed_db)
        _seed_db.close()
        if seeded > 0:
            logger.info("[startup] seeded %d historical cases from JSON", seeded)
    except Exception as e:
        logger.warning("[startup] case seeding skipped: %s", e)
    logger.info(
        "[startup] %s v%s started | model=%s | DEBUG=%s",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.CLAUDE_MODEL,
        settings.DEBUG,
    )
    asyncio.create_task(_check_external_deps())
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Geopolitical intelligence and scenario simulation API",
    version=settings.APP_VERSION,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if settings.DEBUG:
    cors_origins = settings.CORS_ORIGINS + ["*"]
    logger.warning("CORS in DEBUG mode allows all origins.")
else:
    cors_origins = settings.CORS_ORIGINS
    logger.info("CORS whitelist enabled: %s", cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(pipeline_router)
app.include_router(api_router)
app.include_router(annotations_router)

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    logger.info("[startup] Prometheus metrics enabled at /metrics")
except ImportError:
    pass


@app.websocket("/api/v1/ws/pipeline")
async def ws_pipeline(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/api/v1/health", tags=["system"])
async def health():
    now_ts = time.monotonic()
    if now_ts - float(_health_deps_cache["ts"]) > _HEALTH_DEPS_TTL_SECONDS:
        _health_deps_cache["deps"] = await _probe_dependency_status()
        _health_deps_cache["ts"] = now_ts

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "model": settings.CLAUDE_MODEL,
        "debug": settings.DEBUG,
        "deps": _health_deps_cache["deps"],
    }


@app.get("/api/health", tags=["system"], include_in_schema=False)
async def health_legacy():
    return await health()

async def _check_external_deps():
    """启动时非阻塞检查外部依赖，只记日志"""
    deps = await _probe_dependency_status()
    if deps["local_proxy_7897"]:
        logger.info("[startup] local proxy 127.0.0.1:7897 reachable")
    else:
        logger.warning(
            "[startup] local proxy 127.0.0.1:7897 unreachable; RSS sources may fail"
        )

    if deps["claude_api_relay"]:
        logger.info("[startup] Claude relay reachable: %s", settings.ANTHROPIC_BASE_URL)
    else:
        logger.warning(
            "[startup] Claude relay unreachable: %s; analysis will fallback to rules",
            settings.ANTHROPIC_BASE_URL,
        )


# 静态文件挂载放路由后面
frontend_dist = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)
if os.path.exists(frontend_dist):
    logger.info("[startup] mounting frontend static files: %s", frontend_dist)
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
