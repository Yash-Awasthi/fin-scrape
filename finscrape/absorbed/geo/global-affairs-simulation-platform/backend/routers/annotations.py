"""批注路由，支持对事件/剧本/理论/类比的跨模块批注"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.models.annotation import Annotation

router = APIRouter(prefix="/api/v1/annotations", tags=["批注与讨论"])

VALID_ENTITY_TYPES = {"event", "script", "theory", "analogy", "run"}
HISTORY_LIMIT = 5   # 最多留5条历史快照


# --- Pydantic模式 ---

class AnnotationCreate(BaseModel):
    entity_type: str
    entity_id: str
    content: str = Field(..., min_length=1, max_length=5000)
    tags: List[str] = []
    importance: str = "medium"


class AnnotationUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    tags: Optional[List[str]] = None
    importance: Optional[str] = None


def _to_dict(ann: Annotation) -> dict:
    return {
        "annotation_id": ann.annotation_id,
        "entity_type": ann.entity_type,
        "entity_id": ann.entity_id,
        "content": ann.content,
        "tags": ann.tags or [],
        "importance": ann.importance,
        "version": ann.version,
        "history_count": len(ann.history or []),
        "created_at": ann.created_at.isoformat() if ann.created_at else None,
        "updated_at": ann.updated_at.isoformat() if ann.updated_at else None,
    }


# --- 端点 ---

@router.post("", summary="创建批注")
def create_annotation(body: AnnotationCreate, db: Session = Depends(get_db)):
    """创建批注"""
    if body.entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(400, f"entity_type 必须是 {VALID_ENTITY_TYPES} 之一")

    now = datetime.now(timezone.utc).isoformat()
    ann = Annotation(
        annotation_id=str(uuid.uuid4()),
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        content=body.content,
        tags=body.tags,
        importance=body.importance,
        version="1",
        history=[],
        access_log=[{"action": "create", "ts": now}],
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return _to_dict(ann)


@router.get("", summary="获取批注列表")
def list_annotations(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    tag: Optional[str] = None,
    importance: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """按类型/ID/标签/重要性过滤批注"""
    q = db.query(Annotation)
    if entity_type:
        q = q.filter(Annotation.entity_type == entity_type)
    if entity_id:
        q = q.filter(Annotation.entity_id == entity_id)
    if tag:
        q = q.filter(Annotation.tags.contains(tag))
    if importance:
        q = q.filter(Annotation.importance == importance)
    total = q.count()
    items = q.order_by(Annotation.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": [_to_dict(a) for a in items]}


@router.get("/{annotation_id}", summary="获取单条批注（含完整历史）")
def get_annotation(annotation_id: str, db: Session = Depends(get_db)):
    ann = db.query(Annotation).filter_by(annotation_id=annotation_id).first()
    if not ann:
        raise HTTPException(404, "批注不存在")
    # 记访问日志
    log = list(ann.access_log or [])
    log.append({"action": "read", "ts": datetime.now(timezone.utc).isoformat()})
    ann.access_log = log[-20:]  # 最多留20条
    db.commit()
    result = _to_dict(ann)
    result["history"] = ann.history or []
    result["access_log"] = ann.access_log
    return result


@router.patch("/{annotation_id}", summary="更新批注（自动增加版本号并保留历史快照）")
def update_annotation(
    annotation_id: str,
    body: AnnotationUpdate,
    db: Session = Depends(get_db),
):
    ann = db.query(Annotation).filter_by(annotation_id=annotation_id).first()
    if not ann:
        raise HTTPException(404, "批注不存在")

    # 当前版本存历史
    history = list(ann.history or [])
    history.append({
        "version": ann.version,
        "content": ann.content,
        "tags": ann.tags,
        "importance": ann.importance,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    })
    if len(history) > HISTORY_LIMIT:
        history = history[-HISTORY_LIMIT:]

    # 更新
    ann.content = body.content
    if body.tags is not None:
        ann.tags = body.tags
    if body.importance is not None:
        ann.importance = body.importance
    ann.version = str(int(ann.version or "1") + 1)
    ann.history = history
    ann.updated_at = datetime.now(timezone.utc)

    # 访问日志
    log = list(ann.access_log or [])
    log.append({"action": "update", "ts": ann.updated_at.isoformat()})
    ann.access_log = log[-20:]

    db.commit()
    db.refresh(ann)
    result = _to_dict(ann)
    result["history"] = ann.history
    return result


@router.delete("/{annotation_id}", summary="删除批注")
def delete_annotation(annotation_id: str, db: Session = Depends(get_db)):
    ann = db.query(Annotation).filter_by(annotation_id=annotation_id).first()
    if not ann:
        raise HTTPException(404, "批注不存在")
    db.delete(ann)
    db.commit()
    return {"status": "deleted", "annotation_id": annotation_id}


@router.get("/entity/{entity_type}/{entity_id}", summary="获取实体的所有批注（快捷路由）")
def get_entity_annotations(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
):
    """按实体类型+ID查批注"""
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(400, f"entity_type 必须是 {VALID_ENTITY_TYPES} 之一")
    items = (
        db.query(Annotation)
        .filter_by(entity_type=entity_type, entity_id=entity_id)
        .order_by(Annotation.created_at.asc())
        .all()
    )
    return {"entity_type": entity_type, "entity_id": entity_id, "total": len(items), "items": [_to_dict(a) for a in items]}
