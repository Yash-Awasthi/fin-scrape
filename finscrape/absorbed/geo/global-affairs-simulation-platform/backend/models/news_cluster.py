"""
新闻聚类模型
"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Index
from backend.db.database import Base
class NewsCluster(Base):
    __tablename__ = "news_clusters"

    cluster_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cluster_title = Column(Text, nullable=False)           # 事件簇标题
    related_news_ids = Column(JSON, default=list)          # 关联新闻id
    time_window_start = Column(DateTime)
    time_window_end = Column(DateTime)
    key_actors = Column(JSON, default=list)                # 主要行为体
    key_locations = Column(JSON, default=list)             # 关键地点
    primary_issue = Column(Text)                           # 主要议题
    secondary_issues = Column(JSON, default=list)          # 次要议题
    escalation_signals = Column(JSON, default=list)        # 升级信号
    deescalation_signals = Column(JSON, default=list)      # 缓和信号
    evidence_summary = Column(Text)                        # 证据摘要
    cluster_confidence = Column(Float, default=0.7)        # 聚类置信度
    event_id = Column(String, nullable=True, index=True)               # 关联的抽象事件id
    created_at = Column(DateTime, default=utc_now)
    run_snapshot_id = Column(String, nullable=True)        # 快照ID

    __table_args__ = (
        Index("ix_news_clusters_run_snapshot", "run_snapshot_id"),
    )
