"""
事件版本历史 - 记录事件数据的每次变更"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Index
from backend.db.database import Base
class EventVersion(Base):
    """事件版本快照"""
    __tablename__ = "event_versions"

    version_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)

    snapshot = Column(JSON, nullable=False)

    change_source = Column(String(64), nullable=True)
    change_summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_event_versions_event_number", "event_id", "version_number"),
    )


def version_to_dict(v: EventVersion) -> dict:
    return {
        "version_id": v.version_id,
        "event_id": v.event_id,
        "version_number": v.version_number,
        "snapshot": v.snapshot or {},
        "change_source": v.change_source or "",
        "change_summary": v.change_summary or "",
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }
