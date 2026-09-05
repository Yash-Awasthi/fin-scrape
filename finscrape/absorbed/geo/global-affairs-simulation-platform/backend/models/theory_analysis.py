"""
多理论视角分析
"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Index
from backend.db.database import Base

THEORY_NAMES = [
    "realism",
    "liberal_institutionalism",
    "constructivism",
    "geopolitics",
    "international_political_economy",
]

THEORY_DISPLAY_NAMES = {
    "realism": "现实主义",
    "liberal_institutionalism": "自由制度主义",
    "constructivism": "建构主义",
    "geopolitics": "地缘政治学",
    "international_political_economy": "国际政治经济学",
}


class TheoryAnalysis(Base):
    __tablename__ = "theory_analyses"

    analysis_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)
    theory_name = Column(String(60), nullable=False, index=True)
    core_assumption = Column(Text)
    interpretation = Column(Text)
    main_drivers = Column(JSON, default=list)
    likely_actor_responses = Column(JSON, default=dict)
    escalation_implications = Column(JSON, default=list)
    deescalation_implications = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    counterarguments = Column(JSON, default=list)

    confidence_note = Column(Text)
    created_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        Index("ix_theory_event_name", "event_id", "theory_name"),
    )
