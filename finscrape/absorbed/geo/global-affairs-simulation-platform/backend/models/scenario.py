"""
剧本模型
"""
from backend.models.utils import utc_now
import uuid
from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, Boolean, Index
from backend.db.database import Base
class ScenarioScript(Base):
    """具体剧本"""
    __tablename__ = "scenario_scripts"

    script_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=True, index=True)

    direction_type = Column(String(20), nullable=False, index=True)  # escalation/stalemate/de_escalation
    script_title = Column(Text, nullable=False)
    script_description = Column(Text)

    why_this_script_is_realistic = Column(Text)          # 可信理由
    trigger_conditions = Column(JSON, default=list)       # 触发条件
    invalidation_conditions = Column(JSON, default=list)  # 失效条件
    supporting_factors = Column(JSON, default=list)       # 支持因素
    opposing_factors = Column(JSON, default=list)         # 反对因素

    probability_low = Column(Float)                       # 概率下界
    probability_high = Column(Float)                      # 概率上界
    probability_central = Column(Float)                   # 中心估计
    confidence_level = Column(String(20))                 # high/medium/low
    uncertainty_notes = Column(Text)                      # 不确定性
    is_branch = Column(Boolean, default=False)        # 分支剧本
    parent_script_id = Column(String, nullable=True, index=True)      # 父剧本
    created_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        Index("ix_scripts_event_direction", "event_id", "direction_type"),
        Index("ix_scripts_event_run", "event_id", "run_id"),
    )


class ScenarioStep(Base):
    """推演步骤"""
    __tablename__ = "scenario_steps"

    step_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = Column(String, nullable=False, index=True)
    step_number = Column(Integer, nullable=False)

    title = Column(Text, nullable=False)
    why_this_step_happens = Column(Text)                  # 发生原因
    which_actor_acts_first = Column(String(200))          # 谁先动
    how_other_actors_react = Column(JSON, default=dict)   # 各方反应
    key_drivers = Column(JSON, default=list)              # 驱动因素
    constraints = Column(JSON, default=list)              # 约束条件
    supporting_evidence = Column(JSON, default=list)      # 支持证据
    counter_evidence = Column(JSON, default=list)         # 反证
    uncertainty = Column(Text)                            # 不确定性
    impact_on_next_step = Column(Text)                    # 影响下一步
    node_type = Column(String(30), default="model_inference_node")
    # data_driven/model_inference/user_hypothesis/analyst_revision

    created_at = Column(DateTime, default=utc_now)
