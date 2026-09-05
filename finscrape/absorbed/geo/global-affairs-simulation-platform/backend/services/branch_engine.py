"""
分支推演 - 冻结原路径→新建BranchRun→注入推断层重新推演
"""
import uuid
import logging
from typing import Dict, List
from sqlalchemy.orm import Session

from backend.models.prediction import PredictionRun, BranchRun
from backend.models.ir_event import AbstractIRGEvent
from backend.models.scenario import ScenarioScript, ScenarioStep
from backend.core.llm_router import llm_call_json

logger = logging.getLogger(__name__)

BRANCH_SYSTEM_PROMPT = """
你是一位国际关系分析师，正在处理用户对现有推演引入的新假设。

你的任务是：基于用户引入的新假设，重新生成后续3-5步推演，并说明新路径与原路径的关键差异。

规则：
1. 不要忽视新假设的影响
2. 推演步骤必须具体，不是空话
3. 每步必须说明：谁先动、其他方反应、证据和不确定性
4. 必须明确新路径和原路径的分歧点
"""

BRANCH_USER_TEMPLATE = """
原始事件：{event_title}（{event_type}）
当前危机阶段：{stage_of_crisis}
主要行为主体：{key_actors}

【推断层：主体画像摘要（分支剧本必须基于此）】
{actor_profiles_summary}

【推断层：激活的触发器】
{triggers_summary}

【推断层：激活的约束条件】
{constraints_summary}

用户引入的新假设：
假设类型：{hypothesis_type}
假设标题：{hypothesis_title}
假设内容：{hypothesis_description}
预期影响的主体：{affected_actors}
用户预期方向：{expected_direction}

原始推演摘要：
{original_summary}

请基于新假设，生成后续推演路径。步骤必须引用上面的主体画像、触发器和约束条件。
返回如下 JSON：

```json
{{
  "branch_summary": "新分支的总体评估（与原路径的核心差异，具体到主体行为）",
  "divergence_point": "从哪里开始分歧（引用具体触发器或假设内容）",
  "new_direction": "escalation/stalemate/de_escalation",
  "scripts": [
    {{
      "script_title": "新分支剧本名（含主体+行动，不能只说'分支剧本'）",
      "script_description": "剧本描述（100字以上，具体）",
      "why_hypothesis_changes_trajectory": "为什么这个假设改变了推演轨迹（引用约束条件）",
      "trigger_conditions": ["触发条件（引用触发器）"],
      "invalidation_conditions": ["失效条件"],
      "probability_low": 0.15,
      "probability_high": 0.35,
      "probability_central": 0.25,
      "confidence_level": "medium",
      "steps": [
        {{
          "step_number": 1,
          "title": "步骤标题",
          "why_this_step_happens": "因果解释（引用主体画像中的偏好工具/红线）",
          "which_actor_acts_first": "具体主体名称 + 行动原因",
          "how_other_actors_react": {{"主体A": "反应（引用国内约束）", "主体B": "反应"}},
          "key_drivers": ["驱动因素（引用触发器）"],
          "constraints": ["约束条件（引用约束列表）"],
          "supporting_evidence": ["具体证据"],
          "counter_evidence": ["反证"],
          "uncertainty": "不确定性说明",
          "impact_on_next_step": "对下一步的影响"
        }}
      ]
    }}
  ],
  "key_differences_from_original": [
    "与原路径的关键差异1（具体到主体行为）",
    "差异2"
  ]
}}
```
"""


def create_branch(
    db: Session,
    base_run_id: str,
    hypothesis_type: str,
    hypothesis_title: str,
    hypothesis_description: str,
    affected_actors: List[str],
    expected_direction: str,
    introduced_by: str = "user",
) -> Dict:
    """创建分支推演，冻结原run→建BranchRun→调Claude"""
    # 冻结原始run
    base_run = db.query(PredictionRun).filter_by(run_id=base_run_id).first()
    if not base_run:
        raise ValueError(f"PredictionRun {base_run_id} not found")

    base_run.status = "frozen"
    db.commit()

    try:
        event = db.query(AbstractIRGEvent).filter_by(event_id=base_run.event_id).first()
        if not event:
            raise ValueError(f"Event not found for run {base_run_id}")

        branch_run_id = str(uuid.uuid4())
        branch_run = BranchRun(
            branch_run_id=branch_run_id,
            base_run_id=base_run_id,
            event_id=base_run.event_id,
            introduced_by=introduced_by,
            hypothesis_type=hypothesis_type,
            hypothesis_title=hypothesis_title,
            hypothesis_description=hypothesis_description,
            affected_actors=affected_actors,
            expected_direction=expected_direction,
            status="running",
        )
        db.add(branch_run)
        db.commit()

        original_summary = base_run.summary or "原始推演未生成摘要"

        from backend.services.inference_layer_service import get_context
        ctx = get_context(db, base_run.event_id, base_run_id)

        actor_profiles_summary = "（推断层上下文不可用）"
        triggers_summary = "（推断层上下文不可用）"
        constraints_summary = "（推断层上下文不可用）"

        if ctx:
            profiles = ctx.get("actor_profiles_snapshot", [])
            if profiles:
                lines = []
                for p in profiles:
                    esc = p.get('escalation_tendency')
                    neg = p.get('negotiation_tendency')
                    esc_str = f"{esc:.1f}" if isinstance(esc, (int, float)) else str(esc or '?')
                    neg_str = f"{neg:.1f}" if isinstance(neg, (int, float)) else str(neg or '?')
                    lines.append(
                        f"  {p.get('name')}：升级倾向={esc_str} "
                        f"谈判倾向={neg_str} "
                        f"红线={', '.join(p.get('red_lines', [])[:2])} "
                        f"偏好工具={', '.join(p.get('preferred_tools', [])[:2])}"
                    )
                actor_profiles_summary = "\n".join(lines)

            triggers = ctx.get("active_triggers", [])
            if triggers:
                triggers_summary = " | ".join([
                    f"[{t.get('direction_bias')}] {t.get('actor')}: {t.get('condition_expression', '')[:60]}"
                    for t in triggers[:5]
                ])

            constraints = ctx.get("active_constraints", [])
            if constraints:
                constraints_summary = " | ".join([
                    f"{c.get('actor')}: {c.get('condition_expression', '')[:60]} (阻止={c.get('blocks_direction')})"
                    for c in constraints[:5]
                ])

        user_msg = BRANCH_USER_TEMPLATE.format(
            event_title=event.event_title,
            event_type=event.event_type,
            stage_of_crisis=event.stage_of_crisis or "unknown",
            key_actors=", ".join(event.key_actors or []),
            actor_profiles_summary=actor_profiles_summary,
            triggers_summary=triggers_summary,
            constraints_summary=constraints_summary,
            hypothesis_type=hypothesis_type,
            hypothesis_title=hypothesis_title,
            hypothesis_description=hypothesis_description,
            affected_actors=", ".join(affected_actors),
            expected_direction=expected_direction,
            original_summary=original_summary,
        )

        logger.info(f"生成分支推演: {hypothesis_title}")
        result = llm_call_json("branch_regeneration", BRANCH_SYSTEM_PROMPT, user_msg,
                               timeout_seconds=300)

        if result is None or result.get("parse_error"):
            branch_run.status = "error"
            branch_run.diff_summary = "Claude 解析失败"
            base_run.status = "complete"
            db.commit()
            return {"branch_run_id": branch_run_id, "status": "error"}

        script_ids = []
        for script_data in result.get("scripts", []):
            script_id = str(uuid.uuid4())
            script = ScenarioScript(
                script_id=script_id,
                event_id=base_run.event_id,
                run_id=branch_run_id,
                direction_type=result.get("new_direction", expected_direction),
                script_title=script_data.get("script_title", "分支剧本"),
                script_description=script_data.get("script_description", ""),
                why_this_script_is_realistic=script_data.get("why_hypothesis_changes_trajectory", ""),
                trigger_conditions=script_data.get("trigger_conditions", []),
                invalidation_conditions=script_data.get("invalidation_conditions", []),
                supporting_factors=script_data.get("supporting_factors", []),
                opposing_factors=script_data.get("opposing_factors", []),
                uncertainty_notes=script_data.get("uncertainty_notes", ""),
                probability_low=script_data.get("probability_low"),
                probability_high=script_data.get("probability_high"),
                probability_central=script_data.get("probability_central"),
                confidence_level=script_data.get("confidence_level", "medium"),
                is_branch=True,
            )
            db.add(script)
            script_ids.append(script_id)

            for step_data in script_data.get("steps", []):
                step = ScenarioStep(
                    step_id=str(uuid.uuid4()),
                    script_id=script_id,
                    step_number=step_data.get("step_number", 0),
                    title=step_data.get("title", ""),
                    why_this_step_happens=step_data.get("why_this_step_happens", ""),
                    which_actor_acts_first=step_data.get("which_actor_acts_first", ""),
                    how_other_actors_react=step_data.get("how_other_actors_react", {}),
                    key_drivers=step_data.get("key_drivers", []),
                    constraints=step_data.get("constraints", []),
                    supporting_evidence=step_data.get("supporting_evidence", []),
                    counter_evidence=step_data.get("counter_evidence", []),
                    uncertainty=step_data.get("uncertainty", ""),
                    impact_on_next_step=step_data.get("impact_on_next_step", ""),
                    node_type="user_hypothesis_node",
                )
                db.add(step)

        branch_run.status = "complete"
        branch_run.branch_script_ids = script_ids
        branch_run.diff_summary = result.get("branch_summary", "")
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            base_run.status = "complete"
            db.commit()
            raise RuntimeError(f"[branch] 分支状态 commit 失败: {e}") from e

        logger.info(f"分支完成: {branch_run_id}")
        return {
            "branch_run_id": branch_run_id,
            "base_run_id": base_run_id,
            "status": "complete",
            "branch_summary": result.get("branch_summary", ""),
            "divergence_point": result.get("divergence_point", ""),
            "key_differences": result.get("key_differences_from_original", []),
            "script_ids": script_ids,
        }
    except Exception:
        base_run.status = "complete"
        db.commit()
        raise
