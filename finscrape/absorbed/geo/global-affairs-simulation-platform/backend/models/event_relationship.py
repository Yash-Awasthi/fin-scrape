"""
事件间关系模型"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Float, Index
import enum
from backend.db.database import Base
class RelationshipType(str, enum.Enum):
    """关系类型"""
    shared_actor = "shared_actor"
    same_region = "same_region"
    causal_chain = "causal_chain"
    escalation_cascade = "escalation_cascade"
    semantic_similar = "semantic_similar"
    actor_conflict = "actor_conflict"


class EventRelationship(Base):
    __tablename__ = "event_relationships"

    relationship_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_event_id = Column(String, nullable=False, index=True)   # 源事件
    to_event_id = Column(String, nullable=False, index=True)     # 目标事件

    relationship_type = Column(String(40), nullable=False, index=True)       # RelationshipType
    weight = Column(Float, default=1.0)                          # 关系权重

    # 关系元数据，如shared_actor的actors、causal_chain的reason
    rel_metadata = Column("relationship_metadata", JSON, default=dict)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("ix_relationships_from_to", "from_event_id", "to_event_id"),
        Index("ix_relationships_from_type", "from_event_id", "relationship_type"),
    )
