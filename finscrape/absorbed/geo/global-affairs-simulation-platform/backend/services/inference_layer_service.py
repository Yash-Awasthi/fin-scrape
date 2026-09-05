"""
推断中间层 - 画像/触发器/约束/方向权重
"""
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models.ir_event import AbstractIRGEvent
from backend.models.inference_layer import (
    ActorProfile, TriggerRule, ConstraintRule, ScenarioContext
)
from backend.core.llm_router import llm_call_json

logger = logging.getLogger(__name__)

# --- prompts ---

ACTOR_PROFILE_SYSTEM = """
你是一位专注于国际关系行为体分析的战略分析师。

你的任务是为特定事件中的每个主要行为体生成详细画像。

重要规则：
1. 画像必须和当前事件的具体情境强绑定，不是通用的国家介绍
2. 红线必须具体，不是"不喜欢战争"这样的废话
3. 偏好工具必须体现该主体在该类型事件中的历史行为
4. 国内约束必须具体到政治派系、选举周期、舆论压力等

输出严格 JSON 格式。
"""

ACTOR_PROFILE_USER = """
事件：{event_title}
事件类型：{event_type}
危机阶段：{stage_of_crisis}
行为主体：{actor_name}
该主体在事件中的角色：{actor_role}
驱动力背景：{driving_forces}
约束条件背景：{constraints}

为 {actor_name} 生成在该事件中的行为画像：

```json
{{
  "name": "{actor_name}",
  "actor_type": "state/non_state/international_organization",
  "strategic_interests": ["核心战略利益1（具体）", "利益2"],
  "red_lines": ["具体红线1（会引发强烈反应的触发点）", "红线2"],
  "preferred_tools": ["该主体在此类事件中最常用的工具1", "工具2"],
  "escalation_tendency": 0.6,
  "negotiation_tendency": 0.4,
  "domestic_constraints": ["具体国内政治约束1", "约束2"],
  "alliance_dependencies": ["关键同盟依赖1", "依赖2"],
  "historical_behavior_patterns": [
    "历史上类似情境下的行为模式1（可引用具体案例）",
    "模式2"
  ],
  "profile_confidence": 0.8
}}
```
"""

TRIGGER_EXTRACTION_SYSTEM = """
你是一位专注于危机触发机制分析的战略分析师。

你的任务是：从当前事件信息中提取具体的触发器规则——
即什么条件成立时，会推动局势向哪个方向发展。

规则：
1. 触发器必须和当前事件类型强绑定
2. 触发器必须具体，能被观察和验证
3. 不同方向的触发器要有显著差异
4. 必须说明为什么该触发器会推动该方向

输出严格 JSON 格式。
"""

TRIGGER_EXTRACTION_USER = """
事件：{event_title}
事件类型：{event_type}（{event_type_guidance}）
危机阶段：{stage_of_crisis}
主要行为主体：{key_actors}
直接触发器：{immediate_triggers}
驱动力：{driving_forces}
主要风险：{major_risks}

请提取该事件的触发器规则。返回 JSON：

```json
{{
  "escalation_triggers": [
    {{
      "trigger_type": "military_action/diplomatic_statement/economic_measure/domestic_political/third_party_intervention",
      "actor": "触发该规则的主体",
      "condition_expression": "具体可观察的触发条件（不准用套话）",
      "weight": 0.8,
      "explanation": "为什么这个触发器会推动升级"
    }}
  ],
  "stalemate_triggers": [],
  "de_escalation_triggers": []
}}
```
"""

CONSTRAINT_EXTRACTION_SYSTEM = """
你是一位专注于战略约束条件分析的研究员。

你的任务是：识别当前事件中各主体面临的具体约束条件——
即什么因素会限制主体的行动选择，或阻止某个方向的发展。

规则：
1. 约束条件必须和具体主体绑定
2. 约束强度要有区分（0~1）
3. 必须说明约束如何发挥作用

输出严格 JSON 格式。
"""

CONSTRAINT_EXTRACTION_USER = """
事件：{event_title}
事件类型：{event_type}
危机阶段：{stage_of_crisis}
主要行为主体（含角色）：{actor_roles}
约束条件列表（粗识别）：{constraints}

请提取具体约束规则。返回 JSON：

```json
{{
  "constraints": [
    {{
      "actor": "受约束的主体",
      "constraint_type": "economic/military_capacity/domestic_political/international_norm/alliance_obligation/nuclear_threshold/geographic",
      "condition_expression": "具体约束描述",
      "strength": 0.7,
      "blocks_direction": "escalation/stalemate/de_escalation/null",
      "explanation": "该约束如何阻止或限制行动"
    }}
  ]
}}
```
"""


# --- 服务函数 ---

def build_scenario_context(
    db: Session,
    event_id: str,
    run_id: str,
) -> Optional[ScenarioContext]:
    """构建推断中间层，有缓存直接返回"""
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        return None

    # 已有上下文直接返回
    existing = db.query(ScenarioContext).filter_by(event_id=event_id, run_id=run_id).first()
    if existing:
        return existing

    logger.info(f"构建推断中间层: {event.event_title}")

    # 生成主体画像
    actor_profiles = _build_actor_profiles(db, event)

    # 提取触发器
    triggers = _extract_triggers(db, event)

    # 提取约束条件
    constraints = _extract_constraints(db, event)

    # 算方向权重
    direction_weights = _compute_direction_weights(triggers, constraints)

    # 创建ScenarioContext
    context = ScenarioContext(
        context_id=str(uuid.uuid4()),
        event_id=event_id,
        run_id=run_id,
        crisis_stage=event.stage_of_crisis or "emergence",
        crisis_stage_rationale=f"基于事件簇分析判断为 {event.stage_of_crisis}",
        actor_profiles_snapshot=[_profile_to_dict(p) for p in actor_profiles],
        active_triggers=[_trigger_to_dict(t) for t in triggers],
        active_constraints=[_constraint_to_dict(c) for c in constraints],
        theory_views={},
        supporting_evidence=event.immediate_triggers or [],
        counter_evidence=[],
        time_horizon="3_months",
        direction_weights=direction_weights,
    )
    db.add(context)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"context commit 失败: {e}")
        return None

    logger.info(f"中间层完成: {direction_weights}")
    return context


def _build_actor_profiles(db: Session, event: AbstractIRGEvent) -> List[ActorProfile]:
    """并行生成主体画像，最多4个同时调"""
    from backend.db.database import SessionLocal

    actor_names = (event.key_actors or [])[:4]

    # 已有画像直接返回
    existing_map: Dict[str, ActorProfile] = {}
    pending_actors: List[str] = []
    for actor_name in actor_names:
        existing = db.query(ActorProfile).filter_by(
            event_id=event.event_id, name=actor_name
        ).first()
        if existing:
            existing_map[actor_name] = existing
        else:
            pending_actors.append(actor_name)

    if not pending_actors:
        return [existing_map[n] for n in actor_names if n in existing_map]

    # 提前取好字段，防跨线程ORM延迟加载
    event_data = {
        "event_id": event.event_id,
        "event_title": event.event_title,
        "event_type": event.event_type,
        "stage_of_crisis": event.stage_of_crisis or "unknown",
        "actor_roles": dict(event.actor_roles or {}),
        "driving_forces": list(event.driving_forces or []),
        "constraints": list(event.constraints or []),
    }

    def run_one_actor(actor_name: str) -> Optional[ActorProfile]:
        """独立session并行安全"""
        thread_db = SessionLocal()
        try:
            actor_role = event_data["actor_roles"].get(actor_name, "参与方")
            user_msg = ACTOR_PROFILE_USER.format(
                event_title=event_data["event_title"],
                event_type=event_data["event_type"],
                stage_of_crisis=event_data["stage_of_crisis"],
                actor_name=actor_name,
                actor_role=actor_role,
                driving_forces=", ".join(event_data["driving_forces"]),
                constraints=", ".join(event_data["constraints"]),
            )
            result = llm_call_json(
                "actor_profile_generation",
                ACTOR_PROFILE_SYSTEM,
                user_msg,
                fallback_value={"name": actor_name, "escalation_tendency": 0.5, "negotiation_tendency": 0.5},
                timeout_seconds=300,
            )
            profile = ActorProfile(
                actor_id=str(uuid.uuid4()),
                event_id=event_data["event_id"],
                name=actor_name,
                actor_type=result.get("actor_type", "state"),
                strategic_interests=result.get("strategic_interests", []),
                red_lines=result.get("red_lines", []),
                preferred_tools=result.get("preferred_tools", []),
                escalation_tendency=float(result.get("escalation_tendency", 0.5)),
                negotiation_tendency=float(result.get("negotiation_tendency", 0.5)),
                domestic_constraints=result.get("domestic_constraints", []),
                alliance_dependencies=result.get("alliance_dependencies", []),
                historical_behavior_patterns=result.get("historical_behavior_patterns", []),
                profile_confidence=float(result.get("profile_confidence", 0.3 if result.get("_fallback_used") else 0.7)),
            )
            thread_db.add(profile)
            thread_db.commit()
            thread_db.refresh(profile)
            return profile
        except Exception as e:
            logger.warning(f"actor {actor_name} 画像生成失败: {e}")
            return None
        finally:
            thread_db.close()

    new_profiles: Dict[str, ActorProfile] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_one_actor, n): n for n in pending_actors}
        for future in as_completed(futures):
            profile = future.result()
            if profile:
                new_profiles[profile.name] = profile

    # 合并保持顺序
    all_profiles = []
    for actor_name in actor_names:
        if actor_name in existing_map:
            all_profiles.append(existing_map[actor_name])
        elif actor_name in new_profiles:
            all_profiles.append(new_profiles[actor_name])

    return all_profiles


def _extract_triggers(db: Session, event: AbstractIRGEvent) -> List[TriggerRule]:
    """提取触发器"""
    from backend.core.prompts.scenario_prompt import EVENT_TYPE_GUIDANCE

    user_msg = TRIGGER_EXTRACTION_USER.format(
        event_title=event.event_title,
        event_type=event.event_type,
        event_type_guidance=EVENT_TYPE_GUIDANCE.get(event.event_type, ""),
        stage_of_crisis=event.stage_of_crisis or "unknown",
        key_actors=", ".join(event.key_actors or []),
        immediate_triggers=", ".join(event.immediate_triggers or []),
        driving_forces=", ".join(event.driving_forces or []),
        major_risks=", ".join(event.major_risks or []),
    )

    result = llm_call_json(
        "trigger_extraction",
        TRIGGER_EXTRACTION_SYSTEM,
        user_msg,
        fallback_value={
            "escalation_triggers": [],
            "stalemate_triggers": [],
            "de_escalation_triggers": [],
        },
        timeout_seconds=300,
    )

    triggers = []
    direction_map = {
        "escalation_triggers": "escalation",
        "stalemate_triggers": "stalemate",
        "de_escalation_triggers": "de_escalation",
    }

    for field, direction in direction_map.items():
        for t_data in result.get(field, []):
            trigger = TriggerRule(
                trigger_id=str(uuid.uuid4()),
                event_id=event.event_id,
                trigger_type=t_data.get("trigger_type", ""),
                actor=t_data.get("actor", ""),
                condition_expression=t_data.get("condition_expression", ""),
                weight=float(t_data.get("weight", 1.0)),
                direction_bias=direction,
                explanation=t_data.get("explanation", ""),
            )
            db.add(trigger)
            triggers.append(trigger)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"触发器 commit 失败: {e}")
    return triggers


def _extract_constraints(db: Session, event: AbstractIRGEvent) -> List[ConstraintRule]:
    """提取约束"""
    actor_roles_str = ", ".join([f"{k}: {v}" for k, v in (event.actor_roles or {}).items()])

    user_msg = CONSTRAINT_EXTRACTION_USER.format(
        event_title=event.event_title,
        event_type=event.event_type,
        stage_of_crisis=event.stage_of_crisis or "unknown",
        actor_roles=actor_roles_str,
        constraints=", ".join(event.constraints or []),
    )

    result = llm_call_json(
        "constraint_extraction",   # 改用独立task_type
        CONSTRAINT_EXTRACTION_SYSTEM,
        user_msg,
        fallback_value={"constraints": []},
        timeout_seconds=300,
    )

    constraint_rules = []
    for c_data in result.get("constraints", []):
        rule = ConstraintRule(
            constraint_id=str(uuid.uuid4()),
            event_id=event.event_id,
            actor=c_data.get("actor", ""),
            constraint_type=c_data.get("constraint_type", ""),
            condition_expression=c_data.get("condition_expression", ""),
            strength=float(c_data.get("strength", 0.7)),
            blocks_direction=c_data.get("blocks_direction") if c_data.get("blocks_direction") != "null" else None,
            explanation=c_data.get("explanation", ""),
        )
        db.add(rule)
        constraint_rules.append(rule)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"约束条件 commit 失败: {e}")
    return constraint_rules


def _compute_direction_weights(
    triggers: List[TriggerRule],
    constraints: List[ConstraintRule],
) -> Dict[str, float]:
    """算方向权重，靠触发器和约束，不靠拍脑袋"""
    raw_weights = {"escalation": 0.0, "stalemate": 0.5, "de_escalation": 0.0}

    # 触发器加权
    for trigger in triggers:
        direction = trigger.direction_bias
        if direction in raw_weights:
            raw_weights[direction] += trigger.weight

    # 约束减权
    for constraint in constraints:
        blocked = constraint.blocks_direction
        if blocked and blocked in raw_weights:
            raw_weights[blocked] -= constraint.strength * 0.5

    # 归一化
    total = sum(max(v, 0.01) for v in raw_weights.values())
    normalized = {k: round(max(v, 0.01) / total, 2) for k, v in raw_weights.items()}

    # 补齐到1
    diff = 1.0 - sum(normalized.values())
    normalized["stalemate"] = round(normalized["stalemate"] + diff, 2)

    return normalized


def get_context(db: Session, event_id: str, run_id: Optional[str] = None) -> Optional[Dict]:
    """获取推断上下文"""
    query = db.query(ScenarioContext).filter_by(event_id=event_id)
    if run_id:
        query = query.filter_by(run_id=run_id)
    ctx = query.first()
    if not ctx:
        return None
    return {
        "context_id": ctx.context_id,
        "event_id": ctx.event_id,
        "crisis_stage": ctx.crisis_stage,
        "crisis_stage_rationale": ctx.crisis_stage_rationale,
        "actor_profiles_snapshot": ctx.actor_profiles_snapshot,
        "active_triggers": ctx.active_triggers,
        "active_constraints": ctx.active_constraints,
        "direction_weights": ctx.direction_weights,
        "time_horizon": ctx.time_horizon,
        "created_at": ctx.created_at.isoformat() if ctx.created_at else None,
    }


def _profile_to_dict(p: ActorProfile) -> dict:
    return {
        "actor_id": p.actor_id,
        "name": p.name,
        "actor_type": p.actor_type,
        "strategic_interests": p.strategic_interests,
        "red_lines": p.red_lines,
        "preferred_tools": p.preferred_tools,
        "escalation_tendency": p.escalation_tendency,
        "negotiation_tendency": p.negotiation_tendency,
        "domestic_constraints": p.domestic_constraints,
        "alliance_dependencies": p.alliance_dependencies,
        "historical_behavior_patterns": p.historical_behavior_patterns,
        "profile_confidence": p.profile_confidence,
    }


def _trigger_to_dict(t: TriggerRule) -> dict:
    return {
        "trigger_id": t.trigger_id,
        "trigger_type": t.trigger_type,
        "actor": t.actor,
        "condition_expression": t.condition_expression,
        "weight": t.weight,
        "direction_bias": t.direction_bias,
        "explanation": t.explanation,
    }


def _constraint_to_dict(c: ConstraintRule) -> dict:
    return {
        "constraint_id": c.constraint_id,
        "actor": c.actor,
        "constraint_type": c.constraint_type,
        "condition_expression": c.condition_expression,
        "strength": c.strength,
        "blocks_direction": c.blocks_direction,
        "explanation": c.explanation,
    }
