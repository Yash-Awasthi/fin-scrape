"""
实际结果模型
"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Boolean
from backend.db.database import Base


class ActualOutcome(Base):
    """实际结果，和预测对照用"""
    __tablename__ = "actual_outcomes"

    outcome_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)
    related_run_id = Column(String, nullable=True, index=True)

    actual_summary = Column(Text)
    actual_event_type = Column(String(60))
    actual_event_time = Column(DateTime, nullable=True)
    matched_script_id = Column(String, nullable=True)

    evidence_ids = Column(JSON, default=list)

    recorded_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)


class PredictionEvaluation(Base):
    """预测评估 — 对比预测剧本与实际结果，误差分析"""
    __tablename__ = "prediction_evaluations"

    evaluation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, nullable=False, index=True)
    outcome_id = Column(String, nullable=True)

    matched_script_id = Column(String, nullable=True)
    script_hit = Column(Boolean, default=False)
    node_hit_rate = Column(Float, nullable=True)
    main_error_category = Column(String(60), nullable=True)
    detailed_error_analysis = Column(Text)
    correct_aspects = Column(JSON, default=list)
    incorrect_aspects = Column(JSON, default=list)
    suggested_adjustments = Column(JSON, default=list)

    evaluated_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)
