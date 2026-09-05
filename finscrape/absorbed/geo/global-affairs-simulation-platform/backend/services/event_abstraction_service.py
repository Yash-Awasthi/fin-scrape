"""
事件抽象，从簇提炼IR事件，含坐标解析
"""
import uuid
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session

from backend.models.news_cluster import NewsCluster
from backend.models.raw_news import RawNews
from backend.models.ir_event import AbstractIRGEvent
from backend.core.llm_router import llm_call_json
from backend.core.prompts import ABSTRACTION_SYSTEM_PROMPT, ABSTRACTION_USER_TEMPLATE
from backend.services.geocoding_service import get_coordinates_for_event

logger = logging.getLogger(__name__)


def abstract_event_from_cluster(db: Session, cluster_id: str) -> Optional[Dict]:
    """从簇提炼事件，自动分组簇跳LLM走回退"""
    cluster = db.query(NewsCluster).filter_by(cluster_id=cluster_id).first()
    if not cluster:
        return None

    # 已有就直接返回
    if cluster.event_id:
        event = db.query(AbstractIRGEvent).filter_by(event_id=cluster.event_id).first()
        if event:
            return _event_to_dict(event)

    # 自动分组簇质量低，不调LLM
    is_fallback_cluster = "自动分组" in (cluster.cluster_title or "")
    if is_fallback_cluster:
        logger.info(f"跳过 LLM（自动分组簇）: {cluster.cluster_title}")
        return _fallback_abstraction(db, cluster)

    # 只取标题控token
    news_summaries = ""
    if cluster.related_news_ids:
        news_list = db.query(RawNews).filter(RawNews.news_id.in_(cluster.related_news_ids)).all()
        news_summaries = "\n".join([
            f"- {n.title}"
            for n in news_list[:10]   # 最多10条
        ])

    # 构建Prompt
    user_msg = ABSTRACTION_USER_TEMPLATE.format(
        cluster_title=cluster.cluster_title,
        key_actors=", ".join((cluster.key_actors or [])[:6]),
        key_locations=", ".join((cluster.key_locations or [])[:4]),
        primary_issue=cluster.primary_issue or "",
        secondary_issues=", ".join((cluster.secondary_issues or [])[:3]),
        escalation_signals=", ".join((cluster.escalation_signals or [])[:3]),
        deescalation_signals=", ".join((cluster.deescalation_signals or [])[:3]),
        evidence_summary=(cluster.evidence_summary or "")[:300],
        news_summaries=news_summaries or "（无详细新闻摘要）",
    )

    logger.info(f"抽象事件簇: {cluster.cluster_title}")
    result = llm_call_json("event_abstraction", ABSTRACTION_SYSTEM_PROMPT, user_msg,
                           timeout_seconds=300)   # 失败走回退不重试

    if result is None or result.get("parse_error"):
        logger.warning("Claude 返回解析失败，使用回退")
        return _fallback_abstraction(db, cluster)

    # actor_interests旧版字段兼容
    actor_roles = result.get("actor_roles", {})
    actor_interests = result.get("actor_interests", {})
    if actor_interests and actor_roles:
        for actor, roles_desc in actor_roles.items():
            interests = actor_interests.get(actor, {})
            if interests.get("red_line"):
                actor_roles[actor] = f"{roles_desc} | 红线: {interests['red_line']}"

    current_balance = result.get("current_balance", "")
    esc_mech = result.get("escalation_mechanism", "")
    if esc_mech:
        current_balance = f"{current_balance}\n[升级机制] {esc_mech}"

    major_risks = result.get("major_risks", [])
    uncertainties = result.get("strategic_uncertainties", [])
    if uncertainties:
        major_risks = major_risks + [f"[不确定性] {u}" for u in uncertainties[:2]]

    # 坐标优先用Claude返回的，不够查服务
    geo_coords = result.get("geo_coordinates", {})
    if not geo_coords or geo_coords.get("lat") is None:
        real_coords = get_coordinates_for_event(
            key_locations=result.get("key_locations", cluster.key_locations or []),
            region=result.get("region", "Global"),
        )
        if real_coords:
            geo_coords = {"lat": real_coords["lat"], "lng": real_coords["lng"]}

    # 保存事件
    event_id = str(uuid.uuid4())
    event = AbstractIRGEvent(
        event_id=event_id,
        source_cluster_ids=[cluster_id],
        event_title=result.get("event_title", cluster.cluster_title),
        event_type=result.get("event_type", "diplomatic_negotiation"),
        stage_of_crisis=result.get("stage_of_crisis", "emergence"),
        key_actors=result.get("key_actors", cluster.key_actors or []),
        actor_roles=actor_roles if actor_roles else result.get("actor_roles", {}),
        key_locations=result.get("key_locations", cluster.key_locations or []),
        strategic_dimensions=result.get("strategic_dimensions", []),
        driving_forces=result.get("driving_forces", []),
        constraints=result.get("constraints", []),
        immediate_triggers=result.get("immediate_triggers", []),
        current_balance=current_balance if current_balance else result.get("current_balance", ""),
        major_risks=major_risks if major_risks else result.get("major_risks", []),
        current_opportunities=result.get("current_opportunities", []),
        event_confidence=result.get("event_confidence", 0.7),
        geo_coordinates=geo_coords,
        region=result.get("region", "Global"),
    )
    db.add(event)

    cluster.event_id = event_id
    db.commit()

    try:
        from backend.services.event_version_service import create_version
        create_version(db, event_id, change_source="abstraction",
                       change_summary="事件首次抽象创建")
    except Exception:
        pass

    logger.info(f"完成: {event.event_title} [{event.event_type}]")
    return _event_to_dict(event)


def _fallback_abstraction(db: Session, cluster: NewsCluster) -> Dict:
    """回退：从簇信息直接建事件"""
    event_id = str(uuid.uuid4())
    event = AbstractIRGEvent(
        event_id=event_id,
        source_cluster_ids=[cluster.cluster_id],
        event_title=cluster.cluster_title,
        event_type="diplomatic_negotiation",
        stage_of_crisis="emergence",
        key_actors=cluster.key_actors or [],
        key_locations=cluster.key_locations or [],
        driving_forces=[cluster.primary_issue] if cluster.primary_issue else [],
        event_confidence=0.4,
    )
    db.add(event)
    cluster.event_id = event_id
    db.commit()

    try:
        from backend.services.event_version_service import create_version
        create_version(db, event_id, change_source="fallback_abstraction",
                       change_summary="回退抽象创建")
    except Exception:
        pass

    return _event_to_dict(event)


def abstract_all_unprocessed_clusters(db: Session) -> list:
    """批量处理未抽象簇，单个失败不阻断，最多15个调LLM"""
    unprocessed = db.query(NewsCluster).filter(NewsCluster.event_id.is_(None)).all()
    # 真实簇优先，自动分组放后面
    real_clusters = [c for c in unprocessed if "自动分组" not in (c.cluster_title or "")]
    fallback_clusters = [c for c in unprocessed if "自动分组" in (c.cluster_title or "")]

    MAX_LLM_CLUSTERS = 15  # 约15×15s=225s
    real_clusters = real_clusters[:MAX_LLM_CLUSTERS]
    to_process = real_clusters + fallback_clusters

    logger.info(f"共 {len(unprocessed)} 个 cluster 待处理"
          f"（真实LLM簇: {len(real_clusters)}, 自动分组簇: {len(fallback_clusters)}）")
    results = []
    for i, cluster in enumerate(to_process):
        try:
            logger.info(f"处理 {i+1}/{len(to_process)}: {cluster.cluster_title}")
            result = abstract_event_from_cluster(db, cluster.cluster_id)
            if result:
                results.append(result)
        except Exception as e:
            # 单个失败走回退继续
            logger.warning(f"cluster {cluster.cluster_id} 抽象失败，使用回退: {e}")
            try:
                fallback = _fallback_abstraction(db, cluster)
                if fallback:
                    results.append(fallback)
            except Exception as fe:
                logger.error(f"cluster {cluster.cluster_id} 回退也失败，跳过: {fe}")
    logger.info(f"完成，成功抽象 {len(results)}/{len(to_process)} 个事件")
    return results


def _event_to_dict(event: AbstractIRGEvent) -> Dict:
    confidence = event.event_confidence or 0.0
    return {
        "event_id": event.event_id,
        "event_title": event.event_title,
        "event_type": event.event_type,
        "stage_of_crisis": event.stage_of_crisis,
        "key_actors": event.key_actors,
        "actor_roles": event.actor_roles,
        "key_locations": event.key_locations,
        "strategic_dimensions": event.strategic_dimensions,
        "driving_forces": event.driving_forces,
        "constraints": event.constraints,
        "immediate_triggers": event.immediate_triggers,
        "current_balance": event.current_balance,
        "major_risks": event.major_risks,
        "current_opportunities": event.current_opportunities,
        "event_confidence": confidence,
        # is_fallback=回退生成质量低
        "is_fallback": confidence < 0.5,
        "geo_coordinates": event.geo_coordinates,
        "region": event.region,
        "source_cluster_ids": event.source_cluster_ids,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }
