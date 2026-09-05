"""主链路API，跑完整分析流程（采集→聚类→抽象→推演），异步执行"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os
import threading

from backend.db.database import get_db, SessionLocal
from backend.services.ingestion_service import get_mock_news
from backend.models.ir_event import AbstractIRGEvent
from backend.models.theory_analysis import TheoryAnalysis, THEORY_NAMES
from backend.services.rss_ingestion_service import fetch_all_sources
from backend.services.source_registry import list_source_info, get_source_by_id
from backend.services.clustering_service import cluster_news
from backend.services.event_abstraction_service import abstract_all_unprocessed_clusters
from backend.services.theory_analysis_service import generate_theory_analyses
from backend.services.scenario_script_engine import run_scenario_engine, get_scripts_for_event
from backend.services.persistence_service import create_prediction_run, complete_run, list_runs, get_run
from backend.services.geocoding_service import get_cache_stats, get_unresolved_locations
from backend.services.task_manager import task_manager, TaskProgress
from backend.core.rate_limiter import limiter

logger = logging.getLogger("pipeline")
router = APIRouter(prefix="/api/v1/pipeline", tags=["主链路"])

ADMIN_KEY = os.getenv("ADMIN_API_KEY", "")
_pipeline_lock = threading.Lock()
_pipeline_running = False
_reset_confirm_tokens: dict[str, float] = {}


def _verify_admin(x_admin_key: str = Header(default="")):
    if not ADMIN_KEY:
        raise HTTPException(503, "Admin API key not configured. Set ADMIN_API_KEY environment variable.")
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(403, "Admin access required")
    return True


def _run_pipeline_task(
    task: TaskProgress,
    use_mock: bool,
    source_ids: Optional[str],
    resume_from: Optional[str] = None,
):
    """后台线程跑主链路，用独立session。resume_from 指定从哪个步骤开始（跳过之前的）"""
    db = SessionLocal()
    try:
        step_index = {k: i for i, k in enumerate(TaskProgress.STEP_KEYS)}
        resume_idx = step_index.get(resume_from, 0) if resume_from else 0

        ingestion_result = None
        news_collected = 0
        failed_sources = []
        data_source = "mock"
        clusters = []
        events = []

        # --- 新闻采集 ---
        if resume_idx <= 0:
            task.set_step("fetch", "running")
            if use_mock:
                mock_news = get_mock_news(db)
                data_source = "mock"
                news_collected = len(mock_news)
                logger.info(f"[pipeline] Mock 模式：注入 {news_collected} 条测试数据")
            else:
                selected_ids = [s.strip() for s in source_ids.split(",")] if source_ids else None
                ingestion_result = fetch_all_sources(db, source_ids=selected_ids)
                data_source = ingestion_result.data_status
                news_collected = ingestion_result.total_saved
                failed_sources = [
                    r["source_name"] for r in ingestion_result.source_results
                    if r["status"] == "error"
                ]
                logger.info(
                    f"[pipeline] Live 采集完成：新增 {news_collected} 条，"
                    f"失败源 {ingestion_result.total_failed_sources} 个"
                )
            task.set_step("fetch", "done")
        else:
            task.set_step("fetch", "done")
            logger.info("[pipeline] 跳过 fetch（断点续跑）")

        # --- 聚类分析 ---
        if resume_idx <= 1:
            task.set_step("cluster", "running")
            clusters = cluster_news(db)
            task.set_step("cluster", "done")
        else:
            task.set_step("cluster", "done")
            logger.info("[pipeline] 跳过 cluster（断点续跑）")

        # --- 事件抽象 ---
        if resume_idx <= 2:
            task.set_step("abstract", "running")
            events = abstract_all_unprocessed_clusters(db)
            task.set_step("abstract", "done")
        else:
            task.set_step("abstract", "done")
            logger.info("[pipeline] 跳过 abstract（断点续跑）")

        # --- 理论分析 ---
        task.set_step("theory", "running")

        theory_total = 0
        scenario_total = 0
        run_ids = []

        MAX_FULL_ANALYSIS = 3
        THEORY_COUNT = len(THEORY_NAMES)

        new_event_ids = {e["event_id"] for e in events if not e.get("is_fallback") and e.get("event_id")}
        candidate_list = [e for e in events if not e.get("is_fallback") and e.get("event_id")]

        if len(candidate_list) < MAX_FULL_ANALYSIS:
            existing_db_events = (
                db.query(AbstractIRGEvent)
                .order_by(AbstractIRGEvent.event_confidence.desc())
                .limit(20)
                .all()
            )
            for ev in existing_db_events:
                if ev.event_id in new_event_ids:
                    continue
                theory_count = db.query(TheoryAnalysis).filter_by(event_id=ev.event_id).count()
                if theory_count < THEORY_COUNT:
                    candidate_list.append({"event_id": ev.event_id, "is_fallback": False})
                if len(candidate_list) >= MAX_FULL_ANALYSIS:
                    break

        real_events = candidate_list[:MAX_FULL_ANALYSIS]
        total_count = len(real_events)
        logger.info(
            f"[pipeline] 本轮新事件 {len(new_event_ids)} 个，"
            f"含补充共 {total_count} 个事件将做完整分析"
        )

        for idx, event_dict in enumerate(real_events, start=1):
            event_id = event_dict.get("event_id")
            if not event_id:
                continue
            try:
                task.set_progress_detail(
                    f"正在处理事件 {idx}/{total_count}：{event_id[:8]}… 理论分析中"
                )
                task.set_sub_progress(idx, total_count, f"理论分析 {idx}/{total_count}")
                theories = generate_theory_analyses(db, event_id)
                theory_total += len(theories)
                logger.info(
                    f"[pipeline] 事件 {event_id} 理论分析完成（{idx}/{total_count}）：{len(theories)} 理论"
                )
            except Exception as e:
                logger.warning(f"[pipeline] 事件 {event_id} 理论分析失败（跳过）: {e}")
                task.set_progress_detail(
                    f"事件 {idx}/{total_count} 理论分析失败（已跳过）：{str(e)[:60]}"
                )

        task.set_step("theory", "done")
        task.clear_sub_progress()

        # --- 推演生成 ---
        task.set_step("scenario", "running")

        for idx, event_dict in enumerate(real_events, start=1):
            event_id = event_dict.get("event_id")
            if not event_id:
                continue
            try:
                task.set_progress_detail(
                    f"正在处理事件 {idx}/{total_count}：{event_id[:8]}… 推演生成中"
                )
                task.set_sub_progress(idx, total_count, f"推演生成 {idx}/{total_count}")
                run = create_prediction_run(db, event_id)
                scripts = run_scenario_engine(db, event_id, run.run_id, skip_heavy_prep=True)
                script_ids = [s["script_id"] for s in scripts]
                summary = (
                    f"{theory_total} 种理论分析，"
                    f"{len(scripts)} 个推演剧本"
                )
                complete_run(db, run.run_id, summary, script_ids)
                run_ids.append(run.run_id)
                scenario_total += len(scripts)
                logger.info(
                    f"[pipeline] 事件 {event_id} 推演完成（{idx}/{total_count}）：{len(scripts)} 剧本"
                )
                task.set_progress_detail(
                    f"事件 {idx}/{total_count} 推演完成：{len(scripts)} 剧本"
                )
            except Exception as e:
                logger.warning(f"[pipeline] 事件 {event_id} 推演失败（跳过）: {e}")
                task.set_progress_detail(
                    f"事件 {idx}/{total_count} 推演失败（已跳过）：{str(e)[:60]}"
                )

        task.set_step("scenario", "done")
        task.clear_sub_progress()
        task.set_progress_detail(None)
        task.set_step("persist", "running")

        result = {
            "status": "ok",
            "data_source": data_source,
            "news_collected": news_collected,
            "clusters_formed": len(clusters),
            "events_abstracted": len(events),
            "news_count": news_collected,
            "cluster_count": len(clusters),
            "event_count": len(events),
            "theory_count": theory_total,
            "scenario_count": scenario_total,
            "run_ids": run_ids,
            "clusters": clusters,
            "events": events,
            "failed_sources": failed_sources,
            "resumed_from": resume_from,
        }
        if ingestion_result:
            result["ingestion_detail"] = ingestion_result.to_dict()
        task.set_step("persist", "done")

        return result

    except Exception as e:
        logger.exception(f"[pipeline] 任务执行失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/run-full")
@limiter.limit("2/minute")
async def run_full_pipeline(
    request: Request,
    use_mock: bool = False,
    source_ids: Optional[str] = None,
    resume_from: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """启动完整流水线。resume_from 可选值：fetch/cluster/abstract/theory/scenario/persist"""
    global _pipeline_running
    with _pipeline_lock:
        if _pipeline_running:
            raise HTTPException(409, "Pipeline already running, please wait")
        _pipeline_running = True

    if resume_from and resume_from not in TaskProgress.STEP_KEYS:
        raise HTTPException(400, f"Invalid resume_from step: {resume_from}. Valid: {TaskProgress.STEP_KEYS}")

    task = task_manager.create_task()

    def _wrapped_task(t, *args, **kwargs):
        global _pipeline_running
        try:
            return _run_pipeline_task(t, *args, **kwargs)
        except Exception:
            raise
        finally:
            with _pipeline_lock:
                _pipeline_running = False

    try:
        task_manager.run_in_thread(task, _wrapped_task, use_mock, source_ids, resume_from)
    except Exception:
        with _pipeline_lock:
            _pipeline_running = False
        raise HTTPException(500, "Failed to start pipeline thread")
    logger.info(f"[pipeline] 任务 {task.task_id} 已启动，use_mock={use_mock}, resume_from={resume_from}")
    return {"task_id": task.task_id, "status": "pending", "resume_from": resume_from}


@router.post("/tasks/{task_id}/resume")
@limiter.limit("2/minute")
async def resume_pipeline_task(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db),
):
    """从失败任务的出错步骤续跑"""
    global _pipeline_running
    old_task = task_manager.get(task_id)
    if not old_task:
        raise HTTPException(404, f"任务 {task_id} 不存在")
    if old_task.status != "error":
        raise HTTPException(400, f"只能续跑失败的任务，当前状态: {old_task.status}")

    failed_step = None
    for step in old_task.steps:
        if step["status"] == "error":
            failed_step = step["key"]
            break
    if not failed_step:
        failed_step = "theory"

    with _pipeline_lock:
        if _pipeline_running:
            raise HTTPException(409, "Pipeline already running, please wait")
        _pipeline_running = True

    task = task_manager.create_task()

    def _wrapped_task(t, *args, **kwargs):
        global _pipeline_running
        try:
            return _run_pipeline_task(t, *args, **kwargs)
        except Exception:
            raise
        finally:
            with _pipeline_lock:
                _pipeline_running = False

    try:
        task_manager.run_in_thread(task, _wrapped_task, True, None, failed_step)
    except Exception:
        with _pipeline_lock:
            _pipeline_running = False
        raise HTTPException(500, "Failed to start pipeline thread")
    logger.info(f"[pipeline] 任务 {task.task_id} 从 {failed_step} 步骤续跑（原任务 {task_id}）")
    return {
        "task_id": task.task_id,
        "status": "pending",
        "resumed_from": failed_step,
        "original_task_id": task_id,
    }


@router.post("/reset", dependencies=[Depends(_verify_admin)])
@limiter.limit("2/hour")
async def reset_pipeline_data(
    request: Request,
    confirm_token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """清空流水线数据，按依赖关系从叶到根删。需要二次确认：先不带confirm_token调用获取token，再带token调用确认删除"""
    import uuid
    import time as _time

    if not confirm_token:
        token = str(uuid.uuid4())
        _reset_confirm_tokens[token] = _time.monotonic()
        return {
            "status": "confirmation_required",
            "message": "此操作将清空所有数据，请使用返回的 confirm_token 再次调用以确认",
            "confirm_token": token,
            "expires_in_seconds": 300,
        }

    now = _time.monotonic()
    valid_token = _reset_confirm_tokens.pop(confirm_token, None)
    if not valid_token or (now - valid_token) > 300:
        raise HTTPException(400, "confirm_token 无效或已过期（5分钟），请重新获取")

    from backend.models.scenario import ScenarioScript, ScenarioStep
    from backend.models.inference_layer import ActorProfile, TriggerRule, ConstraintRule, ScenarioContext
    from backend.models.news_cluster import NewsCluster
    from backend.models.raw_news import RawNews
    from backend.models.prediction import PredictionRun

    counts = {}

    # 推演步骤
    counts["scenario_steps"] = db.query(ScenarioStep).delete()
    # 推演剧本
    counts["scenario_scripts"] = db.query(ScenarioScript).delete()
    # 推演Run
    counts["prediction_runs"] = db.query(PredictionRun).delete()
    # 推断中间层
    counts["actor_profiles"] = db.query(ActorProfile).delete()
    counts["trigger_rules"] = db.query(TriggerRule).delete()
    counts["constraint_rules"] = db.query(ConstraintRule).delete()
    counts["scenario_contexts"] = db.query(ScenarioContext).delete()
    # 理论分析
    counts["theory_analyses"] = db.query(TheoryAnalysis).delete()
    # 抽象事件
    counts["ir_events"] = db.query(AbstractIRGEvent).delete()
    # 聚类，先解绑新闻的cluster_id
    # 重置时状态要还原成raw，用fetched会导致筛选漏掉数据
    db.query(RawNews).update({"cluster_id": None, "status": "raw"})
    counts["news_clusters"] = db.query(NewsCluster).delete()
    # 原始新闻
    counts["raw_news"] = db.query(RawNews).delete()

    db.commit()
    logger.info(f"[pipeline] 数据已重置: {counts}")
    return {"status": "ok", "deleted": counts}


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """轮询任务进度，返回状态/步骤/结果/错误等"""
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务 {task_id} 不存在（后端可能已重启，内存任务已清除，请重新发起运行）",
        )
    return task.to_dict()


@router.post("/run-analysis/{event_id}")
@limiter.limit("5/hour")
async def run_event_analysis(
    request: Request,
    event_id: str,
    db: Session = Depends(get_db),
):
    """单事件完整分析：理论+推演，自动反模板检查"""
    # 创建run
    run = create_prediction_run(db, event_id)

    # 理论分析
    theory_analyses = generate_theory_analyses(db, event_id)

    # 推演+反模板检查
    scripts = run_scenario_engine(db, event_id, run.run_id)

    # 反模板降级数
    flagged_count = sum(1 for s in scripts if s.get("over_template_flagged", False))

    # 完成run
    summary = (
        f"对事件 {event_id} 完成 {len(theory_analyses)} 种理论分析和 {len(scripts)} 个推演剧本"
        f"（反模板检查：{flagged_count} 个降级）"
    )
    script_ids = [s["script_id"] for s in scripts]
    complete_run(db, run.run_id, summary, script_ids)

    return {
        "run_id": run.run_id,
        "event_id": event_id,
        "theory_analyses_count": len(theory_analyses),
        "scripts_count": len(scripts),
        "anti_template_flagged": flagged_count,
        "summary": summary,
        "status": "complete",
    }


@router.get("/runs")
async def get_runs(event_id: Optional[str] = None, db: Session = Depends(get_db)):
    """推演历史"""
    return list_runs(db, event_id=event_id)


@router.get("/runs/{run_id}")
async def get_run_detail(run_id: str, db: Session = Depends(get_db)):
    """单次推演详情"""
    run = get_run(db, run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    scripts = get_scripts_for_event(db, run["event_id"], run_id)
    return {**run, "scripts": scripts}


# --- 新闻源管理 ---

@router.get("/sources")
async def list_sources():
    """注册的新闻源列表"""
    return {
        "total": len(list_source_info()),
        "sources": list_source_info(),
    }


@router.post("/sources/{source_id}/test")
async def test_source(source_id: str, db: Session = Depends(get_db)):
    """测试新闻源连通性"""
    source = get_source_by_id(source_id)
    if not source:
        raise HTTPException(404, f"源 {source_id} 不存在")

    result = fetch_all_sources(db, source_ids=[source_id], max_per_source=3)
    src_results = [r for r in result.source_results if r["source_id"] == source_id]

    if src_results:
        return {
            "source_id": source_id,
            "source_name": source.source_name,
            "status": src_results[0]["status"],
            "fetched": src_results[0]["fetched"],
            "saved": src_results[0]["saved"],
            "error": src_results[0].get("error"),
        }
    return {"source_id": source_id, "status": "not_tested"}


# --- 地理信息 ---

@router.get("/geocoding/stats")
async def get_geocoding_stats():
    """地理坐标解析统计"""
    return get_cache_stats()


@router.get("/geocoding/unresolved")
async def get_unresolved_geo():
    """没解析出坐标的地名"""
    return {
        "unresolved": get_unresolved_locations(),
        "count": len(get_unresolved_locations()),
    }
