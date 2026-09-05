"""预测校准追踪 - Brier分数/命中率/理论准确度"""
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from sqlalchemy.orm import Session

from backend.models.outcome import ActualOutcome, PredictionEvaluation
from backend.models.prediction import PredictionRun
from backend.models.scenario import ScenarioScript
from backend.models.ir_event import AbstractIRGEvent
from backend.models.theory_analysis import TheoryAnalysis, THEORY_DISPLAY_NAMES

logger = logging.getLogger("calibration")


# --- 核心指标 ---

def compute_brier_score(
    predicted_probability: float,
    actual_outcome: int,  # 1=发生, 0=未发生
) -> float:
    """Brier分数，越小越好，0=完美0.25=随机"""
    return (predicted_probability - actual_outcome) ** 2


def compute_calibration_summary(db: Session) -> Dict:
    """全局校准摘要"""
    try:
        evaluations = db.query(PredictionEvaluation).all()
    except Exception as e:
        logger.error(f"[calibration] 读取评估数据失败: {e}")
        return _empty_calibration_summary()

    if not evaluations:
        return _empty_calibration_summary()

    # 基本命中率
    total = len(evaluations)
    script_hits = sum(1 for e in evaluations if e.script_hit)
    script_hit_rate = script_hits / total if total > 0 else 0.0

    # 平均步骤命中率
    node_rates = [e.node_hit_rate for e in evaluations if e.node_hit_rate is not None]
    avg_node_hit_rate = sum(node_rates) / len(node_rates) if node_rates else 0.0

    # 平均校准误差
    cal_errors = [e.calibration_error for e in evaluations if e.calibration_error is not None]
    avg_calibration_error = sum(cal_errors) / len(cal_errors) if cal_errors else None

    try:
        # 错误类型分布
        error_dist = _compute_error_distribution(evaluations)

        # 批量加载 runs 和 events，避免 N+1
        run_ids = list({e.run_id for e in evaluations if e.run_id})
        runs_map = {
            r.run_id: r
            for r in db.query(PredictionRun).filter(PredictionRun.run_id.in_(run_ids)).all()
        }
        event_ids = list({r.event_id for r in runs_map.values() if r.event_id})
        events_map = {
            ev.event_id: ev
            for ev in db.query(AbstractIRGEvent).filter(AbstractIRGEvent.event_id.in_(event_ids)).all()
        }

        # 按事件类型分组
        by_event_type = _compute_by_event_type_batch(evaluations, runs_map, events_map)

        # 按危机阶段
        by_crisis_stage = _compute_by_crisis_stage_batch(evaluations, runs_map, events_map)

        # 按月趋势
        time_trend = _compute_time_trend(evaluations)

        # 整体 Brier 估算
        brier_estimate = _estimate_overall_brier(db, evaluations)

        # 理论准确度
        theory_accuracy = _compute_theory_accuracy_batch(db, evaluations, runs_map)

    except Exception as e:
        logger.error(f"[calibration] 校准摘要计算部分失败: {e}")
        error_dist = {}
        by_event_type = {}
        by_crisis_stage = {}
        time_trend = []
        brier_estimate = None
        theory_accuracy = {}

    grade_info = _compute_calibration_grade(script_hit_rate, avg_node_hit_rate)

    return {
        "total_evaluations": total,
        "script_hit_rate": round(script_hit_rate, 3),
        "script_hit_count": script_hits,
        "avg_node_hit_rate": round(avg_node_hit_rate, 3),
        "avg_calibration_error": round(avg_calibration_error, 3) if avg_calibration_error is not None else None,
        "avg_brier_score": round(brier_estimate, 3) if brier_estimate is not None else None,
        "overall_brier_score": round(brier_estimate, 3) if brier_estimate is not None else None,
        "error_distribution": error_dist,
        "by_event_type": by_event_type,
        "by_crisis_stage": by_crisis_stage,
        "time_trend": time_trend,
        "theory_accuracy": theory_accuracy,
        "calibration_grade": grade_info["grade"],
        "combined_score": grade_info["combined_score"],
        "improvement_suggestions": _generate_improvement_suggestions(error_dist, by_event_type),
    }


def get_run_calibration_detail(db: Session, run_id: str) -> Optional[Dict]:
    """单次推演的校准详情"""
    run = db.query(PredictionRun).filter_by(run_id=run_id).first()
    if not run:
        return None

    evaluation = db.query(PredictionEvaluation).filter_by(run_id=run_id).first()
    outcome = db.query(ActualOutcome).filter_by(related_run_id=run_id).first()

    # 按event_id查，run_id在ScenarioScript上可空
    # 然后Python里再按run_id筛，优先匹配的
    all_scripts = db.query(ScenarioScript).filter(
        ScenarioScript.event_id == run.event_id,
    ).all()
    # 优先本run的剧本，没有就用事件的
    run_scripts = [s for s in all_scripts if s.run_id == run_id]
    scripts = run_scripts if run_scripts else all_scripts

    matched_script_id = evaluation.matched_script_id if evaluation else None

    script_details = []
    for script in scripts:
        is_hit = (
            matched_script_id == script.script_id and
            evaluation is not None and
            evaluation.script_hit
        )
        prob = script.probability_central or 0.0
        # 只对命中的剧本算Brier
        if matched_script_id == script.script_id and prob > 0:
            brier = compute_brier_score(prob, 1 if is_hit else 0)
        else:
            brier = None
        script_details.append({
            "script_id": script.script_id,
            "script_title": script.script_title,
            "direction_type": script.direction_type,
            "probability_central": prob,
            "probability_range": f"{int((script.probability_low or 0)*100)}%–{int((script.probability_high or 0)*100)}%",
            "confidence_level": script.confidence_level,
            "is_hit": is_hit,
            "brier_score": round(brier, 3) if brier is not None else None,
        })

    return {
        "run_id": run_id,
        "event_id": run.event_id,
        "run_summary": run.summary,
        "status": run.status,
        "scripts": script_details,
        "evaluation": _evaluation_to_dict(evaluation) if evaluation else None,
        "outcome": _outcome_to_dict(outcome) if outcome else None,
    }


def update_calibration_from_evaluation(
    db: Session,
    run_id: str,
    evaluation_id: str,
) -> Dict:
    """根据评估更新校准数据，每次create_evaluation后自动调"""
    evaluation = db.query(PredictionEvaluation).filter_by(evaluation_id=evaluation_id).first()
    if not evaluation:
        return {"status": "evaluation_not_found"}

    # 算Brier（有概率的话）
    if evaluation.matched_script_id:
        script = db.query(ScenarioScript).filter_by(
            script_id=evaluation.matched_script_id
        ).first()
        if script and script.probability_central is not None:
            brier = compute_brier_score(
                script.probability_central,
                1 if evaluation.script_hit else 0
            )
            evaluation.calibration_error = round(brier, 4)
            try:
                db.commit()
            except Exception as commit_err:
                db.rollback()
                logger.warning(f"[calibration] Brier score commit 失败: {commit_err}")
            logger.info(f"[calibration] Run {run_id}: Brier={brier:.3f}, hit={evaluation.script_hit}")

    return {
        "status": "updated",
        "run_id": run_id,
        "script_hit": evaluation.script_hit,
        "calibration_error": evaluation.calibration_error,
    }


def get_theory_calibration(db: Session) -> Dict:
    """各理论视角的推演命中率"""
    evaluations = db.query(PredictionEvaluation).all()
    return _compute_theory_accuracy(db, evaluations)


def get_direction_calibration(db: Session) -> Dict:
    """各推演方向（升级/僵持/缓和）的命中率"""
    evaluations = db.query(PredictionEvaluation).filter(
        PredictionEvaluation.matched_script_id.isnot(None)
    ).all()

    by_direction = defaultdict(lambda: {"total": 0, "hits": 0})

    for eval_ in evaluations:
        if not eval_.matched_script_id:
            continue
        script = db.query(ScenarioScript).filter_by(
            script_id=eval_.matched_script_id
        ).first()
        if script:
            direction = script.direction_type
            by_direction[direction]["total"] += 1
            if eval_.script_hit:
                by_direction[direction]["hits"] += 1

    result = {}
    for direction, stats in by_direction.items():
        total = stats["total"]
        hits = stats["hits"]
        result[direction] = {
            "total": total,
            "hits": hits,
            "hit_rate": round(hits / total, 3) if total > 0 else 0.0,
        }

    return result


# --- 内部计算 ---

def _compute_error_distribution(evaluations: List) -> Dict:
    """错误类型分布"""
    error_counts = defaultdict(int)
    for e in evaluations:
        cat = e.main_error_category or "unclassified"
        error_counts[cat] += 1

    total = len(evaluations)
    return {
        cat: {"count": cnt, "rate": round(cnt / total, 3)}
        for cat, cnt in sorted(error_counts.items(), key=lambda x: -x[1])
    }


def _compute_by_event_type_batch(evaluations: List, runs_map: Dict, events_map: Dict) -> Dict:
    """按事件类型分组命中率，批量版"""
    type_stats = defaultdict(lambda: {"total": 0, "hits": 0, "brier_sum": 0.0, "brier_count": 0})
    for eval_ in evaluations:
        run = runs_map.get(eval_.run_id)
        if not run:
            continue
        event = events_map.get(run.event_id)
        if not event:
            continue
        et = event.event_type or "unknown"
        type_stats[et]["total"] += 1
        if eval_.script_hit:
            type_stats[et]["hits"] += 1
        if eval_.calibration_error is not None:
            type_stats[et]["brier_sum"] += eval_.calibration_error
            type_stats[et]["brier_count"] += 1

    result = {}
    for et, s in type_stats.items():
        total = s["total"]
        result[et] = {
            "total": total,
            "hits": s["hits"],
            "hit_rate": round(s["hits"] / total, 3) if total > 0 else 0.0,
            "avg_brier": round(s["brier_sum"] / s["brier_count"], 3) if s["brier_count"] > 0 else None,
        }
    return result


def _compute_by_crisis_stage_batch(evaluations: List, runs_map: Dict, events_map: Dict) -> Dict:
    """按危机阶段分组命中率，批量版"""
    stage_stats = defaultdict(lambda: {"total": 0, "hits": 0})
    for eval_ in evaluations:
        run = runs_map.get(eval_.run_id)
        if not run:
            continue
        event = events_map.get(run.event_id)
        if not event:
            continue
        stage = event.stage_of_crisis or "unknown"
        stage_stats[stage]["total"] += 1
        if eval_.script_hit:
            stage_stats[stage]["hits"] += 1

    result = {}
    for stage, s in stage_stats.items():
        total = s["total"]
        result[stage] = {
            "total": total,
            "hits": s["hits"],
            "hit_rate": round(s["hits"] / total, 3) if total > 0 else 0.0,
            "count": total,
        }
    return result


def _compute_theory_accuracy_batch(db: Session, evaluations: List, runs_map: Dict) -> Dict:
    """各理论视角命中率，批量版

    每个evaluation只归到该run对应事件的理论上
    """
    event_eval_map: Dict[str, Dict] = {}
    for eval_ in evaluations:
        run = runs_map.get(eval_.run_id)
        if run:
            event_eval_map.setdefault(run.event_id, {
                "total": 0,
                "hits": 0,
            })
            event_eval_map[run.event_id]["total"] += 1
            if eval_.script_hit:
                event_eval_map[run.event_id]["hits"] += 1

    theory_stats = {}
    for theory_name, display_name in THEORY_DISPLAY_NAMES.items():
        analyses = db.query(TheoryAnalysis).filter_by(theory_name=theory_name).all()
        theory_events_with_eval = 0
        theory_hits = 0
        theory_total = 0
        for a in analyses:
            ev = event_eval_map.get(a.event_id)
            if ev and ev["total"] > 0:
                theory_events_with_eval += 1
                theory_hits += ev["hits"]
                theory_total += ev["total"]
        if theory_total > 0:
            theory_stats[theory_name] = {
                "display_name": display_name,
                "events_analyzed": len(analyses),
                "events_with_evaluation": theory_events_with_eval,
                "evaluations_linked": theory_total,
                "avg_hit_rate": round(theory_hits / theory_total, 3),
                "count": theory_total,
                "hit_rate": round(theory_hits / theory_total, 3),
            }
    return theory_stats


def _compute_time_trend(evaluations: List) -> List[Dict]:
    """按月命中率趋势"""
    month_stats = defaultdict(lambda: {"total": 0, "hits": 0})

    for e in evaluations:
        if not e.evaluated_at:
            continue
        month_key = e.evaluated_at.strftime("%Y-%m")
        month_stats[month_key]["total"] += 1
        if e.script_hit:
            month_stats[month_key]["hits"] += 1

    trend = []
    for month in sorted(month_stats.keys()):
        stats = month_stats[month]
        total = stats["total"]
        hits = stats["hits"]
        trend.append({
            "month": month,
            "total": total,
            "hits": hits,
            "hit_rate": round(hits / total, 3) if total > 0 else 0.0,
        })
    return trend


def _estimate_overall_brier(db: Session, evaluations: List) -> Optional[float]:
    """估算整体Brier分数"""
    brier_scores = []

    for eval_ in evaluations:
        if eval_.calibration_error is not None:
            brier_scores.append(eval_.calibration_error)
        elif eval_.matched_script_id:
            # 实时算一下
            script = db.query(ScenarioScript).filter_by(
                script_id=eval_.matched_script_id
            ).first()
            if script and script.probability_central is not None:
                brier = compute_brier_score(
                    script.probability_central,
                    1 if eval_.script_hit else 0
                )
                brier_scores.append(brier)

    if not brier_scores:
        return None
    return sum(brier_scores) / len(brier_scores)


def _compute_theory_accuracy(db: Session, evaluations: List) -> Dict:
    """各理论视角命中率，旧版wrapper"""
    run_ids = list({e.run_id for e in evaluations if e.run_id})
    runs_map = {
        r.run_id: r
        for r in db.query(PredictionRun).filter(PredictionRun.run_id.in_(run_ids)).all()
    }
    return _compute_theory_accuracy_batch(db, evaluations, runs_map)


def _compute_calibration_grade(hit_rate: float, node_hit_rate: float) -> Dict:
    """校准等级A-F，combined=命中率*0.6+步骤*0.4"""
    combined = hit_rate * 0.6 + node_hit_rate * 0.4

    if combined >= 0.75:
        grade = "A"
    elif combined >= 0.60:
        grade = "B"
    elif combined >= 0.45:
        grade = "C"
    elif combined >= 0.30:
        grade = "D"
    else:
        grade = "F"

    return {
        "grade": grade,
        "combined_score": round(combined, 3),
    }


def _generate_improvement_suggestions(
    error_dist: Dict,
    by_event_type: Dict,
) -> List[str]:
    """根据错误分布和事件类型命中率生成改进建议"""
    suggestions = []

    # 主要错误类型
    if error_dist:
        top_error = max(error_dist.items(), key=lambda x: x[1].get("count", 0) if isinstance(x[1], dict) else x[1])
        error_type = top_error[0]
        error_suggestions = {
            "evidence_miss": "建议增加多源信息融合，扩展 RSS 源覆盖范围",
            "actor_profile_error": "建议补充行为主体历史行为数据库，完善主体画像",
            "historical_analogy_failure": "建议扩充历史案例库，增加近20年案例",
            "timing_error": "建议在剧本步骤中增加时间窗口估算",
            "template_overfitting": "反模板检查阈值建议从0.65降至0.55",
            "black_swan": "建议增加'黑天鹅'专项剧本，标注低概率高影响场景",
        }
        suggestion = error_suggestions.get(error_type, f"主要错误类型 '{error_type}' 需要专项改进")
        suggestions.append(suggestion)

    # 低命中率事件类型
    if by_event_type:
        low_hit_types = [
            et for et, stats in by_event_type.items()
            if stats.get("total", 0) >= 2 and stats.get("hit_rate", 1.0) < 0.3
        ]
        for et in low_hit_types[:2]:
            suggestions.append(f"事件类型 '{et}' 命中率偏低，建议补充该类型历史案例和专项提示词")

    if not suggestions:
        suggestions.append("当前评估数据不足，建议完成至少5次预测评估后再查看改进建议")

    return suggestions


def _empty_calibration_summary() -> Dict:
    """空摘要，没数据时用"""
    return {
        "total_evaluations": 0,
        "script_hit_rate": None,
        "script_hit_count": 0,
        "avg_node_hit_rate": None,
        "avg_calibration_error": None,
        "avg_brier_score": None,
        "overall_brier_score": None,
        "error_distribution": {},
        "by_event_type": {},
        "by_crisis_stage": {},
        "time_trend": [],
        "theory_accuracy": {},
        "calibration_grade": None,
        "combined_score": None,
        "improvement_suggestions": ["暂无评估数据，请完成预测后记录实际结果并创建评估"],
        "data_note": "需要至少1条 PredictionEvaluation 记录才能生成校准数据",
    }


def _evaluation_to_dict(evaluation) -> Dict:
    if not evaluation:
        return {}
    return {
        "evaluation_id": evaluation.evaluation_id,
        "script_hit": evaluation.script_hit,
        "node_hit_rate": evaluation.node_hit_rate,
        "calibration_error": evaluation.calibration_error,
        "main_error_category": evaluation.main_error_category,
        "detailed_error_analysis": evaluation.detailed_error_analysis,
        "correct_aspects": evaluation.correct_aspects or [],
        "incorrect_aspects": evaluation.incorrect_aspects or [],
        "suggested_adjustments": evaluation.suggested_adjustments or [],
        "evaluated_at": evaluation.evaluated_at.isoformat() if evaluation.evaluated_at else None,
    }


def _outcome_to_dict(outcome) -> Dict:
    if not outcome:
        return {}
    return {
        "outcome_id": outcome.outcome_id,
        "actual_summary": outcome.actual_summary,
        "actual_event_type": outcome.actual_event_type,
        "actual_event_time": outcome.actual_event_time.isoformat() if outcome.actual_event_time else None,
        "recorded_at": outcome.recorded_at.isoformat() if outcome.recorded_at else None,
    }
