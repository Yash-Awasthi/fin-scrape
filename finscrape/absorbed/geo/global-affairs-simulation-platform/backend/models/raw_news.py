"""
原始新闻模型
"""
from backend.models.utils import utc_now
import uuid

from sqlalchemy import JSON, Column, DateTime, Index, String, Text

from backend.db.database import Base
class RawNews(Base):
    __tablename__ = "raw_news"

    news_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name = Column(String(200), nullable=False)
    source_type = Column(String(50))  # rss/api/scrape/manual
    title = Column(Text, nullable=False)
    body = Column(Text)
    url = Column(Text)
    published_at = Column(DateTime)
    language = Column(String(10), default="en")
    region_tags = Column(JSON, default=list)  # 地区标签
    raw_entities = Column(JSON, default=dict)  # 实体抽取结果
    dedupe_hash = Column(String(64), unique=True, index=True)  # 去重hash
    cluster_id = Column(String, nullable=True)
    fetched_at = Column(DateTime, default=utc_now)
    status = Column(String(20), default="raw", index=True)  # raw/cleaned/clustered

    __table_args__ = (
        Index("ix_raw_news_source_status", "source_name", "status"),
    )
