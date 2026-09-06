"""FastAPI app factory: lifespan opens the pool + runs migrations; /health probes.

Phase 0 ships only /health (+ auto /docs). Later phases mount routers from
server/routes/ here. Keeping the factory small means tests can build an app without
a real DB by monkeypatching db.connect.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from finscrape.api.geopolitical_api import router as geopolitical_router
from finscrape.api.intelligence_api import router as intelligence_router
from server import db, pubsub, queries
from server.middleware import configure_hardening
from server.obs import install_observability
from server.routes import accuracy as accuracy_routes
from server.routes import agents as agents_routes
from server.routes import ai as ai_routes
from server.routes import correlations as correlations_routes
from server.routes import data as data_routes
from server.routes import events as events_routes
from server.routes import health as health_routes
from server.routes import insight as insight_routes
from server.routes import market as market_routes
from server.routes import portfolio as portfolio_routes
from server.routes import sentiment as sentiment_routes
from server.routes import telegram as telegram_routes
from server.schemas import HealthResponse
from server.settings import get_settings
from server.ws import hub

log = logging.getLogger("worldfin.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    p = await db.connect(s.database_url, min_size=s.db_pool_min, max_size=s.db_pool_max)
    if s.run_migrations_on_startup:
        await db.run_migrations(p)
    # Forward worker-published new_events to this process's WS clients (no-op without Redis).
    sub_task = asyncio.create_task(pubsub.subscribe_forever(hub.broadcast))
    try:
        yield
    finally:
        sub_task.cancel()
        await db.disconnect()


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="WorldFin API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in s.cors_origins.split(",")]
        if s.cors_origins
        else [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    configure_hardening(app)
    # Registered after hardening → outermost: stamps a correlation id on every
    # request (incl. error paths) and times them. Also mounts /metrics.
    install_observability(app, stale_after_min=s.source_stale_after_minutes)

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Liveness: the process is up. Always 200 (degraded if DB is unreachable)."""
        db_ok = True
        try:
            await db.pool().fetchval("SELECT 1")
        except Exception as exc:  # pragma: no cover - exercised only on a broken DB
            log.warning("health: db check failed: %s", exc)
            db_ok = False
        return HealthResponse(
            status="ok" if db_ok else "degraded",
            db=db_ok,
            llm=s.has_llm,
            sources=[],
        )

    @app.get("/ready")
    async def ready(response: Response) -> dict:
        """Readiness: 200 only when the DB pool answers; 503 otherwise so an
        orchestrator (compose healthcheck / k8s) stops routing to a half-open replica."""
        try:
            await db.pool().fetchval("SELECT 1")
        except Exception as exc:  # pragma: no cover - exercised only on a broken DB
            log.warning("ready: db check failed: %s", exc)
            response.status_code = 503
            return {"ready": False}
        return {"ready": True}

    app.include_router(events_routes.router)
    app.include_router(ai_routes.router)
    app.include_router(health_routes.router)
    app.include_router(correlations_routes.router)
    app.include_router(data_routes.router)
    app.include_router(market_routes.router)
    app.include_router(insight_routes.router)
    app.include_router(agents_routes.router)
    app.include_router(accuracy_routes.router)
    app.include_router(sentiment_routes.router)
    app.include_router(portfolio_routes.router)
    app.include_router(telegram_routes.router)
    app.include_router(geopolitical_router, prefix="/api/v1", tags=["Geopolitical & Sentiment"])
    app.include_router(intelligence_router, prefix="/api/v1", tags=["Intelligence Modules"])

    @app.websocket("/api/ws")
    async def ws(websocket: WebSocket) -> None:
        await hub.add(websocket)
        try:
            pool = db.pool()
            await websocket.send_json(
                jsonable_encoder(
                    {
                        "type": "init",
                        "stats": await queries.get_stats(pool),
                        "events": await queries.get_events(pool, limit=20),
                    }
                )
            )
            while True:
                msg = await websocket.receive_json()
                if isinstance(msg, dict) and msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            await hub.remove(websocket)

    return app
