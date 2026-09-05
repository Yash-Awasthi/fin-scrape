"""
数据库配置，默认SQLite可扩展PostgreSQL，优先Alembic迁移，不行就create_all
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("database")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./geopolitical_intel.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_postgresql = DATABASE_URL.startswith("postgresql")

connect_args = {"check_same_thread": False} if _is_sqlite else {}

if _is_sqlite:
    from sqlalchemy.pool import NullPool
    engine = create_engine(
        DATABASE_URL,
        connect_args={**connect_args, "timeout": 30},
        poolclass=NullPool,
    )
    with engine.connect() as _conn:
        _conn.execute(text("PRAGMA journal_mode=WAL"))
        _conn.execute(text("PRAGMA synchronous=NORMAL"))
        _conn.execute(text("PRAGMA busy_timeout=10000"))
        _conn.execute(text("PRAGMA cache_size=-32000"))
        _conn.commit()
    logger.info("[DB] 使用 SQLite: %s", DATABASE_URL)
elif _is_postgresql:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_size=10,
        max_overflow=20,
        pool_timeout=60,
        pool_pre_ping=True,
    )
    logger.info("[DB] 使用 PostgreSQL: %s", DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL)
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    logger.info("[DB] 使用其他数据库: %s", DATABASE_URL.split("://")[0])

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """建表，优先Alembic迁移，不行就create_all"""
    from backend.models import (  # noqa: F401 注册ORM类
        RawNews, NewsCluster, AbstractIRGEvent,
        TheoryAnalysis, ScenarioScript, ScenarioStep,
        PredictionRun, BranchRun, ActualOutcome, PredictionEvaluation,
        ActorProfile, TriggerRule, ConstraintRule, ScenarioContext,
        HistoricalAnalogyResult, HistoricalCase, EventVersion, Annotation,
    )
    from backend.models.user import User  # noqa: F401

    alembic_ok = False
    try:
        from alembic.config import Config
        from alembic import command

        logger.info("[DB] 尝试使用 Alembic 迁移...")
        alembic_cfg = Config(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")))
        command.upgrade(alembic_cfg, "head")
        logger.info("[DB] ✓ Alembic 迁移成功完成")
        alembic_ok = True
    except Exception as e:
        logger.warning(
            f"[DB] Alembic 迁移失败 ({type(e).__name__}: {str(e)[:100]}), "
            f"回退到 create_all() 模式"
        )

    Base.metadata.create_all(bind=engine)

    if not alembic_ok:
        logger.warning(
            "[DB] ⚠ 使用 create_all() 模式（无迁移历史），"
            "建议运行: alembic revision --autogenerate -m 'initial' 初始化迁移"
        )
