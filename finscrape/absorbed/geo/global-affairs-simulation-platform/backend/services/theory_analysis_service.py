"""多理论视角分析 - 为每个事件生成5种理论的并行分析"""
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.models.ir_event import AbstractIRGEvent
from backend.models.theory_analysis import TheoryAnalysis, THEORY_NAMES, THEORY_DISPLAY_NAMES
from backend.core.llm_router import llm_call_json
from backend.core.prompts import THEORY_SYSTEM_PROMPT, THEORY_USER_TEMPLATE, THEORY_DESCRIPTIONS
from backend.db.database import SessionLocal

logger = logging.getLogger(__name__)


def generate_theory_analyses(db: Session, event_id: str) -> List[Dict]:
    """为事件生成全部5种理论视角分析，并行最多2个LLM调用"""
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        return []

    # 已有的分析直接用
    existing = db.query(TheoryAnalysis).filter_by(event_id=event_id).all()
    existing_theories = {a.theory_name for a in existing}

    results = [_analysis_to_dict(a) for a in existing]

    pending = [t for t in THEORY_NAMES if t not in existing_theories]
    if not pending:
        return results

    # 提前提取事件字段，避免跨线程访问ORM延迟加载
    event_data = {
        "event_id": event.event_id,
        "event_title": event.event_title,
        "event_type": event.event_type,
        "stage_of_crisis": event.stage_of_crisis or "unknown",
        "key_actors": list(event.key_actors or []),
        "actor_roles": dict(event.actor_roles or {}),
        "driving_forces": list(event.driving_forces or []),
        "constraints": list(event.constraints or []),
        "immediate_triggers": list(event.immediate_triggers or []),
    }

    # 并行执行，每个理论用独立DB session（session不是线程安全的）
    # max_workers=2：SQLite WAL写操作仍串行，3+并行容易busy_timeout
    def run_one(theory_name: str) -> Optional[Dict]:
        thread_db = SessionLocal()
        try:
            logger.info(f"生成 {THEORY_DISPLAY_NAMES[theory_name]} 分析...")
            return _generate_single_theory(thread_db, event_data, theory_name)
        except Exception as e:
            logger.warning(f"{theory_name} 异常: {e}")
            return None
        finally:
            thread_db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(run_one, t): t for t in pending}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    return results


def _generate_single_theory(
    db: Session, event_data: dict, theory_name: str
) -> Optional[Dict]:
    """生成单一理论视角分析，接受event_data字典，线程安全"""
    user_msg = THEORY_USER_TEMPLATE.format(
        event_title=event_data["event_title"],
        event_type=event_data["event_type"],
        stage_of_crisis=event_data["stage_of_crisis"],
        key_actors=", ".join(event_data["key_actors"]),
        actor_roles=str(event_data["actor_roles"]),
        driving_forces=", ".join(event_data["driving_forces"]),
        constraints=", ".join(event_data["constraints"]),
        immediate_triggers=", ".join(event_data["immediate_triggers"]),
        theory_name=THEORY_DISPLAY_NAMES.get(theory_name, theory_name),
        theory_description=THEORY_DESCRIPTIONS.get(theory_name, ""),
    )

    result = llm_call_json("theory_analysis", THEORY_SYSTEM_PROMPT, user_msg,
                           timeout_seconds=300)

    if result is None or result.get("parse_error"):
        logger.warning(f"{theory_name} 解析失败，跳过")
        return None

    analysis = TheoryAnalysis(
        analysis_id=str(uuid.uuid4()),
        event_id=event_data["event_id"],
        theory_name=theory_name,
        core_assumption=result.get("core_assumption", ""),
        interpretation=result.get("interpretation", ""),
        main_drivers=result.get("main_drivers", []),
        likely_actor_responses=result.get("likely_actor_responses", {}),
        escalation_implications=result.get("escalation_implications", []),
        deescalation_implications=result.get("deescalation_implications", []),
        weaknesses=result.get("weaknesses", []),
        counterarguments=result.get("counterarguments", []),
        confidence_note=result.get("confidence_note", ""),
    )
    db.add(analysis)
    # commit失败必须rollback，否则session损坏
    try:
        db.commit()
    except Exception as commit_err:
        db.rollback()
        logger.warning(f"{theory_name} DB commit 失败: {commit_err}")
        return None

    return _analysis_to_dict(analysis)


def get_theory_analyses(db: Session, event_id: str) -> List[Dict]:
    """获取事件的所有理论分析"""
    analyses = db.query(TheoryAnalysis).filter_by(event_id=event_id).all()
    return [_analysis_to_dict(a) for a in analyses]


def _analysis_to_dict(analysis: TheoryAnalysis) -> Dict:
    return {
        "analysis_id": analysis.analysis_id,
        "event_id": analysis.event_id,
        "theory_name": analysis.theory_name,
        "theory_display_name": THEORY_DISPLAY_NAMES.get(analysis.theory_name, analysis.theory_name),
        "core_assumption": analysis.core_assumption,
        "interpretation": analysis.interpretation,
        "main_drivers": analysis.main_drivers,
        "likely_actor_responses": analysis.likely_actor_responses,
        "escalation_implications": analysis.escalation_implications,
        "deescalation_implications": analysis.deescalation_implications,
        "weaknesses": analysis.weaknesses,
        "counterarguments": analysis.counterarguments,
        "confidence_note": analysis.confidence_note,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }
