"""
推断中间层模型
"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Float
from backend.db.database import Base


class ActorProfile(Base):
    """主体画像"""
    __tablename__ = "actor_profiles"

    actor_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)
    name = Column(String(200), nullable=False)

    actor_type = Column(String(50))

    strategic_interests = Column(JSON, default=list)
    red_lines = Column(JSON, default=list)
    preferred_tools = Column(JSON, default=list)

    escalation_tendency = Column(Float, default=0.5)
    negotiation_tendency = Column(Float, default=0.5)

    domestic_constraints = Column(JSON, default=list)
    alliance_dependencies = Column(JSON, default=list)
    historical_behavior_patterns = Column(JSON, default=list)

    profile_confidence = Column(Float, default=0.7)
    generated_by = Column(String(20), default="model")
    created_at = Column(DateTime, default=utc_now)


class TriggerRule(Base):
    """触发器规则"""
    __tablename__ = "trigger_rules"

    trigger_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)

    trigger_type = Column(String(50))
    actor = Column(String(200))
    condition_expression = Column(Text)
    weight = Column(Float, default=1.0)
    direction_bias = Column(String(20))
    explanation = Column(Text)

    is_active = Column(String(5), default="true")
    created_at = Column(DateTime, default=utc_now)


class ConstraintRule(Base):
    """约束条件规则"""
    __tablename__ = "constraint_rules"

    constraint_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)

    actor = Column(String(200))
    constraint_type = Column(String(50))
    condition_expression = Column(Text)
    strength = Column(Float, default=0.7)
    blocks_direction = Column(String(20), nullable=True)
    explanation = Column(Text)

    is_active = Column(String(5), default="true")
    created_at = Column(DateTime, default=utc_now)


class ScenarioContext(Base):
    """情景上下文快照"""
    __tablename__ = "scenario_contexts"

    context_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=True, index=True)

    crisis_stage = Column(String(30))
    crisis_stage_rationale = Column(Text)

    actor_profiles_snapshot = Column(JSON, default=list)
    active_triggers = Column(JSON, default=list)
    active_constraints = Column(JSON, default=list)
    theory_views = Column(JSON, default=dict)

    supporting_evidence = Column(JSON, default=list)
    counter_evidence = Column(JSON, default=list)

    time_horizon = Column(String(50), default="3_months")
    direction_weights = Column(JSON, default=dict)

    created_at = Column(DateTime, default=utc_now)
