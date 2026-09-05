"""事件关系计算 - 多种关系类型，缓存+增量更新"""
import logging
from sqlalchemy.orm import Session

from backend.models.ir_event import AbstractIRGEvent
from backend.models.event_relationship import EventRelationship, RelationshipType

logger = logging.getLogger("relationship_service")

CAUSAL_TIME_WINDOW_DAYS = 30
SEMANTIC_SIMILARITY_THRESHOLD = 0.3


def compute_and_persist_relationships(db: Session) -> dict:
    """全量计算并持久化事件关系，先清旧再算"""
    events = db.query(AbstractIRGEvent).order_by(AbstractIRGEvent.created_at).all()
    
    db.query(EventRelationship).delete()
    db.flush()
    
    new_relationships = []
    stats = {rel_type.value: 0 for rel_type in RelationshipType}
    
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            a, b = events[i], events[j]
            rels = _compute_pair_relationships(a, b)
            for rel_data in rels:
                rel = EventRelationship(
                    from_event_id=a.event_id,
                    to_event_id=b.event_id,
                    relationship_type=rel_data["type"],
                    weight=rel_data["weight"],
                    rel_metadata=rel_data.get("metadata", {}),
                )
                db.add(rel)
                new_relationships.append(rel)
                stats[rel_data["type"]] += 1
    
    db.commit()
    
    logger.info(
        f"[relationship] 计算完成: {len(events)} 个事件, "
        f"{len(new_relationships)} 条关系, {stats}"
    )
    
    return {
        "event_count": len(events),
        "relationship_count": len(new_relationships),
        "stats": stats,
    }


def get_globe_relationships(db: Session, event_ids_with_coords: set[str]) -> list[dict]:
    """地球可视化用的关系数据，只返回两端都有坐标的"""
    rels = db.query(EventRelationship).filter(
        EventRelationship.from_event_id.in_(event_ids_with_coords),
        EventRelationship.to_event_id.in_(event_ids_with_coords),
    ).all()
    
    return [_rel_to_dict(rel) for rel in rels]


def get_relationships_for_event(db: Session, event_id: str) -> list[dict]:
    """单个事件的所有关系"""
    rels = db.query(EventRelationship).filter(
        (EventRelationship.from_event_id == event_id) |
        (EventRelationship.to_event_id == event_id)
    ).all()
    
    result = []
    for rel in rels:
        d = _rel_to_dict(rel)
        d["direction"] = "outgoing" if rel.from_event_id == event_id else "incoming"
        d["other_event_id"] = rel.to_event_id if rel.from_event_id == event_id else rel.from_event_id
        result.append(d)
    
    return result


def _compute_pair_relationships(
    a: AbstractIRGEvent, b: AbstractIRGEvent
) -> list[dict]:
    """两个事件之间所有可能的关系"""
    rels = []
    
    _add_shared_actor_rel(a, b, rels)
    _add_same_region_rel(a, b, rels)
    _add_causal_chain_rel(a, b, rels)
    _add_escalation_cascade_rel(a, b, rels)
    _add_semantic_similar_rel(a, b, rels)
    _add_actor_conflict_rel(a, b, rels)
    
    return rels


def _add_shared_actor_rel(a: AbstractIRGEvent, b: AbstractIRGEvent, rels: list[dict]):
    """共同行为体"""
    actors_a = set(a.key_actors or [])
    actors_b = set(b.key_actors or [])
    shared = actors_a & actors_b
    
    if shared:
        rels.append({
            "type": RelationshipType.shared_actor.value,
            "weight": len(shared),
            "metadata": {"actors": list(shared)},
        })


def _add_same_region_rel(a: AbstractIRGEvent, b: AbstractIRGEvent, rels: list[dict]):
    """同地区"""
    if a.region and b.region and a.region == b.region:
        rels.append({
            "type": RelationshipType.same_region.value,
            "weight": 1.0,
            "metadata": {"region": a.region},
        })


def _add_causal_chain_rel(a: AbstractIRGEvent, b: AbstractIRGEvent, rels: list[dict]):
    """因果链：时间先后+共享行为体+维度重叠+30天内"""
    actors_a = set(a.key_actors or [])
    actors_b = set(b.key_actors or [])
    shared_actors = actors_a & actors_b
    
    if not shared_actors:
        return
    
    dims_a = set(a.strategic_dimensions or [])
    dims_b = set(b.strategic_dimensions or [])
    shared_dims = dims_a & dims_b
    
    if not shared_dims:
        return
    
    time_a = a.created_at
    time_b = b.created_at
    
    if not time_a or not time_b:
        return
    
    time_diff = abs((time_b - time_a).total_seconds()) / 86400
    
    if time_diff > CAUSAL_TIME_WINDOW_DAYS:
        return
    
    time_order = "a_before_b" if time_a < time_b else "b_before_a"
    earlier_event = a if time_a < time_b else b
    later_event = b if time_a < time_b else a
    
    weight = min(
        len(shared_actors) * 0.3 + len(shared_dims) * 0.2 + (1.0 - time_diff / CAUSAL_TIME_WINDOW_DAYS) * 0.5,
        1.0,
    )
    
    rels.append({
        "type": RelationshipType.causal_chain.value,
        "weight": round(weight, 2),
        "metadata": {
            "shared_actors": list(shared_actors),
            "shared_dimensions": list(shared_dims),
            "time_gap_days": round(time_diff, 1),
            "time_order": time_order,
            "earlier_event_id": earlier_event.event_id,
            "later_event_id": later_event.event_id,
        },
    })


def _add_escalation_cascade_rel(a: AbstractIRGEvent, b: AbstractIRGEvent, rels: list[dict]):
    """升级级联：共享行为体+事件类型升级趋势+时间先后"""
    ESCALATION_ORDER = {
        "diplomatic_negotiation": 1,
        "economic_coercion": 2,
        "energy_shipping_risk": 3,
        "information_psychological_operations": 3,
        "domestic_political_spillover": 4,
        "alliance_realignment": 4,
        "military_escalation": 5,
    }
    
    actors_a = set(a.key_actors or [])
    actors_b = set(b.key_actors or [])
    shared_actors = actors_a & actors_b
    
    if not shared_actors:
        return
    
    level_a = ESCALATION_ORDER.get(a.event_type, 0)
    level_b = ESCALATION_ORDER.get(b.event_type, 0)
    
    if level_a == 0 or level_b == 0:
        return
    
    if abs(level_b - level_a) < 2:
        return
    
    time_a = a.created_at
    time_b = b.created_at
    
    if not time_a or not time_b:
        return
    
    if time_a < time_b and level_b > level_a:
        escalation_path = [a.event_type, b.event_type]
        weight = (level_b - level_a) / len(ESCALATION_ORDER)
        
        rels.append({
            "type": RelationshipType.escalation_cascade.value,
            "weight": round(weight, 2),
            "metadata": {
                "shared_actors": list(shared_actors),
                "escalation_path": escalation_path,
                "from_level": level_a,
                "to_level": level_b,
            },
        })
    elif time_b < time_a and level_a > level_b:
        escalation_path = [b.event_type, a.event_type]
        weight = (level_a - level_b) / len(ESCALATION_ORDER)
        
        rels.append({
            "type": RelationshipType.escalation_cascade.value,
            "weight": round(weight, 2),
            "metadata": {
                "shared_actors": list(shared_actors),
                "escalation_path": escalation_path,
                "from_level": level_b,
                "to_level": level_a,
            },
        })


def _add_semantic_similar_rel(a: AbstractIRGEvent, b: AbstractIRGEvent, rels: list[dict]):
    """语义相似：标题关键词+维度重叠，Jaccard"""
    def _tokenize(s: str) -> set[str]:
        return set(s.lower().split())
    
    title_tokens_a = _tokenize(a.event_title or "")
    title_tokens_b = _tokenize(b.event_title or "")
    
    if not title_tokens_a or not title_tokens_b:
        return
    
    title_intersection = title_tokens_a & title_tokens_b
    title_union = title_tokens_a | title_tokens_b
    title_similarity = len(title_intersection) / len(title_union) if title_union else 0
    
    dims_a = set(a.strategic_dimensions or [])
    dims_b = set(b.strategic_dimensions or [])
    shared_dims = dims_a & dims_b
    dim_similarity = len(shared_dims) / max(len(dims_a | dims_b), 1)
    
    combined_similarity = title_similarity * 0.6 + dim_similarity * 0.4
    
    if combined_similarity < SEMANTIC_SIMILARITY_THRESHOLD:
        return
    
    rels.append({
        "type": RelationshipType.semantic_similar.value,
        "weight": round(combined_similarity, 2),
        "metadata": {
            "title_similarity": round(title_similarity, 2),
            "dimension_similarity": round(dim_similarity, 2),
            "shared_issues": list(shared_dims),
        },
    })


def _add_actor_conflict_rel(a: AbstractIRGEvent, b: AbstractIRGEvent, rels: list[dict]):
    """行为体冲突：角色对立（主导vs对抗）出现在不同事件"""
    roles_a = a.actor_roles or {}
    roles_b = b.actor_roles or {}
    
    conflict_pairs = []
    
    for actor_a, role_a in roles_a.items():
        for actor_b, role_b in roles_b.items():
            if actor_a == actor_b:
                continue
            
            is_opposing = (
                ("对抗" in str(role_a) or "反对" in str(role_a) or "制裁" in str(role_a)) and
                ("主导" in str(role_b) or "支持" in str(role_b) or "防御" in str(role_b))
            ) or (
                ("对抗" in str(role_b) or "反对" in str(role_b) or "制裁" in str(role_b)) and
                ("主导" in str(role_a) or "支持" in str(role_a) or "防御" in str(role_a))
            )
            
            if is_opposing:
                conflict_pairs.append((actor_a, actor_b))
    
    if conflict_pairs:
        rels.append({
            "type": RelationshipType.actor_conflict.value,
            "weight": min(len(conflict_pairs) * 0.3, 1.0),
            "metadata": {
                "conflicting_actors": [
                    f"{p[0]} vs {p[1]}" for p in conflict_pairs[:3]
                ],
            },
        })


def _rel_to_dict(rel: EventRelationship) -> dict:
    """EventRelationship转字典"""
    metadata = rel.rel_metadata or {}
    
    return {
        "from": rel.from_event_id,
        "to": rel.to_event_id,
        "type": rel.relationship_type,
        "actors": metadata.get("actors", metadata.get("shared_actors", [])),
        "weight": rel.weight or 1.0,
        "metadata": metadata,
    }
