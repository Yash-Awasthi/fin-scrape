"""
统一批注机制
"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON
from backend.db.database import Base
class Annotation(Base):
    __tablename__ = "annotations"

    annotation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # --- 绑定目标
    # event/script/theory/analogy/run
    entity_type = Column(String(32), nullable=False, index=True)
    entity_id   = Column(String(64), nullable=False, index=True)

    # --- 内容
    content      = Column(Text, nullable=False)
    # insight/question/critique/data/todo
    tags         = Column(JSON, nullable=False, default=list)
    # low/medium/high
    importance   = Column(String(16), nullable=False, default="medium")

    # --- 版本控制
    version      = Column(String(16), nullable=False, default="1")
    # 历史版本，最多5条
    history      = Column(JSON, nullable=False, default=list)

    # --- 访问日志
    access_log   = Column(JSON, nullable=False, default=list)

    # --- 元数据
    created_at   = Column(DateTime, default=utc_now, nullable=False)
    updated_at   = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
