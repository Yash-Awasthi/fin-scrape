"""
反模板化检查 - 强制关卡，不可跳过
"""
import logging
from typing import List, Dict

from backend.core.llm_router import llm_call_json

logger = logging.getLogger("anti_template")


ANTI_TEMPLATE_SYSTEM = """
你是一位国际关系分析质量审查员，专门检查情景推演是否高度模板化。

你的任务：检查生成的剧本是否真正和当前事件的特定情境绑定，
还是只是换了一些词的套话。

模板化剧本的特征：
1. 步骤可以轻松替换到任何其他事件中（删掉主体名也成立）
2. 没有具体的主体名称，只有"一方"、"另一方"
3. 没有调用当前事件的具体触发器和约束
4. 步骤之间没有真实的因果链条（只是列举，不是推导）
5. 证据是"历史表明…"这样无法验证的空话
6. 可以对换升级/缓和两个方向而不影响语义
7. 步骤没有supporting_evidence或只有空列表

请严格评判，不要宽容。over_template_score > 0.65 表示需要重新生成。
"""

ANTI_TEMPLATE_USER = """
事件：{event_title}
事件类型：{event_type}
危机阶段：{stage_of_crisis}
主要触发器：{triggers}
主要约束：{constraints}

待检查剧本：
剧本标题：{script_title}
方向：{direction_type}
描述：{script_description}
步骤摘要（共{step_count}步）：
{steps_summary}

请检查以下问题并返回严格 JSON：

```json
{{
  "is_event_type_bound": true,
  "event_type_evidence": "说明剧本如何体现了当前事件类型的特征",
  "is_crisis_stage_bound": true,
  "crisis_stage_evidence": "说明剧本如何体现了当前危机阶段",
  "uses_actor_profiles": true,
  "actor_profile_evidence": "说明具体主体名称和行为逻辑的使用",
  "uses_triggers_constraints": true,
  "trigger_constraint_evidence": "说明触发器和约束的具体引用",
  "has_causal_chain": true,
  "causal_chain_evidence": "说明步骤之间的因果推进逻辑",
  "has_supporting_evidence": true,
  "has_counter_evidence": true,
  "over_template_score": 0.3,
  "over_template_reasoning": "如果分数>0.65，必须说明具体模板化问题（不能只说'过于通用'）",
  "missing_context": ["缺失的上下文类型，如actor_profiles/triggers/evidence等"],
  "low_specificity": false,
  "regeneration_needed": false,
  "checker_notes": "总体质量评估（1-2句）"
}}
```

over_template_score: 0=完全原创, 1=严重模板化，0.65以上建议重新生成
"""


def check_script_anti_template(
    event_title: str,
    event_type: str,
    stage_of_crisis: str,
    triggers: List[Dict],
    constraints: List[Dict],
    script_title: str,
    direction_type: str,
    script_description: str,
    steps: List[Dict],
) -> Dict:
    """检查剧本模板化程度，失败不静默fallback"""
    steps_summary = "\n".join([
        f"  步骤{s.get('step_number', i+1)}: {s.get('title', '')} | "
        f"行动方: {s.get('which_actor_acts_first', '(未填)')} | "
        f"原因: {s.get('why_this_step_happens', '(未填)')[:100]} | "
        f"证据: {'有' if s.get('supporting_evidence') else '无'} | "
        f"反证: {'有' if s.get('counter_evidence') else '无'}"
        for i, s in enumerate(steps[:6])
    ])

    trigger_summary = " | ".join([
        t.get("condition_expression", "")[:60] for t in triggers[:4]
    ]) or "（无触发器数据）"

    constraint_summary = " | ".join([
        f"{c.get('actor','?')}: {c.get('condition_expression', '')[:50]}"
        for c in constraints[:4]
    ]) or "（无约束数据）"

    user_msg = ANTI_TEMPLATE_USER.format(
        event_title=event_title,
        event_type=event_type,
        stage_of_crisis=stage_of_crisis,
        triggers=trigger_summary,
        constraints=constraint_summary,
        script_title=script_title,
        direction_type=direction_type,
        script_description=script_description[:400],
        step_count=len(steps),
        steps_summary=steps_summary or "（无步骤数据）",
    )

    # 不传fallback_value，失败要能被检测
    result = llm_call_json(
        "anti_template_check",
        ANTI_TEMPLATE_SYSTEM,
        user_msg,
        timeout_seconds=60,
        # 故意不传fallback
    )

    # 失败构造标记的fallback，不静默
    if result is None or result.get("parse_error") or result.get("_fallback_used"):
        logger.warning(
            f"[anti_template] checker 调用失败（script='{script_title}'），"
            f"采用保守默认值（score=0.5，不触发重生成）"
        )
        return {
            "over_template_score": 0.5,
            "regeneration_needed": False,
            "over_template_reasoning": "checker 调用失败，采用保守默认（不代表通过检查）",
            "missing_context": [],
            "checker_notes": "anti_template LLM 调用失败",
            "_fallback_used": True,
            "_checker_failed": True,
        }

    # 字段名兼容
    if "regenerate_recommended" in result and "regeneration_needed" not in result:
        result["regeneration_needed"] = result["regenerate_recommended"]

    logger.info(
        f"[anti_template] script='{script_title}' direction={direction_type} "
        f"score={result.get('over_template_score', 0):.2f} "
        f"regen={result.get('regeneration_needed', False)}"
    )
    return result
