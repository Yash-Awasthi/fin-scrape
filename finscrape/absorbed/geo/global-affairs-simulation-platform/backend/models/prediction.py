"""
推演的根记录
"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON
from backend.db.database import Base


class PredictionRun(Base):
    """推演的根记录"""
    __tablename__ = "prediction_runs"

    run_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)

    root_question = Column(Text)
    summary = Column(Text)
    status = Column(String(20), default="pending", index=True)

    model_version = Column(String(80))
    rules_version = Column(String(20))
    is_branch = Column(String(5), default="false")

    script_ids = Column(JSON, default=list)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class BranchRun(Base):
    """分支推演 — 用户引入假设后从原PredictionRun分叉"""
    __tablename__ = "branch_runs"

    branch_run_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    base_run_id = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)

    introduced_by = Column(String(80), default="user")
    hypothesis_type = Column(String(40))
    hypothesis_title = Column(Text)
    hypothesis_description = Column(Text)
    affected_actors = Column(JSON, default=list)
    expected_direction = Column(String(30))

    status = Column(String(20), default="running", index=True)
    branch_script_ids = Column(JSON, default=list)
    diff_summary = Column(Text)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
