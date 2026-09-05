"""
历史类比模型
"""
from backend.models.utils import utc_now
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from backend.db.database import Base
class HistoricalAnalogyResult(Base):
    """历史类比推理结果"""
    __tablename__ = "historical_analogy_results"

    analogy_id = Column(String(36), primary_key=True)
    event_id = Column(String(36), nullable=False, index=True)

    # 匹配的历史案例
    matched_cases = Column(JSON, default=list)

    # 综合分析
    synthesis = Column(Text, nullable=True)

    # 历史基础概率
    historical_base_rate = Column(JSON, default=dict)

    # 独特现代因素
    unique_modern_factors = Column(JSON, default=list)

    # 搜索案例数
    total_cases_searched = Column(Integer, default=0)

    # 生成时间
    generated_at = Column(DateTime, default=utc_now)
