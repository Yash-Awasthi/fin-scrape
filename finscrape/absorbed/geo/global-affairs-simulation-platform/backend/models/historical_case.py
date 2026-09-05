"""
鍘嗗彶妗堜緥妯″瀷 - 浠嶫SON鏂囦欢杩佺Щ鍒版暟鎹簱瀛樺偍
"""
from backend.models.utils import utc_now
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from backend.db.database import Base
class HistoricalCase(Base):
    """历史案例库"""
    __tablename__ = "historical_cases"

    case_id = Column(String(128), primary_key=True)

    title = Column(String(256), nullable=False)
    title_en = Column(String(256), nullable=True)

    year = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=True)

    event_type = Column(String(64), nullable=True, index=True)
    region = Column(String(64), nullable=True, index=True)
    crisis_stage_peak = Column(String(32), nullable=True)

    key_actors = Column(JSON, default=list)
    actor_roles = Column(JSON, default=dict)

    primary_issue = Column(Text, nullable=True)
    strategic_dimensions = Column(JSON, default=list)
    key_triggers = Column(JSON, default=list)
    key_constraints = Column(JSON, default=list)
    escalation_path = Column(JSON, default=list)

    resolution = Column(Text, nullable=True)
    resolution_type = Column(String(32), nullable=True)
    outcome_summary = Column(Text, nullable=True)

    key_lessons = Column(JSON, default=list)
    analogous_features = Column(JSON, default=list)

    probability_realized = Column(JSON, default=dict)
    actual_outcome_direction = Column(String(32), nullable=True)
    prediction_accuracy_notes = Column(Text, nullable=True)

    tags = Column(JSON, default=list)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


def case_to_dict(case: HistoricalCase) -> dict:
    return {
        "case_id": case.case_id,
        "title": case.title,
        "title_en": case.title_en or "",
        "year": case.year,
        "duration_days": case.duration_days,
        "event_type": case.event_type or "",
        "region": case.region or "",
        "crisis_stage_peak": case.crisis_stage_peak or "",
        "key_actors": case.key_actors or [],
        "actor_roles": case.actor_roles or {},
        "primary_issue": case.primary_issue or "",
        "strategic_dimensions": case.strategic_dimensions or [],
        "key_triggers": case.key_triggers or [],
        "key_constraints": case.key_constraints or [],
        "escalation_path": case.escalation_path or [],
        "resolution": case.resolution or "",
        "resolution_type": case.resolution_type or "",
        "outcome_summary": case.outcome_summary or "",
        "key_lessons": case.key_lessons or [],
        "analogous_features": case.analogous_features or [],
        "probability_realized": case.probability_realized or {},
        "actual_outcome_direction": case.actual_outcome_direction or "",
        "prediction_accuracy_notes": case.prediction_accuracy_notes or "",
        "tags": case.tags or [],
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }
