"""持久化 - PredictionRun的创建/保存/查询"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models.prediction import PredictionRun
from backend.models.outcome import ActualOutcome, PredictionEvaluation
from backend.core.config import settings


def create_prediction_run(db: Session, event_id: str, root_question: str = "") -> PredictionRun:
    """创建新推演记录"""
    run = PredictionRun(
        run_id=str(uuid.uuid4()),
        event_id=event_id,
        root_question=root_question or "该事件接下来会如何发展？",
        model_version=settings.CLAUDE_MODEL,
        rules_version="1.0",
        status="running",
    )
    db.add(run)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"create_prediction_run commit 失败: {e}") from e
    return run


def complete_run(db: Session, run_id: str, summary: str, script_ids: List[str]) -> bool:
    """标记推演完成"""
    run = db.query(PredictionRun).filter_by(run_id=run_id).first()
    if not run:
        return False
    run.status = "complete"
    run.summary = summary
    run.script_ids = script_ids
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"complete_run commit 失败: {e}") from e
    return True


def get_run(db: Session, run_id: str) -> Optional[Dict]:
    """获取推演记录"""
    run = db.query(PredictionRun).filter_by(run_id=run_id).first()
    if not run:
        return None
    return _run_to_dict(run)


def list_runs(db: Session, event_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict]:
    """列出推演记录"""
    query = db.query(PredictionRun)
    if event_id:
        query = query.filter_by(event_id=event_id)
    runs = query.order_by(PredictionRun.created_at.desc()).offset(offset).limit(limit).all()
    return [_run_to_dict(r) for r in runs]


def record_actual_outcome(
    db: Session,
    run_id: str,
    event_id: str,
    actual_summary: str,
    actual_event_type: str,
    matched_script_id: Optional[str] = None,
    evidence_ids: Optional[List[str]] = None,
) -> Dict:
    """记录实际结果，用于复盘"""
    outcome = ActualOutcome(
        outcome_id=str(uuid.uuid4()),
        related_run_id=run_id,
        event_id=event_id,
        actual_summary=actual_summary,
        actual_event_time=datetime.now(timezone.utc),
        actual_event_type=actual_event_type,
        matched_script_id=matched_script_id,
        evidence_ids=evidence_ids or [],
    )
    db.add(outcome)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"record_actual_outcome commit 失败: {e}") from e
    return _outcome_to_dict(outcome)


def create_evaluation(
    db: Session,
    run_id: str,
    outcome_id: str,
    matched_script_id: Optional[str],
    script_hit: bool,
    node_hit_rate: Optional[float],
    main_error_category: Optional[str],
    detailed_error_analysis: str,
    correct_aspects: List[str],
    incorrect_aspects: List[str],
    suggested_adjustments: List[str],
) -> Dict:
    """创建预测评估（误差分析）"""
    evaluation = PredictionEvaluation(
        evaluation_id=str(uuid.uuid4()),
        run_id=run_id,
        outcome_id=outcome_id,
        matched_script_id=matched_script_id,
        script_hit=script_hit,
        node_hit_rate=node_hit_rate,
        main_error_category=main_error_category,
        detailed_error_analysis=detailed_error_analysis,
        correct_aspects=correct_aspects,
        incorrect_aspects=incorrect_aspects,
        suggested_adjustments=suggested_adjustments,
    )
    db.add(evaluation)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"create_evaluation commit 失败: {e}") from e
    return _eval_to_dict(evaluation)


def _run_to_dict(run: PredictionRun) -> Dict:
    return {
        "run_id": run.run_id,
        "event_id": run.event_id,
        "root_question": run.root_question,
        "model_version": run.model_version,
        "rules_version": run.rules_version,
        "summary": run.summary,
        "status": run.status,
        "script_ids": run.script_ids,
        "is_branch": run.is_branch,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


def _outcome_to_dict(outcome: ActualOutcome) -> Dict:
    return {
        "outcome_id": outcome.outcome_id,
        "related_run_id": outcome.related_run_id,
        "actual_summary": outcome.actual_summary,
        "actual_event_type": outcome.actual_event_type,
        "matched_script_id": outcome.matched_script_id,
        "recorded_at": outcome.recorded_at.isoformat() if outcome.recorded_at else None,
    }


def _eval_to_dict(evaluation: PredictionEvaluation) -> Dict:
    return {
        "evaluation_id": evaluation.evaluation_id,
        "run_id": evaluation.run_id,
        "script_hit": evaluation.script_hit,
        "node_hit_rate": evaluation.node_hit_rate,
        "main_error_category": evaluation.main_error_category,
        "detailed_error_analysis": evaluation.detailed_error_analysis,
        "correct_aspects": evaluation.correct_aspects,
        "incorrect_aspects": evaluation.incorrect_aspects,
        "suggested_adjustments": evaluation.suggested_adjustments,
        "evaluated_at": evaluation.evaluated_at.isoformat() if evaluation.evaluated_at else None,
    }
