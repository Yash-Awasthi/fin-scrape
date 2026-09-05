"""
历史案例类比推理 - Claude语义匹配找相关案例注入推演上下文
案例库从JSON文件迁移到数据库存储，支持动态CRUD管理
"""
import json
import os
import uuid
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.models.ir_event import AbstractIRGEvent
from backend.models.historical_case import HistoricalCase, case_to_dict
from backend.core.llm_router import llm_call_json

logger = logging.getLogger("analogy")

CASES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "historical_cases.json")

_cases_cache: Optional[List[Dict]] = None


def _invalidate_cache():
    global _cases_cache
    _cases_cache = None


def _safe_join(val, sep: str = ", ") -> str:
    if not val:
        return ""
    if isinstance(val, str):
        return val
    try:
        return sep.join(str(v) for v in val)
    except Exception:
        return str(val)


def _case_title(case: Dict) -> str:
    return case.get("title") or case.get("case_title") or "未知案例"


ANALOGY_MATCH_SYSTEM = """
你是一位顶级国际关系史学家，同时精通当代地缘政治分析。
你的任务是：从给定的历史案例库中，找出与当前事件最相关的类比案例，
并深度分析每个类比的适用性与局限性。

核心原则：
1. 类比必须有具体的结构性相似（不是表面相似）
2. 必须指出类比的局限性和反类比理由
3. 历史经验必须转化为对当前推演的具体推断
4. 如果没有好的类比，明确说明，不要强行比附
"""

ANALOGY_MATCH_USER = """
当前待分析事件：
- 事件标题：{event_title}
- 事件类型：{event_type}
- 危机阶段：{crisis_stage}
- 主要行为主体：{key_actors}
- 核心议题：{primary_issue}
- 驱动力：{driving_forces}
- 主要约束：{constraints}
- 当前态势：{current_balance}
- 地区：{region}

历史案例库（共 {case_count} 个案例）：
{cases_summary}

请从案例库中选择 2-3 个最相关的类比案例，返回以下 JSON：

```json
{{
  "matched_cases": [
    {{
      "case_id": "案例ID",
      "case_title": "案例标题",
      "similarity_score": 0.85,
      "structural_similarities": [
        "结构性相似点1（具体描述，不是泛泛而谈）",
        "结构性相似点2"
      ],
      "key_differences": [
        "关键差异1（为什么当前情况与历史不同）",
        "关键差异2"
      ],
      "historical_outcome": "历史上这个案例实际如何演变",
      "analogy_implications_for_current": [
        "对当前推演的具体启示1",
        "对当前推演的具体启示2"
      ],
      "warning_from_history": "历史给当前分析的最重要警示",
      "probability_adjustment": {{
        "escalation_adjustment": "基于此类比，升级概率应该调整的方向和理由",
        "stalemate_adjustment": "僵持概率调整",
        "de_escalation_adjustment": "缓和概率调整"
      }},
      "analogy_confidence": "high/medium/low",
      "analogy_confidence_reason": "为什么这个类比的置信度是这个水平"
    }}
  ],
  "synthesis": "综合多个类比的总体推断（200字以上）",
  "historical_base_rate": {{
    "escalation_historical_rate": "在类似历史情境中，升级发生的历史概率（基于案例库）",
    "stalemate_historical_rate": "僵持的历史概率",
    "de_escalation_historical_rate": "缓和的历史概率",
    "caveats": "历史基础概率的局限性说明"
  }},
  "unique_modern_factors": [
    "当前事件中没有历史先例的新因素（如AI/核武器/社交媒体/全球化经济依存度）"
  ]
}}
```
"""


def find_historical_analogies(
    db: Session,
    event_id: str,
    max_cases: int = 3,
    force_regenerate: bool = False,
) -> Optional[Dict]:
    from backend.models.analogy import HistoricalAnalogyResult

    if not force_regenerate:
        cached = db.query(HistoricalAnalogyResult).filter_by(event_id=event_id).first()
        if cached:
            logger.info(f"[analogy] 使用缓存结果: {event_id}")
            return _result_to_dict(cached)

    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()
    if not event:
        return None

    cases = _load_cases(db)
    if not cases:
        logger.error("[analogy] 历史案例库加载失败")
        return None

    cases_summary = _build_cases_summary(cases)

    user_msg = ANALOGY_MATCH_USER.format(
        event_title=event.event_title,
        event_type=event.event_type,
        crisis_stage=event.stage_of_crisis or "unknown",
        key_actors=_safe_join(event.key_actors),
        primary_issue=(event.driving_forces[0] if event.driving_forces else None) or event.current_balance or "未知",
        driving_forces=_safe_join(event.driving_forces),
        constraints=_safe_join(event.constraints),
        current_balance=event.current_balance or "未知",
        region=event.region or "Global",
        case_count=len(cases),
        cases_summary=cases_summary,
    )

    logger.info(f"[analogy] 为事件 '{event.event_title}' 匹配历史类比...")
    result = llm_call_json("analogy_matching", ANALOGY_MATCH_SYSTEM, user_msg,
                           timeout_seconds=300)

    if result is None or result.get("parse_error"):
        logger.warning("[analogy] Claude 返回解析失败，使用规则回退")
        return _rule_based_fallback(event, cases)

    enriched = _enrich_result_with_case_data(result, cases)

    _save_analogy_result(db, event_id, enriched)

    return enriched


def get_analogies_for_event(db: Session, event_id: str) -> Optional[Dict]:
    from backend.models.analogy import HistoricalAnalogyResult
    cached = db.query(HistoricalAnalogyResult).filter_by(event_id=event_id).first()
    if cached:
        return _result_to_dict(cached)
    return None


def get_all_cases(db: Session = None) -> List[Dict]:
    if db is not None:
        return _load_cases(db)
    return _load_cases_from_json()


def get_case_by_id(case_id: str, db: Session = None) -> Optional[Dict]:
    if db is not None:
        row = db.query(HistoricalCase).filter_by(case_id=case_id).first()
        if row:
            return case_to_dict(row)
        return None
    cases = _load_cases_from_json()
    for case in cases:
        if case.get("case_id") == case_id:
            return case
    return None


def build_analogy_context_for_scenario(event_id: str, db: Session) -> str:
    analogies = get_analogies_for_event(db, event_id)
    if not analogies:
        analogies = find_historical_analogies(db, event_id)
    if not analogies:
        return "（历史类比：无可用案例）"

    lines = ["【历史类比推理（必须在剧本步骤中引用）】"]

    for case in analogies.get("matched_cases", [])[:3]:
        lines.append(
            f"\n类比案例：{case.get('case_title', '')} "
            f"（相似度={case.get('similarity_score', 0):.0%}，置信={case.get('analogy_confidence', 'low')}）"
        )
        sims = case.get("structural_similarities", [])
        if sims:
            lines.append(f"  结构相似：{sims[0]}")
        implications = case.get("analogy_implications_for_current", [])
        if implications:
            lines.append(f"  当前推断：{implications[0]}")
        warning = case.get("warning_from_history", "")
        if warning:
            lines.append(f"  历史警示：{warning}")

    hist_rates = analogies.get("historical_base_rate", {})
    if hist_rates:
        lines.append(
            f"\n历史基础概率参考："
            f"升级={hist_rates.get('escalation_historical_rate', 'N/A')} | "
            f"僵持={hist_rates.get('stalemate_historical_rate', 'N/A')} | "
            f"缓和={hist_rates.get('de_escalation_historical_rate', 'N/A')}"
        )

    synthesis = analogies.get("synthesis", "")
    if synthesis:
        lines.append(f"\n综合推断：{synthesis[:200]}...")

    return "\n".join(lines)


# --- 案例CRUD ---

def create_case(db: Session, data: Dict) -> Dict:
    case_id = data.get("case_id") or f"custom_{uuid.uuid4().hex[:12]}"
    existing = db.query(HistoricalCase).filter_by(case_id=case_id).first()
    if existing:
        raise ValueError(f"case_id '{case_id}' 已存在")

    row = HistoricalCase(
        case_id=case_id,
        title=data.get("title", ""),
        title_en=data.get("title_en", ""),
        year=data.get("year"),
        duration_days=data.get("duration_days"),
        event_type=data.get("event_type", ""),
        region=data.get("region", ""),
        crisis_stage_peak=data.get("crisis_stage_peak", ""),
        key_actors=data.get("key_actors", []),
        actor_roles=data.get("actor_roles", {}),
        primary_issue=data.get("primary_issue", ""),
        strategic_dimensions=data.get("strategic_dimensions", []),
        key_triggers=data.get("key_triggers", []),
        key_constraints=data.get("key_constraints", []),
        escalation_path=data.get("escalation_path", []),
        resolution=data.get("resolution", ""),
        resolution_type=data.get("resolution_type", ""),
        outcome_summary=data.get("outcome_summary", ""),
        key_lessons=data.get("key_lessons", []),
        analogous_features=data.get("analogous_features", []),
        probability_realized=data.get("probability_realized", {}),
        actual_outcome_direction=data.get("actual_outcome_direction", ""),
        prediction_accuracy_notes=data.get("prediction_accuracy_notes", ""),
        tags=data.get("tags", []),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    _invalidate_cache()
    logger.info(f"[analogy] 创建案例: {case_id}")
    return case_to_dict(row)


def update_case(db: Session, case_id: str, data: Dict) -> Optional[Dict]:
    row = db.query(HistoricalCase).filter_by(case_id=case_id).first()
    if not row:
        return None

    updatable_fields = [
        "title", "title_en", "year", "duration_days",
        "event_type", "region", "crisis_stage_peak",
        "key_actors", "actor_roles", "primary_issue",
        "strategic_dimensions", "key_triggers", "key_constraints",
        "escalation_path", "resolution", "resolution_type",
        "outcome_summary", "key_lessons", "analogous_features",
        "probability_realized", "actual_outcome_direction",
        "prediction_accuracy_notes", "tags",
    ]
    for field in updatable_fields:
        if field in data:
            setattr(row, field, data[field])

    db.commit()
    db.refresh(row)
    _invalidate_cache()
    logger.info(f"[analogy] 更新案例: {case_id}")
    return case_to_dict(row)


def delete_case(db: Session, case_id: str) -> bool:
    row = db.query(HistoricalCase).filter_by(case_id=case_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    _invalidate_cache()
    logger.info(f"[analogy] 删除案例: {case_id}")
    return True


def seed_cases_from_json(db: Session) -> int:
    count = db.query(HistoricalCase).count()
    if count > 0:
        logger.info(f"[analogy] 案例库已有 {count} 条，跳过种子")
        return 0

    try:
        with open(CASES_FILE, "r", encoding="utf-8") as f:
            json_cases = json.load(f)
    except Exception as e:
        logger.error(f"[analogy] 种子文件加载失败: {e}")
        return 0

    seeded = 0
    for data in json_cases:
        case_id = data.get("case_id", "")
        if not case_id:
            continue
        existing = db.query(HistoricalCase).filter_by(case_id=case_id).first()
        if existing:
            continue
        row = HistoricalCase(
            case_id=case_id,
            title=data.get("title", ""),
            title_en=data.get("title_en", ""),
            year=data.get("year"),
            duration_days=data.get("duration_days"),
            event_type=data.get("event_type", ""),
            region=data.get("region", ""),
            crisis_stage_peak=data.get("crisis_stage_peak", ""),
            key_actors=data.get("key_actors", []),
            actor_roles=data.get("actor_roles", {}),
            primary_issue=data.get("primary_issue", ""),
            strategic_dimensions=data.get("strategic_dimensions", []),
            key_triggers=data.get("key_triggers", []),
            key_constraints=data.get("key_constraints", []),
            escalation_path=data.get("escalation_path", []),
            resolution=data.get("resolution", ""),
            resolution_type=data.get("resolution_type", ""),
            outcome_summary=data.get("outcome_summary", ""),
            key_lessons=data.get("key_lessons", []),
            analogous_features=data.get("analogous_features", []),
            probability_realized=data.get("probability_realized", {}),
            actual_outcome_direction=data.get("actual_outcome_direction", ""),
            prediction_accuracy_notes=data.get("prediction_accuracy_notes", ""),
            tags=data.get("tags", []),
        )
        db.add(row)
        seeded += 1

    db.commit()
    _invalidate_cache()
    logger.info(f"[analogy] 从JSON种子导入 {seeded} 条案例")
    return seeded


# --- 内部函数 ---

def _load_cases(db: Session) -> List[Dict]:
    global _cases_cache
    if _cases_cache is not None:
        return _cases_cache
    rows = db.query(HistoricalCase).all()
    if rows:
        _cases_cache = [case_to_dict(r) for r in rows]
        return _cases_cache
    json_cases = _load_cases_from_json()
    if json_cases:
        _cases_cache = json_cases
    return _cases_cache


def _load_cases_from_json() -> List[Dict]:
    try:
        with open(CASES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[analogy] JSON案例库加载失败: {e}")
        return []


def _build_cases_summary(cases: List[Dict]) -> str:
    lines = []
    for c in cases:
        lines.append(
            f"[{c.get('case_id', '?')}] {_case_title(c)} ({c.get('year', '?')}) | "
            f"类型:{c.get('event_type', '?')} | 地区:{c.get('region', '?')} | "
            f"实际结果:{c.get('actual_outcome_direction', 'N/A')} | "
            f"标签:{','.join(c.get('tags', [])[:4])}"
        )
    return "\n".join(lines)


def _enrich_result_with_case_data(result: Dict, cases: List[Dict]) -> Dict:
    case_map = {c["case_id"]: c for c in cases}
    enriched_cases = []

    for matched in result.get("matched_cases", []):
        case_id = matched.get("case_id", "")
        full_case = case_map.get(case_id, {})
        enriched = {
            **matched,
            "full_case": {
                "year": full_case.get("year"),
                "duration_days": full_case.get("duration_days"),
                "key_actors": full_case.get("key_actors", []),
                "key_lessons": full_case.get("key_lessons", []),
                "outcome_summary": full_case.get("outcome_summary", ""),
                "actual_outcome_direction": full_case.get("actual_outcome_direction"),
                "probability_realized": full_case.get("probability_realized", {}),
                "prediction_accuracy_notes": full_case.get("prediction_accuracy_notes", ""),
                "tags": full_case.get("tags", []),
            }
        }
        enriched_cases.append(enriched)

    return {**result, "matched_cases": enriched_cases, "total_cases_searched": len(cases)}


def _rule_based_fallback(event: AbstractIRGEvent, cases: List[Dict]) -> Dict:
    relevant = []
    for case in cases:
        score = 0
        if case.get("event_type") == event.event_type:
            score += 3
        if case.get("region") == event.region:
            score += 2
        case_actors = set(case.get("key_actors", []))
        event_actors = set(event.key_actors or [])
        overlap = len(case_actors & event_actors)
        score += overlap
        if score > 0:
            relevant.append((score, case))

    relevant.sort(key=lambda x: -x[0])
    top_cases = [c for _, c in relevant[:3]]

    matched = []
    for case in top_cases:
        matched.append({
            "case_id": case.get("case_id", ""),
            "case_title": _case_title(case),
            "similarity_score": 0.5,
            "structural_similarities": [f"事件类型相同: {case.get('event_type')}"],
            "key_differences": ["规则匹配，需人工验证具体相似点"],
            "historical_outcome": case.get("outcome_summary", ""),
            "analogy_implications_for_current": [(case.get("key_lessons") or ["参见历史记录"])[0]],
            "warning_from_history": case.get("prediction_accuracy_notes", ""),
            "analogy_confidence": "low",
            "analogy_confidence_reason": "规则匹配回退，未经Claude语义验证",
            "full_case": {
                "year": case.get("year"),
                "key_lessons": case.get("key_lessons", []),
                "outcome_summary": case.get("outcome_summary", ""),
                "actual_outcome_direction": case.get("actual_outcome_direction"),
                "probability_realized": case.get("probability_realized", {}),
                "tags": case.get("tags", []),
            }
        })

    return {
        "matched_cases": matched,
        "synthesis": "规则匹配回退结果，建议人工验证",
        "historical_base_rate": {
            "escalation_historical_rate": "N/A",
            "stalemate_historical_rate": "N/A",
            "de_escalation_historical_rate": "N/A",
            "caveats": "规则匹配回退，基础概率不可靠",
        },
        "unique_modern_factors": [],
        "total_cases_searched": len(cases),
        "is_fallback": True,
    }


def _save_analogy_result(db: Session, event_id: str, result: Dict):
    try:
        from backend.models.analogy import HistoricalAnalogyResult

        existing = db.query(HistoricalAnalogyResult).filter_by(event_id=event_id).first()
        if existing:
            existing.matched_cases = result.get("matched_cases", [])
            existing.synthesis = result.get("synthesis", "")
            existing.historical_base_rate = result.get("historical_base_rate", {})
            existing.unique_modern_factors = result.get("unique_modern_factors", [])
            existing.total_cases_searched = result.get("total_cases_searched", 0)
        else:
            record = HistoricalAnalogyResult(
                analogy_id=str(uuid.uuid4()),
                event_id=event_id,
                matched_cases=result.get("matched_cases", []),
                synthesis=result.get("synthesis", ""),
                historical_base_rate=result.get("historical_base_rate", {}),
                unique_modern_factors=result.get("unique_modern_factors", []),
                total_cases_searched=result.get("total_cases_searched", 0),
            )
            db.add(record)
        db.commit()
    except Exception as e:
        logger.error(f"[analogy] 保存失败: {e}")
        db.rollback()


def _result_to_dict(record) -> Dict:
    return {
        "analogy_id": record.analogy_id,
        "event_id": record.event_id,
        "matched_cases": record.matched_cases or [],
        "synthesis": record.synthesis or "",
        "historical_base_rate": record.historical_base_rate or {},
        "unique_modern_factors": record.unique_modern_factors or [],
        "total_cases_searched": record.total_cases_searched or 0,
        "generated_at": record.generated_at.isoformat() if record.generated_at else None,
    }
