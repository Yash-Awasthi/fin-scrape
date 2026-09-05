"""
抽象国际关系事件模型
"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Index
from backend.db.database import Base
from backend.models.utils import utc_now


class AbstractIRGEvent(Base):
    __tablename__ = "abstract_irg_events"

    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_cluster_ids = Column(JSON, default=list)

    event_title = Column(Text, nullable=False)
    event_type = Column(String(60), nullable=False, index=True)
    stage_of_crisis = Column(String(30), index=True)

    key_actors = Column(JSON, default=list)
    actor_roles = Column(JSON, default=dict)
    key_locations = Column(JSON, default=list)
    strategic_dimensions = Column(JSON, default=list)

    driving_forces = Column(JSON, default=list)
    constraints = Column(JSON, default=list)
    immediate_triggers = Column(JSON, default=list)
    current_balance = Column(Text)
    major_risks = Column(JSON, default=list)
    current_opportunities = Column(JSON, default=list)

    event_confidence = Column(Float, default=0.75)
    geo_coordinates = Column(JSON, default=dict)
    region = Column(String(100), index=True)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    status = Column(String(20), default="active", index=True)

    _is_fallback_override = None

    __table_args__ = (
        Index("ix_events_type_stage", "event_type", "stage_of_crisis"),
        Index("ix_events_region_status", "region", "status"),
    )

    @property
    def is_fallback(self) -> bool:
        if self._is_fallback_override is not None:
            return bool(self._is_fallback_override)
        return (self.event_confidence or 0.0) < 0.5

    @is_fallback.setter
    def is_fallback(self, value):
        self._is_fallback_override = bool(value)
