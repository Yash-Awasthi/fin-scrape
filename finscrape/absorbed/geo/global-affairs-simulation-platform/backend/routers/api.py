"""实体API路由 - 新闻/事件/剧本/分支/历史/类比/校准等"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Response, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.models.raw_news import RawNews
from backend.models.news_cluster import NewsCluster
from backend.models.ir_event import AbstractIRGEvent
from backend.services.theory_analysis_service import get_theory_analyses, generate_theory_analyses
from backend.services.scenario_script_engine import get_scripts_for_event
from backend.models.scenario import ScenarioScript
from backend.services.branch_engine import create_branch
from backend.services.persistence_service import (
    list_runs, record_actual_outcome, create_evaluation
)
from backend.models.outcome import ActualOutcome, PredictionEvaluation
from backend.models.prediction import PredictionRun
from backend.services.inference_layer_service import build_scenario_context, get_context
from backend.services.pdf_export_service import generate_pdf_report
from backend.services.analogy_engine import (
    find_historical_analogies, get_analogies_for_event,
    get_all_cases, get_case_by_id,
    create_case, update_case, delete_case, seed_cases_from_json,
)
from backend.services.event_version_service import (
    create_version, list_versions, get_version,
    rollback_to_version, diff_versions,
)
from backend.services.calibration_service import (
    compute_calibration_summary, get_run_calibration_detail,
    get_theory_calibration, get_direction_calibration, update_calibration_from_evaluation
)
from backend.services.relationship_service import (
    compute_and_persist_relationships, get_globe_relationships, get_relationships_for_event
)
from backend.models.event_relationship import EventRelationship
from backend.core.rate_limiter import limiter

logger = logging.getLogger("api")
router = APIRouter(prefix="/api/v1", tags=["实体"])


# --- 新闻 ---
@router.get("/news")
async def list_news(
    status: Optional[str] = None,
    region: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """新闻列表"""
    query = db.query(RawNews)
    if status:
        query = query.filter_by(status=status)
    if region:
        query = query.filter(RawNews.region_tags.contains(region))
    total = query.count()
    news = query.order_by(RawNews.fetched_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "news_id": n.news_id,
                "title": n.title,
                "source_name": n.source_name,
                "source_type": n.source_type,
                "published_at": n.published_at.isoformat() if n.published_at else None,
                "region_tags": n.region_tags,
                "raw_entities": n.raw_entities,
                "cluster_id": n.cluster_id,
                "status": n.status,
                "url": n.url,
            }
            for n in news
        ],
    }


# --- 事件簇 ---
@router.get("/clusters")
async def list_clusters(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """事件簇列表"""
    query = db.query(NewsCluster)
    total = query.count()
    clusters = query.order_by(NewsCluster.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_cluster_dict(c) for c in clusters],
    }


@router.get("/clusters/{cluster_id}")
async def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    """单个事件簇，带关联新闻"""
    cluster = db.query(NewsCluster).filter_by(cluster_id=cluster_id).first()
    if not cluster:
        raise HTTPException(404, "Cluster not found")

    news_list = []
    if cluster.related_news_ids:
        news_items = db.query(RawNews).filter(RawNews.news_id.in_(cluster.related_news_ids)).all()
        news_list = [
            {"news_id": n.news_id, "title": n.title, "source_name": n.source_name, "body": n.body}
            for n in news_items
        ]

    return {**_cluster_dict(cluster), "news": news_list}


# --- 抽象事件 ---
@router.get("/events")
async def list_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """抽象事件列表"""
    query = db.query(AbstractIRGEvent)
    total = query.count()
    events = query.order_by(AbstractIRGEvent.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_event_dict(e) for e in events],
    }


@router.get("/events/{event_id}")
async def get_event(event_id: str, db: Session = Depends(get_db)):
    """单个事件详情"""
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    return _event_dict(event)


# --- 事件版本管理 ---
@router.get("/events/{event_id}/versions")
async def get_event_versions(event_id: str, db: Session = Depends(get_db)):
    """事件版本历史列表"""
    versions = list_versions(db, event_id)
    return {"event_id": event_id, "versions": versions, "total": len(versions)}


@router.get("/events/{event_id}/versions/{version_number}")
async def get_event_version(event_id: str, version_number: int, db: Session = Depends(get_db)):
    """获取特定版本快照"""
    v = get_version(db, event_id, version_number)
    if not v:
        raise HTTPException(404, "Version not found")
    return v


@router.post("/events/{event_id}/versions")
async def create_event_version(
    event_id: str,
    change_source: str = "manual",
    change_summary: str = "",
    db: Session = Depends(get_db),
):
    """手动创建版本快照"""
    result = create_version(db, event_id, change_source, change_summary)
    if not result:
        raise HTTPException(404, "Event not found")
    return result


@router.post("/events/{event_id}/versions/rollback")
async def rollback_event_version(
    event_id: str,
    version_number: int,
    db: Session = Depends(get_db),
):
    """回滚事件到指定版本"""
    result = rollback_to_version(db, event_id, version_number)
    if not result:
        raise HTTPException(404, "Event or version not found")
    return result


@router.get("/events/{event_id}/versions/diff")
async def diff_event_versions(
    event_id: str,
    v1: int = Query(..., description="版本号1"),
    v2: int = Query(..., description="版本号2"),
    db: Session = Depends(get_db),
):
    """对比两个版本的差异"""
    result = diff_versions(db, event_id, v1, v2)
    if not result:
        raise HTTPException(404, "Version not found")
    return result


# --- 理论分析 ---
@router.get("/events/{event_id}/theories")
async def get_theories(event_id: str, db: Session = Depends(get_db)):
    """事件的多理论分析，只读不调LLM"""
    analyses = get_theory_analyses(db, event_id)
    return {"event_id": event_id, "analyses": analyses}


@router.post("/events/{event_id}/theories/generate")
@limiter.limit("5/hour")
async def generate_theories(request: Request, event_id: str, db: Session = Depends(get_db)):
    """触发生成理论分析"""
    analyses = generate_theory_analyses(db, event_id)
    return {"event_id": event_id, "analyses": analyses}


# --- 推演剧本 ---
@router.get("/events/{event_id}/scripts")
async def get_scenarios(event_id: str, run_id: Optional[str] = None, db: Session = Depends(get_db)):
    """事件的推演剧本"""
    scripts = get_scripts_for_event(db, event_id, run_id)
    return {
        "event_id": event_id,
        "run_id": run_id,
        "total": len(scripts),
        "scripts": scripts,
    }


# --- 分支推演 ---
class BranchRequest(BaseModel):
    base_run_id: str = Field(..., min_length=1, max_length=100)
    hypothesis_type: str = Field(..., pattern=r"^(actor_decision|external_shock|policy_change|information_revelation)$")
    hypothesis_title: str = Field(..., min_length=1, max_length=200)
    hypothesis_description: str = Field(..., min_length=1, max_length=5000)
    affected_actors: List[str] = Field(..., min_length=1, max_length=20)
    expected_direction: str = Field(..., pattern=r"^(escalation|stalemate|de_escalation)$")


@router.post("/branches")
@limiter.limit("3/hour")
async def create_branch_run(request: Request, req: BranchRequest, db: Session = Depends(get_db)):
    """创建分支推演"""
    try:
        result = create_branch(
            db=db,
            base_run_id=req.base_run_id,
            hypothesis_type=req.hypothesis_type,
            hypothesis_title=req.hypothesis_title,
            hypothesis_description=req.hypothesis_description,
            affected_actors=req.affected_actors,
            expected_direction=req.expected_direction,
        )
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/branches/{base_run_id}")
async def get_branches(base_run_id: str, db: Session = Depends(get_db)):
    """某次推演的所有分支"""
    from backend.models.prediction import BranchRun
    branches = db.query(BranchRun).filter_by(base_run_id=base_run_id).all()
    return {
        "base_run_id": base_run_id,
        "branches": [
            {
                "branch_run_id": b.branch_run_id,
                "hypothesis_title": b.hypothesis_title,
                "hypothesis_type": b.hypothesis_type,
                "expected_direction": b.expected_direction,
                "status": b.status,
                "diff_summary": b.diff_summary,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in branches
        ],
    }


@router.delete("/branches/{branch_run_id}")
async def delete_branch_run(branch_run_id: str, db: Session = Depends(get_db)):
    """删除分支推演"""
    from backend.models.prediction import BranchRun
    branch = db.query(BranchRun).filter_by(branch_run_id=branch_run_id).first()
    if not branch:
        raise HTTPException(404, "分支不存在")
    db.delete(branch)
    db.commit()
    return {"status": "deleted", "branch_run_id": branch_run_id}


@router.patch("/branches/{branch_run_id}/retract")
async def retract_branch_run(branch_run_id: str, db: Session = Depends(get_db)):
    """撤回分支推演（标记为已撤回）"""
    from backend.models.prediction import BranchRun
    branch = db.query(BranchRun).filter_by(branch_run_id=branch_run_id).first()
    if not branch:
        raise HTTPException(404, "分支不存在")
    branch.status = "retracted"
    db.commit()
    return {"status": "retracted", "branch_run_id": branch_run_id}


# --- 历史记录与复盘 ---
@router.get("/history")
async def get_history(
    event_id: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """历史推演记录，带实际结果和评估（批量查询避免N+1）"""
    runs = list_runs(db, event_id=event_id, limit=limit, offset=skip)
    run_ids = [r["run_id"] for r in runs]

    # 批量加载 outcomes 和 evaluations
    if run_ids:
        outcomes = {
            o.related_run_id: o
            for o in db.query(ActualOutcome).filter(ActualOutcome.related_run_id.in_(run_ids)).all()
        }
        evaluations = {
            e.run_id: e
            for e in db.query(PredictionEvaluation).filter(PredictionEvaluation.run_id.in_(run_ids)).all()
        }

        for run in runs:
            rid = run["run_id"]
            outcome = outcomes.get(rid)
            if outcome:
                run["actual_outcome"] = {
                    "outcome_id": outcome.outcome_id,
                    "actual_summary": outcome.actual_summary,
                    "actual_event_type": outcome.actual_event_type,
                    "matched_script_id": outcome.matched_script_id,
                }
            evaluation = evaluations.get(rid)
            if evaluation:
                run["evaluation"] = {
                    "evaluation_id": evaluation.evaluation_id,
                    "script_hit": evaluation.script_hit,
                    "node_hit_rate": evaluation.node_hit_rate,
                    "main_error_category": evaluation.main_error_category,
                    "detailed_error_analysis": evaluation.detailed_error_analysis,
                    "correct_aspects": evaluation.correct_aspects,
                    "incorrect_aspects": evaluation.incorrect_aspects,
                    "suggested_adjustments": evaluation.suggested_adjustments,
                }
    return runs


class OutcomeRequest(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=100)
    actual_summary: str = Field(..., min_length=1, max_length=5000)
    actual_event_type: str = Field(..., min_length=1, max_length=100)
    matched_script_id: Optional[str] = None


@router.post("/runs/{run_id}/outcome")
async def record_outcome(run_id: str, request: OutcomeRequest, db: Session = Depends(get_db)):
    """记录实际结果"""
    return record_actual_outcome(
        db, run_id, request.event_id,
        request.actual_summary, request.actual_event_type,
        request.matched_script_id,
    )


class EvaluationRequest(BaseModel):
    outcome_id: str = Field(..., min_length=1, max_length=100)
    matched_script_id: Optional[str] = None
    script_hit: bool
    node_hit_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    main_error_category: Optional[str] = Field(default=None, max_length=100)
    detailed_error_analysis: str = Field(..., min_length=1, max_length=5000)
    correct_aspects: List[str] = Field(default=[], max_length=20)
    incorrect_aspects: List[str] = Field(default=[], max_length=20)
    suggested_adjustments: List[str] = Field(default=[], max_length=20)


@router.post("/runs/{run_id}/auto-evaluation")
@limiter.limit("5/hour")
async def auto_generate_evaluation(request: Request, run_id: str, db: Session = Depends(get_db)):
    """LLM自动复盘，run必须先有实际结果"""
    from backend.core.llm_router import llm_call_json
    from backend.models.scenario import ScenarioScript

    run = db.query(PredictionRun).filter_by(run_id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="run_id 不存在")

    outcome = db.query(ActualOutcome).filter_by(related_run_id=run_id).first()
    if not outcome:
        raise HTTPException(status_code=400, detail="请先记录实际结果（actual_outcome）再生成评估")

    # 已有评估直接返回
    existing_eval = db.query(PredictionEvaluation).filter_by(run_id=run_id).first()
    if existing_eval:
        return {
            "evaluation_id": existing_eval.evaluation_id,
            "message": "已存在评估，返回现有结果",
            "script_hit": existing_eval.script_hit,
        }

    # 读剧本摘要
    scripts = db.query(ScenarioScript).filter(
        ScenarioScript.script_id.in_(run.script_ids or [])
    ).all() if run.script_ids else []
    scripts_summary = "\n".join([
        f"- [{s.direction_type}] {s.script_title}（概率{s.probability_central or 0:.0%}）: {s.script_description[:150]}"
        for s in scripts
    ]) or "（无剧本数据）"

    llm_system = """你是一位专业的国际关系预测复盘分析师。
你的任务是对比预测剧本与实际结果，生成严格的误差分析报告。
输出纯 JSON，不要任何额外文字。"""

    llm_user = f"""推演摘要：{run.summary or '（无摘要）'}

预测剧本（共{len(scripts)}个）：
{scripts_summary}

实际发生：{outcome.actual_summary}
实际事件类型：{outcome.actual_event_type}
命中剧本ID：{outcome.matched_script_id or '（无命中）'}

请评估预测质量并返回 JSON：
{{
  "script_hit": true,
  "node_hit_rate": 0.6,
  "main_error_category": "evidence_miss/actor_profile_error/historical_analogy_failure/timing_error/template_overfitting/black_swan 中选一",
  "detailed_error_analysis": "2-4句具体说明预测的主要误差来源",
  "correct_aspects": ["预测正确的方面1", "方面2"],
  "incorrect_aspects": ["预测错误的方面1", "方面2"],
  "suggested_adjustments": ["改进建议1", "建议2"]
}}

script_hit: 实际结果是否大体符合某个预测剧本的方向
node_hit_rate: 剧本步骤与实际发展的匹配比例（0~1）
"""

    result = llm_call_json(
        "auto_evaluation",
        llm_system,
        llm_user,
        fallback_value={
            "script_hit": outcome.matched_script_id is not None,
            "node_hit_rate": 0.5,
            "main_error_category": "evidence_miss",
            "detailed_error_analysis": "自动评估生成失败，使用默认值",
            "correct_aspects": [],
            "incorrect_aspects": [],
            "suggested_adjustments": [],
        },
        timeout_seconds=120,
    )

    eval_result = create_evaluation(
        db, run_id, outcome.outcome_id,
        outcome.matched_script_id,
        bool(result.get("script_hit", False)),
        float(result.get("node_hit_rate", 0.5)),
        result.get("main_error_category"),
        result.get("detailed_error_analysis", ""),
        result.get("correct_aspects", []),
        result.get("incorrect_aspects", []),
        result.get("suggested_adjustments", []),
    )

    try:
        update_calibration_from_evaluation(db, run_id, eval_result["evaluation_id"])
    except Exception as e:
        logger.warning("[calibration] auto-evaluation calibration update failed: %s", e)

    return eval_result


@router.post("/runs/{run_id}/evaluation")
async def create_run_evaluation(run_id: str, request: EvaluationRequest, db: Session = Depends(get_db)):
    """创建预测评估"""
    result = create_evaluation(
        db, run_id, request.outcome_id,
        request.matched_script_id, request.script_hit,
        request.node_hit_rate, request.main_error_category,
        request.detailed_error_analysis,
        request.correct_aspects, request.incorrect_aspects,
        request.suggested_adjustments,
    )
    # 评估后更新校准数据
    try:
        update_calibration_from_evaluation(db, run_id, result["evaluation_id"])
    except Exception as e:
        # 校准更新失败不影响主流程
        logger.warning("[calibration] update_calibration_from_evaluation failed: %s", e)
    return result


# --- PDF 导出 ---
@router.get("/reports/export")
async def export_pdf(
    report_type: str = "event_brief",
    event_id: Optional[str] = None,
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """导出PDF报告，type: event_brief/scenario_report/thematic_report/review_report"""
    pdf_bytes = generate_pdf_report(db, report_type, event_id, run_id)
    filename = f"geopolitical_report_{report_type}_{event_id or run_id or 'unknown'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- 地球数据 ---
@router.get("/globe/events")
async def get_globe_data(db: Session = Depends(get_db)):
    """地球渲染数据：事件坐标点+事件间关系"""
    events = db.query(AbstractIRGEvent).all()
    points = []

    event_ids = [e.event_id for e in events]
    all_scripts = db.query(ScenarioScript).filter(
        ScenarioScript.event_id.in_(event_ids)
    ).all() if event_ids else []
    scripts_by_event: dict[str, list] = {}
    for s in all_scripts:
        scripts_by_event.setdefault(s.event_id, []).append(s)

    for event in events:
        coords = event.geo_coordinates or {}
        if coords.get("lat") is None or coords.get("lng") is None:
            continue

        scripts = scripts_by_event.get(event.event_id, [])
        prob: dict[str, list[float]] = {}
        for s in scripts:
            if s.direction_type and s.probability_central is not None:
                prob.setdefault(s.direction_type, []).append(s.probability_central)

        scenario_summary = {
            "has_scenarios": len(scripts) > 0,
            "script_count": len(scripts),
            "escalation": round(sum(prob.get("escalation", [])) / max(len(prob.get("escalation", [])), 1), 3) if prob.get("escalation") else None,
            "stalemate": round(sum(prob.get("stalemate", [])) / max(len(prob.get("stalemate", [])), 1), 3) if prob.get("stalemate") else None,
            "de_escalation": round(sum(prob.get("de_escalation", [])) / max(len(prob.get("de_escalation", [])), 1), 3) if prob.get("de_escalation") else None,
        }

        points.append({
            "event_id": event.event_id,
            "event_title": event.event_title,
            "event_type": event.event_type,
            "stage_of_crisis": event.stage_of_crisis,
            "lat": coords["lat"],
            "lng": coords["lng"],
            "region": event.region,
            "key_actors": event.key_actors or [],
            "actor_roles": event.actor_roles or {},
            "event_confidence": event.event_confidence,
            "scenario_summary": scenario_summary,
        })

    event_ids_with_coords = {p["event_id"] for p in points}

    if not event_ids_with_coords:
        return {
            "total": 0,
            "total_events": len(events),
            "no_coords_count": len(events),
            "points": [],
            "relationships": [],
        }

    relationships = get_globe_relationships(db, event_ids_with_coords)

    if not relationships:
        existing_count = db.query(EventRelationship).count()
        if existing_count == 0:
            logger.info("关系表为空，自动计算...")
            compute_and_persist_relationships(db)
            relationships = get_globe_relationships(db, event_ids_with_coords)

    return {
        "total": len(points),
        "total_events": len(events),
        "no_coords_count": len(events) - len(points),
        "points": points,
        "relationships": relationships,
    }


@router.get("/globe/relationships/{event_id}")
async def get_event_relationships(event_id: str, db: Session = Depends(get_db)):
    """单事件的所有关系，给详情面板高亮弧线用"""
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    rels = get_relationships_for_event(db, event_id)
    return {
        "event_id": event_id,
        "total": len(rels),
        "relationships": rels,
    }


@router.post("/globe/relationships/recompute")
async def recompute_relationships(db: Session = Depends(get_db)):
    """重新计算所有事件间关系"""
    result = compute_and_persist_relationships(db)
    return {
        "status": "success",
        **result,
    }


# --- 推断中间层 ---
@router.get("/events/{event_id}/inference-context")
async def get_inference_context_api(event_id: str, run_id: Optional[str] = None, db: Session = Depends(get_db)):
    """推断中间层上下文"""
    context = get_context(db, event_id, run_id)
    if not context:
        return {
            "event_id": event_id,
            "status": "not_built",
            "message": "尚未构建推断中间层，运行分析后自动生成"
        }
    return {**context, "status": "ready"}


@router.post("/events/{event_id}/build-inference-context")
@limiter.limit("5/hour")
async def build_inference_context_api(
    request: Request,
    event_id: str,
    run_id: str = "manual",
    db: Session = Depends(get_db),
):
    """构建推断中间层"""
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    context = build_scenario_context(db, event_id, run_id)
    if not context:
        raise HTTPException(500, "Failed to build inference context")
    return get_context(db, event_id, run_id)


# --- 历史类比推理 ---

@router.get("/events/{event_id}/analogies")
async def get_event_analogies(event_id: str, db: Session = Depends(get_db)):
    """事件的历史类比，有缓存直接返回"""
    analogies = get_analogies_for_event(db, event_id)
    if not analogies:
        return {
            "event_id": event_id,
            "status": "not_generated",
            "message": "历史类比尚未生成，请调用 POST /build-analogies 触发生成"
        }
    return {**analogies, "status": "ready"}


@router.post("/events/{event_id}/build-analogies")
@limiter.limit("5/hour")
async def build_event_analogies(
    request: Request,
    event_id: str,
    force_regenerate: bool = False,
    db: Session = Depends(get_db),
):
    """触发历史类比推理，force_regenerate=true忽略缓存"""
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")

    result = find_historical_analogies(db, event_id, force_regenerate=force_regenerate)
    if not result:
        raise HTTPException(500, "历史类比生成失败")

    return {**result, "status": "ready", "event_id": event_id}


@router.get("/analogies/cases")
async def list_historical_cases(
    event_type: Optional[str] = None,
    region: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """历史案例库，可按类型/地区/年代筛选"""
    cases = get_all_cases(db)

    if event_type:
        cases = [c for c in cases if c.get("event_type") == event_type]
    if region:
        cases = [c for c in cases if c.get("region") == region]
    if year_from:
        cases = [c for c in cases if c.get("year", 0) >= year_from]
    if year_to:
        cases = [c for c in cases if c.get("year", 9999) <= year_to]

    return {
        "total": len(cases),
        "cases": cases,
    }


@router.get("/analogies/cases/{case_id}")
async def get_historical_case(case_id: str, db: Session = Depends(get_db)):
    """单个历史案例详情"""
    case = get_case_by_id(case_id, db=db)
    if not case:
        raise HTTPException(404, f"Case {case_id} not found")
    return case


class HistoricalCaseCreate(BaseModel):
    case_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=256)
    title_en: Optional[str] = ""
    year: Optional[int] = None
    duration_days: Optional[int] = None
    event_type: Optional[str] = ""
    region: Optional[str] = ""
    crisis_stage_peak: Optional[str] = ""
    key_actors: Optional[List[str]] = []
    actor_roles: Optional[dict] = {}
    primary_issue: Optional[str] = ""
    strategic_dimensions: Optional[List[str]] = []
    key_triggers: Optional[List[str]] = []
    key_constraints: Optional[List[str]] = []
    escalation_path: Optional[List[str]] = []
    resolution: Optional[str] = ""
    resolution_type: Optional[str] = ""
    outcome_summary: Optional[str] = ""
    key_lessons: Optional[List[str]] = []
    analogous_features: Optional[List[str]] = []
    probability_realized: Optional[dict] = {}
    actual_outcome_direction: Optional[str] = ""
    prediction_accuracy_notes: Optional[str] = ""
    tags: Optional[List[str]] = []


class HistoricalCaseUpdate(BaseModel):
    title: Optional[str] = None
    title_en: Optional[str] = None
    year: Optional[int] = None
    duration_days: Optional[int] = None
    event_type: Optional[str] = None
    region: Optional[str] = None
    crisis_stage_peak: Optional[str] = None
    key_actors: Optional[List[str]] = None
    actor_roles: Optional[dict] = None
    primary_issue: Optional[str] = None
    strategic_dimensions: Optional[List[str]] = None
    key_triggers: Optional[List[str]] = None
    key_constraints: Optional[List[str]] = None
    escalation_path: Optional[List[str]] = None
    resolution: Optional[str] = None
    resolution_type: Optional[str] = None
    outcome_summary: Optional[str] = None
    key_lessons: Optional[List[str]] = None
    analogous_features: Optional[List[str]] = None
    probability_realized: Optional[dict] = None
    actual_outcome_direction: Optional[str] = None
    prediction_accuracy_notes: Optional[str] = None
    tags: Optional[List[str]] = None


@router.post("/analogies/cases", status_code=201)
async def create_historical_case(body: HistoricalCaseCreate, db: Session = Depends(get_db)):
    """创建历史案例"""
    try:
        return create_case(db, body.model_dump())
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.put("/analogies/cases/{case_id}")
async def update_historical_case(case_id: str, body: HistoricalCaseUpdate, db: Session = Depends(get_db)):
    """更新历史案例"""
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(400, "没有提供更新字段")
    result = update_case(db, case_id, data)
    if not result:
        raise HTTPException(404, f"Case {case_id} not found")
    return result


@router.delete("/analogies/cases/{case_id}")
async def delete_historical_case(case_id: str, db: Session = Depends(get_db)):
    """删除历史案例"""
    ok = delete_case(db, case_id)
    if not ok:
        raise HTTPException(404, f"Case {case_id} not found")
    return {"status": "deleted", "case_id": case_id}


@router.post("/analogies/cases/seed")
async def seed_historical_cases(db: Session = Depends(get_db)):
    """从JSON种子文件导入案例（仅在案例库为空时生效）"""
    count = seed_cases_from_json(db)
    return {"seeded": count, "message": f"从JSON种子导入 {count} 条案例"}


# --- 预测校准 ---

@router.get("/calibration/summary")
async def get_calibration_summary(db: Session = Depends(get_db)):
    """全局校准摘要：命中率/Brier分数/错误分布/分组统计"""
    return compute_calibration_summary(db)


@router.get("/calibration/runs/{run_id}")
async def get_run_calibration(run_id: str, db: Session = Depends(get_db)):
    """单次推演校准详情，剧本概率vs实际结果"""
    detail = get_run_calibration_detail(db, run_id)
    if not detail:
        raise HTTPException(404, "Run not found")
    return detail


@router.get("/calibration/theories")
async def get_theory_calibration_api(db: Session = Depends(get_db)):
    """各理论视角的命中率"""
    return get_theory_calibration(db)


@router.get("/calibration/directions")
async def get_direction_calibration_api(db: Session = Depends(get_db)):
    """各推演方向的命中率"""
    return get_direction_calibration(db)


# --- 外部验证对接 ---
@router.get("/metaculus/search")
async def search_metaculus(
    event_type: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=20),
):
    """搜索 Metaculus 公开预测市场"""
    from backend.services.metaculus_service import search_predictions
    results = await search_predictions(event_type=event_type, query=query, limit=limit)
    return {"total": len(results), "predictions": results}


@router.get("/metaculus/{question_id}")
async def get_metaculus_prediction(question_id: int):
    """获取 Metaculus 单个预测详情"""
    from backend.services.metaculus_service import get_prediction
    result = await get_prediction(question_id)
    if not result:
        raise HTTPException(404, "Metaculus prediction not found")
    return result


# --- 工具函数 ---
def _cluster_dict(c: NewsCluster) -> dict:
    return {
        "cluster_id": c.cluster_id,
        "cluster_title": c.cluster_title,
        "news_count": len(c.related_news_ids or []),
        "related_news_ids": c.related_news_ids,
        "time_window_start": c.time_window_start.isoformat() if c.time_window_start else None,
        "time_window_end": c.time_window_end.isoformat() if c.time_window_end else None,
        "key_actors": c.key_actors,
        "key_locations": c.key_locations,
        "primary_issue": c.primary_issue,
        "secondary_issues": c.secondary_issues,
        "escalation_signals": c.escalation_signals,
        "deescalation_signals": c.deescalation_signals,
        "evidence_summary": c.evidence_summary,
        "cluster_confidence": c.cluster_confidence,
        "event_id": c.event_id,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _event_dict(e: AbstractIRGEvent) -> dict:
    confidence = e.event_confidence or 0.0
    return {
        "event_id": e.event_id,
        "event_title": e.event_title,
        "event_type": e.event_type,
        "stage_of_crisis": e.stage_of_crisis,
        "key_actors": e.key_actors,
        "actor_roles": e.actor_roles,
        "key_locations": e.key_locations,
        "strategic_dimensions": e.strategic_dimensions,
        "driving_forces": e.driving_forces,
        "constraints": e.constraints,
        "immediate_triggers": e.immediate_triggers,
        "current_balance": e.current_balance,
        "major_risks": e.major_risks,
        "current_opportunities": e.current_opportunities,
        "event_confidence": confidence,
        "is_fallback": confidence < 0.5,  # Claude挂了就靠规则引擎
        "geo_coordinates": e.geo_coordinates,
        "region": e.region,
        "source_cluster_ids": e.source_cluster_ids,
        "status": e.status,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }
