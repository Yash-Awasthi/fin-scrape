"""
多剧本推演引擎 - 约束式生成+强制反模板检查
"""
import uuid
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.models.ir_event import AbstractIRGEvent
from backend.models.scenario import ScenarioScript, ScenarioStep
from backend.core.llm_router import llm_call_json
from backend.core.prompts import SCENARIO_SYSTEM_PROMPT, EVENT_TYPE_GUIDANCE
from backend.services.inference_layer_service import build_scenario_context, get_context
from backend.services.analogy_engine import build_analogy_context_for_scenario

logger = logging.getLogger("scenario")


def _clamp_prob(value, default=0.5):
    if value is None:
        return default
    try:
        v = float(value)
        return max(0.0, min(1.0, v))
    except (TypeError, ValueError):
        return default

# 反模板阈值
ANTI_TEMPLATE_THRESHOLD = 0.65
# 最多重生成1次，每次300s
MAX_REGENERATION_ATTEMPTS = 1


# 整合推断中间层的Prompt
CONSTRAINED_SCENARIO_USER_TEMPLATE = """
事件标题：{event_title}
事件类型：{event_type}（{event_type_guidance}）
危机阶段：{crisis_stage}
主要行为主体：{key_actors}
主体角色：{actor_roles}
主要地点：{key_locations}
战略维度：{strategic_dimensions}

【推断中间层 - 主体画像（必须在剧本中体现）】
{actor_profiles_summary}

【推断中间层 - 激活的触发器（剧本步骤必须引用）】
{triggers_summary}

【推断中间层 - 激活的约束条件（必须体现在"为什么该步骤不会走极端"）】
{constraints_summary}

【方向权重参考（基于触发器和约束计算，不是拍脑袋）】
升级方向基础权重: {escalation_weight}
僵持方向基础权重: {stalemate_weight}
缓和方向基础权重: {de_escalation_weight}

{analogy_context}

驱动力：{driving_forces}
主要风险：{major_risks}
当前机会：{current_opportunities}
当前力量对比：{current_balance}
推演时间视野：{time_horizon}

【重要要求】
1. 剧本标题必须具体（必须含主体名+行动，禁止"升级剧本A"此类废话）
2. 每个方向生成1个最可能的剧本（共3个）
3. 每个剧本5个推演步骤（不少于5步）
4. 每步必须体现上面的主体画像、触发器和约束条件
5. 每步必须有 supporting_evidence（具体证据）和 counter_evidence（反证）

返回 JSON：

```json
{{
  "direction_groups": [
    {{
      "direction_type": "escalation",
      "direction_rationale": "为什么升级是可能方向（引用触发器）",
      "scripts": [
        {{
          "script_title": "具体剧本名称（含主体+行动，禁用'升级剧本A'此类废话）",
          "script_description": "剧本总体描述（100字以上，必须具体到当前事件）",
          "why_this_script_is_realistic": "为什么现实（引用主体画像和触发器）",
          "trigger_conditions": ["引用上面触发器的具体条件"],
          "invalidation_conditions": ["什么条件会使这个剧本不成立"],
          "supporting_factors": ["支持因素（具体到主体和行动）"],
          "opposing_factors": ["反对因素（具体）"],
          "probability_low": 0.10,
          "probability_high": 0.25,
          "probability_central": 0.17,
          "confidence_level": "medium",
          "uncertainty_notes": "主要不确定性来源",
          "steps": [
            {{
              "step_number": 1,
              "title": "步骤标题",
              "why_this_step_happens": "因果解释（引用主体画像中的偏好工具/红线/国内约束）",
              "which_actor_acts_first": "具体主体名称 + 行动原因",
              "how_other_actors_react": {{
                "主体A": "反应描述（引用其国内约束和偏好工具）",
                "主体B": "反应描述"
              }},
              "key_drivers": ["引用上面触发器条目"],
              "constraints": ["引用上面约束条目"],
              "supporting_evidence": ["具体证据（历史先例或当前数据，不是套话）"],
              "counter_evidence": ["反证（为什么这步不一定发生）"],
              "uncertainty": "本步骤主要不确定性",
              "impact_on_next_step": "如何影响下一步"
            }}
          ]
        }}
      ]
    }},
    {{
      "direction_type": "stalemate",
      "direction_rationale": "为什么僵持是可能方向",
      "scripts": []
    }},
    {{
      "direction_type": "de_escalation",
      "direction_rationale": "为什么缓和是可能方向",
      "scripts": []
    }}
  ],
  "overall_assessment": "三个方向相对可能性的总体评估"
}}
```
"""


def run_scenario_engine(db: Session, event_id: str, run_id: str,
                        skip_heavy_prep: bool = True) -> List[Dict]:
    """多方向多剧本推演，skip_heavy_prep=True跳过LLM构建省调用"""
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        return []

    # 推断中间层：pipeline模式跳LLM用默认权重
    if not skip_heavy_prep:
        logger.info("[scenario] 构建推断中间层...")
        ctx_obj = build_scenario_context(db, event_id, run_id)
        # ORM对象转dict
        context = {
            "direction_weights": ctx_obj.direction_weights if ctx_obj else None,
            "actor_profiles_snapshot": ctx_obj.actor_profiles_snapshot if ctx_obj else [],
            "active_triggers": ctx_obj.active_triggers if ctx_obj else [],
            "active_constraints": ctx_obj.active_constraints if ctx_obj else [],
            "time_horizon": ctx_obj.time_horizon if ctx_obj else "3_months",
            "crisis_stage": ctx_obj.crisis_stage if ctx_obj else None,
        } if ctx_obj else None
    else:
        context = get_context(db, event_id, run_id)  # 已是 dict

    direction_weights = context.get("direction_weights") if context else None
    direction_weights = direction_weights or {"escalation": 0.33, "stalemate": 0.34, "de_escalation": 0.33}

    # 主体画像摘要
    actor_profiles_summary = ""
    if context and context.get("actor_profiles_snapshot"):
        lines = []
        for p in context["actor_profiles_snapshot"]:
            lines.append(
                f"  {p.get('name')}：\n"
                f"    升级倾向={p.get('escalation_tendency', 0.5):.1f} 谈判倾向={p.get('negotiation_tendency', 0.5):.1f}\n"
                f"    红线：{', '.join(p.get('red_lines', [])[:2])}\n"
                f"    偏好工具：{', '.join(p.get('preferred_tools', [])[:2])}\n"
                f"    国内约束：{', '.join(p.get('domestic_constraints', [])[:2])}"
            )
        actor_profiles_summary = "\n".join(lines)

    # 触发器摘要
    triggers_summary = ""
    if context and context.get("active_triggers"):
        lines = []
        for t in context["active_triggers"][:6]:
            lines.append(
                f"  [{t.get('direction_bias')}] {t.get('actor')}: "
                f"{t.get('condition_expression')} (权重={t.get('weight')})"
            )
        triggers_summary = "\n".join(lines)

    # 约束摘要
    constraints_summary = ""
    if context and context.get("active_constraints"):
        lines = []
        for c in context["active_constraints"][:6]:
            lines.append(
                f"  {c.get('actor')}: {c.get('condition_expression')} "
                f"(强度={c.get('strength')} 阻止={c.get('blocks_direction')})"
            )
        constraints_summary = "\n".join(lines)

    # 事件类型指导
    event_type_guide = EVENT_TYPE_GUIDANCE.get(event.event_type, "")

    # 历史类比：pipeline模式跳过
    if not skip_heavy_prep:
        logger.info("[scenario] 注入历史类比上下文...")
        analogy_context = build_analogy_context_for_scenario(event_id, db)
    else:
        analogy_context = ""  # pipeline模式不额外调LLM

    # 构建Prompt
    user_msg = CONSTRAINED_SCENARIO_USER_TEMPLATE.format(
        event_title=event.event_title,
        event_type=event.event_type,
        event_type_guidance=event_type_guide,
        crisis_stage=event.stage_of_crisis or "unknown",
        key_actors=", ".join(event.key_actors or []),
        actor_roles=str(event.actor_roles or {}),
        key_locations=", ".join(event.key_locations or []),
        strategic_dimensions=", ".join(event.strategic_dimensions or []),
        actor_profiles_summary=actor_profiles_summary or "（主体画像生成中）",
        triggers_summary=triggers_summary or "（触发器提取中）",
        constraints_summary=constraints_summary or "（约束条件提取中）",
        escalation_weight=direction_weights.get("escalation", 0.33),
        stalemate_weight=direction_weights.get("stalemate", 0.34),
        de_escalation_weight=direction_weights.get("de_escalation", 0.33),
        analogy_context=analogy_context,
        driving_forces=", ".join(event.driving_forces or []),
        major_risks=", ".join(event.major_risks or []),
        current_opportunities=", ".join(event.current_opportunities or []),
        current_balance=event.current_balance or "未知",
        time_horizon=context.get("time_horizon", "3_months") if context else "3_months",
    )

    logger.info("[scenario] 约束式推演: %s", event.event_title)
    result = llm_call_json(
        "scenario_generation",
        SCENARIO_SYSTEM_PROMPT,
        user_msg,
        timeout_seconds=300,   # 失败走回退不重试
    )

    if result is None or result.get("parse_error"):
        logger.info("[scenario] Claude 解析失败，使用回退剧本")
        return _fallback_scenarios(db, event, run_id)

    # 内部已逐个commit
    all_scripts = []
    for direction_group in result.get("direction_groups", []):
        direction_type = direction_group.get("direction_type", "stalemate")

        for script_data in direction_group.get("scripts", []):
            saved = _save_script_from_data(db, event_id, run_id, direction_type, script_data)
            if saved:
                all_scripts.append(saved)

    # 不再重复commit，_save_script_from_data已commit
    logger.info("[scenario] 初始生成: %d 个剧本，开始强制反模板检查...", len(all_scripts))

    # --- 强制反模板检查 ---
    all_scripts = _mandatory_anti_template_pass(
        db=db,
        event=event,
        run_id=run_id,
        scripts=all_scripts,
        context=context,
        user_msg_template=(
            CONSTRAINED_SCENARIO_USER_TEMPLATE,
            {
                "event_title": event.event_title,
                "event_type": event.event_type,
                "event_type_guidance": EVENT_TYPE_GUIDANCE.get(event.event_type, ""),
                "crisis_stage": event.stage_of_crisis or "unknown",
                "key_actors": ", ".join(event.key_actors or []),
                "actor_roles": str(event.actor_roles or {}),
                "key_locations": ", ".join(event.key_locations or []),
                "strategic_dimensions": ", ".join(event.strategic_dimensions or []),
                "actor_profiles_summary": actor_profiles_summary or "（主体画像生成中）",
                "triggers_summary": triggers_summary or "（触发器提取中）",
                "constraints_summary": constraints_summary or "（约束条件提取中）",
                "escalation_weight": direction_weights.get("escalation", 0.33),
                "stalemate_weight": direction_weights.get("stalemate", 0.34),
                "de_escalation_weight": direction_weights.get("de_escalation", 0.33),
                "analogy_context": analogy_context,   # 补上类比上下文
                "driving_forces": ", ".join(event.driving_forces or []),
                "major_risks": ", ".join(event.major_risks or []),
                "current_opportunities": ", ".join(event.current_opportunities or []),
                "current_balance": event.current_balance or "未知",
                "time_horizon": (context.get("time_horizon", "3_months") if isinstance(context, dict) else getattr(context, 'time_horizon', '3_months')),
            },
        ),
    )

    logger.info("[scenario] 最终完成: %d 个剧本（含反模板验证）", len(all_scripts))
    return all_scripts


def _mandatory_anti_template_pass(
    db: Session,
    event: AbstractIRGEvent,
    run_id: str,
    scripts: List[Dict],
    context,
    user_msg_template: tuple,
) -> List[Dict]:
    """强制反模板检查，超阈值重生成，仍不过降级，整体超时300s熔断"""
    import time as _time
    from backend.services.anti_template_service import check_script_anti_template

    pass_start = _time.time()
    ANTI_TEMPLATE_PASS_TIMEOUT = 300  # 整个检查阶段最多300s

    triggers = []
    constraints_list = []
    if context:
        triggers = context.get("active_triggers") or []
        constraints_list = context.get("active_constraints") or []

    validated_scripts = []

    for script_dict in scripts:
        # 熔断：超时直接通过
        elapsed = _time.time() - pass_start
        if elapsed > ANTI_TEMPLATE_PASS_TIMEOUT:
            logger.warning(
                f"[anti_template] 检查阶段超时（{elapsed:.0f}s > {ANTI_TEMPLATE_PASS_TIMEOUT}s），"
                f"剩余 {len(scripts) - len(validated_scripts)} 个脚本跳过检查直接通过"
            )
            script_dict["over_template_flagged"] = False
            script_dict.setdefault("anti_template_check", {
                "over_template_score": 0.5,
                "regenerate_recommended": False,
                "over_template_reasoning": "检查阶段超时，已跳过",
            })
            validated_scripts.append(script_dict)
            continue

        script_id = script_dict["script_id"]
        # 步骤已commit可查库，内存有steps优先用
        steps = script_dict.get("steps") or _get_steps_for_script(db, script_id)

        check_result = check_script_anti_template(
            event_title=event.event_title,
            event_type=event.event_type,
            stage_of_crisis=event.stage_of_crisis or "unknown",
            triggers=triggers,
            constraints=constraints_list,
            script_title=script_dict.get("script_title", ""),
            direction_type=script_dict.get("direction_type", ""),
            script_description=script_dict.get("script_description", ""),
            steps=steps,
        )

        score = check_result.get("over_template_score", 0.0)
        script_dict["anti_template_check"] = {
            "over_template_score": score,
            "regenerate_recommended": check_result.get("regenerate_recommended", False),
            "over_template_reasoning": check_result.get("over_template_reasoning", ""),
        }

        if score > ANTI_TEMPLATE_THRESHOLD:
            logger.warning(
                f"[anti_template] 剧本 '{script_dict.get('script_title')}' "
                f"模板化评分 {score:.2f} 超过阈值 {ANTI_TEMPLATE_THRESHOLD}，触发重新生成"
            )
            # 尝试重生成
            regenerated = _attempt_regenerate_script(
                db=db,
                event=event,
                run_id=run_id,
                original_script=script_dict,
                user_msg_template=user_msg_template,
                triggers=triggers,
                constraints_list=constraints_list,
            )
            if regenerated:
                validated_scripts.append(regenerated)
            else:
                # 重生成失败，降级
                logger.warning(
                    f"[anti_template] 重新生成失败，剧本 '{script_dict.get('script_title')}' 降级为 low_confidence"
                )
                _downgrade_script_confidence(db, script_id, score)
                script_dict["confidence_level"] = "low"
                script_dict["over_template_flagged"] = True
                script_dict["anti_template_check"]["note"] = "已降级为low_confidence（重新生成失败）"
                validated_scripts.append(script_dict)
        else:
            script_dict["over_template_flagged"] = False
            validated_scripts.append(script_dict)

    return validated_scripts


def _get_steps_for_script(db: Session, script_id: str) -> List[Dict]:
    """获取剧本步骤"""
    steps = db.query(ScenarioStep).filter_by(script_id=script_id).order_by(ScenarioStep.step_number).all()
    return [_step_to_dict(s) for s in steps]


def _attempt_regenerate_script(
    db: Session,
    event: AbstractIRGEvent,
    run_id: str,
    original_script: Dict,
    user_msg_template: tuple,
    triggers: List,
    constraints_list: List,
) -> Optional[Dict]:
    """重生成单方向剧本，强调上次太模板"""
    from backend.services.anti_template_service import check_script_anti_template

    template_str, template_kwargs = user_msg_template
    direction = original_script.get("direction_type", "stalemate")

    regen_extra = f"""
【重新生成指令 - 上一版本模板化评分过高】
原剧本：{original_script.get('script_title')}
模板化原因：{original_script.get('anti_template_check', {}).get('over_template_reasoning', '过于通用')}

请特别注意：
- 必须使用具体主体名称（不得说"一方"、"对方"）
- 步骤必须引用触发器和约束的具体内容
- 每步必须有不可替换的具体证据
- 只生成 {direction} 方向的 1 个剧本
"""

    user_msg = template_str.format(**template_kwargs) + regen_extra

    for attempt in range(MAX_REGENERATION_ATTEMPTS):
        logger.info(f"[anti_template] 重新生成 {direction} 方向剧本（第{attempt+1}次）")
        result = llm_call_json("scenario_generation", SCENARIO_SYSTEM_PROMPT, user_msg,
                               timeout_seconds=300)

        if result is None or result.get("parse_error"):
            continue

        # 找目标方向
        for group in result.get("direction_groups", []):
            if group.get("direction_type") != direction:
                continue
            for script_data in group.get("scripts", []):
                # 反模板检查
                steps_data = script_data.get("steps", [])
                check = check_script_anti_template(
                    event_title=event.event_title,
                    event_type=event.event_type,
                    stage_of_crisis=event.stage_of_crisis or "unknown",
                    triggers=triggers,
                    constraints=constraints_list,
                    script_title=script_data.get("script_title", ""),
                    direction_type=direction,
                    script_description=script_data.get("script_description", ""),
                    steps=steps_data,
                )
                new_score = check.get("over_template_score", 0.0)

                if new_score <= ANTI_TEMPLATE_THRESHOLD:
                    # 通过检查，保存
                    new_script = _save_script_from_data(db, event.event_id, run_id, direction, script_data)
                    if new_script:
                        # 删旧剧本
                        old = db.query(ScenarioScript).filter_by(script_id=original_script["script_id"]).first()
                        if old:
                            db.query(ScenarioStep).filter_by(script_id=old.script_id).delete()
                            db.delete(old)
                            try:
                                db.commit()
                            except Exception:
                                db.rollback()
                        new_script["anti_template_check"] = {
                            "over_template_score": new_score,
                            "regenerate_recommended": False,
                            "over_template_reasoning": "重新生成后通过检查",
                            "regeneration_attempt": attempt + 1,
                        }
                        new_script["over_template_flagged"] = False
                        return new_script
    return None


def _save_script_from_data(
    db: Session, event_id: str, run_id: str, direction_type: str, script_data: Dict
) -> Optional[Dict]:
    """保存单个剧本到库"""
    try:
        script_id = str(uuid.uuid4())
        script = ScenarioScript(
            script_id=script_id,
            event_id=event_id,
            run_id=run_id,
            direction_type=direction_type,
            script_title=script_data.get("script_title", "重生成剧本"),
            script_description=script_data.get("script_description", ""),
            why_this_script_is_realistic=script_data.get("why_this_script_is_realistic", ""),
            trigger_conditions=script_data.get("trigger_conditions", []),
            invalidation_conditions=script_data.get("invalidation_conditions", []),
            supporting_factors=script_data.get("supporting_factors", []),
            opposing_factors=script_data.get("opposing_factors", []),
            probability_low=_clamp_prob(script_data.get("probability_low")),
            probability_high=_clamp_prob(script_data.get("probability_high")),
            probability_central=_clamp_prob(script_data.get("probability_central")),
            confidence_level=script_data.get("confidence_level", "medium"),
            uncertainty_notes=script_data.get("uncertainty_notes", ""),
        )
        db.add(script)
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
            )
            db.add(step)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        # 步骤附到dict上供反模板检查用，免得再查库
        script_result = _script_to_dict(script)
        script_result["steps"] = [_step_to_dict_from_data(sd) for sd in script_data.get("steps", [])]
        return script_result
    except Exception as e:
        logger.error(f"[scenario] 保存重生成剧本失败: {e}")
        db.rollback()
        return None


def _downgrade_script_confidence(db: Session, script_id: str, score: float):
    """降级为low_confidence"""
    script = db.query(ScenarioScript).filter_by(script_id=script_id).first()
    if script:
        script.confidence_level = "low"
        script.uncertainty_notes = (
            f"{script.uncertainty_notes or ''} [反模板评分={score:.2f}，已降级]"
        )
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise


def get_scripts_for_event(db: Session, event_id: str, run_id: Optional[str] = None) -> List[Dict]:
    """获取事件所有剧本含步骤"""
    query = db.query(ScenarioScript).filter_by(event_id=event_id)
    if run_id:
        query = query.filter_by(run_id=run_id)
    scripts = query.all()

    result = []
    for script in scripts:
        script_dict = _script_to_dict(script)
        steps = db.query(ScenarioStep).filter_by(script_id=script.script_id).order_by(ScenarioStep.step_number).all()
        script_dict["steps"] = [_step_to_dict(s) for s in steps]
        result.append(script_dict)

    return result


def _fallback_scenarios(db: Session, event: AbstractIRGEvent, run_id: str) -> List[Dict]:
    """回退剧本"""
    directions = ["escalation", "stalemate", "de_escalation"]
    titles = {
        "escalation": "局势升级路径",
        "stalemate": "长期僵持路径",
        "de_escalation": "逐步缓和路径",
    }
    scripts = []
    for direction in directions:
        script_id = str(uuid.uuid4())
        script = ScenarioScript(
            script_id=script_id,
            event_id=event.event_id,
            run_id=run_id,
            direction_type=direction,
            script_title=titles[direction],
            script_description="（回退生成，需人工补充）",
            probability_low=0.1,
            probability_high=0.5,
            probability_central=0.33,
            confidence_level="low",
            uncertainty_notes="Claude API 解析失败，概率和步骤需人工完善",
        )
        db.add(script)

        for i in range(1, 4):
            step = ScenarioStep(
                step_id=str(uuid.uuid4()),
                script_id=script_id,
                step_number=i,
                title=f"阶段 {i}（待完善）",
                why_this_step_happens="待分析",
                which_actor_acts_first="待判断",
                uncertainty="完整分析需 Claude API 支持",
            )
            db.add(step)
        scripts.append(_script_to_dict(script))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return scripts


def _script_to_dict(script: ScenarioScript) -> Dict:
    return {
        "script_id": script.script_id,
        "event_id": script.event_id,
        "run_id": script.run_id,
        "direction_type": script.direction_type,
        "script_title": script.script_title,
        "script_description": script.script_description,
        "why_this_script_is_realistic": script.why_this_script_is_realistic,
        "trigger_conditions": script.trigger_conditions,
        "invalidation_conditions": script.invalidation_conditions,
        "supporting_factors": script.supporting_factors,
        "opposing_factors": script.opposing_factors,
        "probability_low": script.probability_low,
        "probability_high": script.probability_high,
        "probability_central": script.probability_central,
        "confidence_level": script.confidence_level,
        "uncertainty_notes": script.uncertainty_notes,
        "is_branch": script.is_branch,
        "created_at": script.created_at.isoformat() if script.created_at else None,
    }


def _step_to_dict(step: ScenarioStep) -> Dict:
    return {
        "step_id": step.step_id,
        "script_id": step.script_id,
        "step_number": step.step_number,
        "title": step.title,
        "why_this_step_happens": step.why_this_step_happens,
        "which_actor_acts_first": step.which_actor_acts_first,
        "how_other_actors_react": step.how_other_actors_react,
        "key_drivers": step.key_drivers,
        "constraints": step.constraints,
        "supporting_evidence": step.supporting_evidence,
        "counter_evidence": step.counter_evidence,
        "uncertainty": step.uncertainty,
        "impact_on_next_step": step.impact_on_next_step,
        "node_type": step.node_type,
    }


def _step_to_dict_from_data(step_data: Dict) -> Dict:
    """步骤dict转标准格式，不依赖ORM"""
    return {
        "step_id": step_data.get("step_id", ""),
        "script_id": step_data.get("script_id", ""),
        "step_number": step_data.get("step_number", 0),
        "title": step_data.get("title", ""),
        "why_this_step_happens": step_data.get("why_this_step_happens", ""),
        "which_actor_acts_first": step_data.get("which_actor_acts_first", ""),
        "how_other_actors_react": step_data.get("how_other_actors_react", {}),
        "key_drivers": step_data.get("key_drivers", []),
        "constraints": step_data.get("constraints", []),
        "supporting_evidence": step_data.get("supporting_evidence", []),
        "counter_evidence": step_data.get("counter_evidence", []),
        "uncertainty": step_data.get("uncertainty", ""),
        "impact_on_next_step": step_data.get("impact_on_next_step", ""),
        "node_type": None,
    }
