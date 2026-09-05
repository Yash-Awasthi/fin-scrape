"""
事件版本管理服务 - 快照创建、历史查询、版本回滚
"""
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from backend.models.ir_event import AbstractIRGEvent
from backend.models.event_version import EventVersion, version_to_dict

logger = logging.getLogger("event_version")

SNAPSHOT_FIELDS = [
    "event_title", "event_type", "stage_of_crisis",
    "key_actors", "actor_roles", "key_locations", "strategic_dimensions",
    "driving_forces", "constraints", "immediate_triggers",
    "current_balance", "major_risks", "current_opportunities",
    "event_confidence", "geo_coordinates", "region", "status",
]


def _event_to_snapshot(event: AbstractIRGEvent) -> Dict:
    return {field: getattr(event, field, None) for field in SNAPSHOT_FIELDS}


def create_version(
    db: Session,
    event_id: str,
    change_source: str = "manual",
    change_summary: str = "",
) -> Optional[Dict]:
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        return None

    last_version = (
        db.query(EventVersion)
        .filter_by(event_id=event_id)
        .order_by(EventVersion.version_number.desc())
        .first()
    )
    next_number = (last_version.version_number + 1) if last_version else 1

    snapshot = _event_to_snapshot(event)

    if last_version and last_version.snapshot == snapshot:
        return version_to_dict(last_version)

    version = EventVersion(
        event_id=event_id,
        version_number=next_number,
        snapshot=snapshot,
        change_source=change_source,
        change_summary=change_summary,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    logger.info(f"[event_version] 创建版本 v{next_number} for event {event_id}")
    return version_to_dict(version)


def list_versions(db: Session, event_id: str) -> List[Dict]:
    rows = (
        db.query(EventVersion)
        .filter_by(event_id=event_id)
        .order_by(EventVersion.version_number.asc())
        .all()
    )
    return [version_to_dict(v) for v in rows]


def get_version(db: Session, event_id: str, version_number: int) -> Optional[Dict]:
    row = db.query(EventVersion).filter_by(event_id=event_id, version_number=version_number).first()
    if not row:
        return None
    return version_to_dict(row)


def rollback_to_version(db: Session, event_id: str, version_number: int) -> Optional[Dict]:
    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        return None

    target = (
        db.query(EventVersion)
        .filter_by(event_id=event_id, version_number=version_number)
        .first()
    )
    if not target:
        return None

    create_version(db, event_id, change_source="rollback",
                   change_summary=f"回滚前快照（v{target.version_number - 1 if target.version_number > 1 else 0}）")

    for field, value in target.snapshot.items():
        if hasattr(event, field):
            setattr(event, field, value)

    db.commit()
    db.refresh(event)

    create_version(db, event_id, change_source="rollback",
                   change_summary=f"已回滚至 v{version_number}")

    logger.info(f"[event_version] 事件 {event_id} 回滚至 v{version_number}")
    return version_to_dict(target)


def diff_versions(db: Session, event_id: str, v1: int, v2: int) -> Optional[Dict]:
    row1 = db.query(EventVersion).filter_by(event_id=event_id, version_number=v1).first()
    row2 = db.query(EventVersion).filter_by(event_id=event_id, version_number=v2).first()
    if not row1 or not row2:
        return None

    changes = []
    all_keys = set(list((row1.snapshot or {}).keys()) + list((row2.snapshot or {}).keys()))
    for key in sorted(all_keys):
        val1 = row1.snapshot.get(key)
        val2 = row2.snapshot.get(key)
        if val1 != val2:
            changes.append({
                "field": key,
                "old": val1,
                "new": val2,
            })

    return {
        "event_id": event_id,
        "version_a": v1,
        "version_b": v2,
        "changes": changes,
        "change_count": len(changes),
    }
