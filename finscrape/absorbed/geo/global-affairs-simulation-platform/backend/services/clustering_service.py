"""
新闻聚类，分批调Claude，回退走TF-IDF相似度分组
"""
import uuid
import math
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models.raw_news import RawNews
from backend.models.news_cluster import NewsCluster
from backend.core.llm_router import llm_call_json
from backend.core.prompts import CLUSTERING_SYSTEM_PROMPT, CLUSTERING_USER_TEMPLATE

logger = logging.getLogger(__name__)


def format_news_for_clustering(news_list: List[RawNews]) -> str:
    """格式化新闻给Prompt，只取标题+摘要80字+地区"""
    lines = []
    for i, news in enumerate(news_list):
        entities = news.raw_entities or {}
        countries = entities.get("countries", [])
        lines.append(
            f"[{i}] {news.source_name} | {news.published_at.strftime('%m-%d') if news.published_at else '?'}\n"
            f"    标题: {news.title}\n"
            f"    摘要: {(news.body or '')[:80]}\n"
            f"    地区/国家: {', '.join((news.region_tags or [])[:2])} {', '.join(countries[:3])}\n"
        )
    return "\n".join(lines)


def cluster_news(db: Session, news_ids: Optional[List[str]] = None) -> List[Dict]:
    """聚类主函数，分批调Claude"""
    query = db.query(RawNews).filter(RawNews.cluster_id.is_(None))
    if news_ids:
        query = query.filter(RawNews.news_id.in_(news_ids))
    news_list = query.order_by(RawNews.published_at.desc()).limit(80).all()

    if len(news_list) < 2:
        return []

    # 时间窗口
    dates = [n.published_at for n in news_list if n.published_at]
    time_window = (
        f"{min(dates).strftime('%Y-%m-%d') if dates else '未知'} ~ "
        f"{max(dates).strftime('%Y-%m-%d') if dates else '未知'}"
    )

    # 分批，每批≤25条防截断
    BATCH_SIZE = 25
    all_clusters: List[Dict] = []
    batches = [news_list[i:i + BATCH_SIZE] for i in range(0, len(news_list), BATCH_SIZE)]
    logger.info(f"[clustering] 共 {len(news_list)} 条新闻，分 {len(batches)} 批处理")

    for batch_idx, batch in enumerate(batches):
        logger.info(f"[clustering] 处理第 {batch_idx + 1}/{len(batches)} 批 ({len(batch)} 条)...")
        batch_clusters = _cluster_batch(db, batch, time_window, batch_idx)
        all_clusters.extend(batch_clusters)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"[clustering] 最终 commit 失败（数据可能已在批次内提交）: {e}")
    logger.info(f"[clustering] 完成：{len(all_clusters)} 个事件簇")
    return all_clusters


def _cluster_batch(db: Session, news_list: List[RawNews], time_window: str, batch_idx: int) -> List[Dict]:
    """单批聚类，失败走回退"""
    formatted = format_news_for_clustering(news_list)
    user_msg = CLUSTERING_USER_TEMPLATE.format(
        news_count=len(news_list),
        time_window=time_window,
        news_list=formatted,
    )

    result = llm_call_json(
        "cluster_summarization", CLUSTERING_SYSTEM_PROMPT, user_msg,
        timeout_seconds=300,   # 每批≤25条，60s够
    )

    if result is None or result.get("parse_error"):
        logger.warning(f"[clustering] 第 {batch_idx + 1} 批 Claude 返回解析失败，使用回退逻辑")
        return _fallback_clustering(db, news_list)

    clusters = []
    for cluster_data in result.get("clusters", []):
        cluster_id = str(uuid.uuid4())
        news_indices = cluster_data.get("related_news_indices", [])
        related_ids = [news_list[i].news_id for i in news_indices if i < len(news_list)]

        # 解析时间
        time_start = time_end = None
        try:
            if cluster_data.get("time_window_start"):
                time_start = datetime.strptime(cluster_data["time_window_start"], "%Y-%m-%d")
            if cluster_data.get("time_window_end"):
                time_end = datetime.strptime(cluster_data["time_window_end"], "%Y-%m-%d")
        except Exception:
            pass

        # key_actors可能是dict格式
        key_actors_raw = cluster_data.get("key_actors", [])
        if isinstance(key_actors_raw, dict):
            # 升级版格式
            key_actors = (
                key_actors_raw.get("primary_actors", []) +
                key_actors_raw.get("reactive_actors", []) +
                key_actors_raw.get("background_actors", [])
            )
        else:
            key_actors = key_actors_raw

        # escalation_signals可能是带强度的dict
        escalation_signals_raw = cluster_data.get("escalation_signals", [])
        escalation_signals = _normalize_signals(escalation_signals_raw)

        deescalation_signals_raw = cluster_data.get("deescalation_signals", [])
        deescalation_signals = _normalize_signals(deescalation_signals_raw)

        # evidence_summary加触发器分析
        evidence_summary = cluster_data.get("evidence_summary", "")
        trigger_rationale = cluster_data.get("trigger_rationale", "")
        if trigger_rationale:
            evidence_summary = f"[触发器分析] {trigger_rationale}\n\n{evidence_summary}"

        # 战略联动存进secondary_issues
        secondary_issues = cluster_data.get("secondary_issues", [])
        strategic_linkages = cluster_data.get("strategic_linkages", [])
        if strategic_linkages:
            secondary_issues = secondary_issues + [f"[战略联动] {linkage}" for linkage in strategic_linkages[:2]]

        cluster = NewsCluster(
            cluster_id=cluster_id,
            cluster_title=cluster_data.get("cluster_title", "未命名事件簇"),
            related_news_ids=related_ids,
            time_window_start=time_start,
            time_window_end=time_end,
            key_actors=key_actors[:10],  # 限数
            key_locations=cluster_data.get("key_locations", []),
            primary_issue=cluster_data.get("primary_issue", ""),
            secondary_issues=secondary_issues[:6],
            escalation_signals=escalation_signals,
            deescalation_signals=deescalation_signals,
            evidence_summary=evidence_summary,
            cluster_confidence=cluster_data.get("cluster_confidence", 0.7),
        )
        db.add(cluster)

        # 更新cluster_id
        for idx in news_indices:
            if idx < len(news_list):
                news_list[idx].cluster_id = cluster_id
                news_list[idx].status = "clustered"

        clusters.append({
            "cluster_id": cluster_id,
            "cluster_title": cluster.cluster_title,
            "news_count": len(related_ids),
            "key_actors": cluster.key_actors,
            "primary_issue": cluster.primary_issue,
            "escalation_signals_count": len(escalation_signals),
            "has_strategic_linkages": bool(strategic_linkages),
        })

    # 跨簇关联
    cross_cluster = result.get("cross_cluster_dynamics", "")
    if cross_cluster:
        logger.info(f"[clustering] 批次{batch_idx+1} 跨簇战略关联: {cross_cluster[:100]}...")

    logger.info(f"[clustering] 批次{batch_idx+1} 完成：{len(clusters)} 个事件簇")
    return clusters


def _normalize_signals(signals_raw) -> List[str]:
    """信号格式统一，兼容str和dict"""
    if not signals_raw:
        return []
    result = []
    for s in signals_raw:
        if isinstance(s, str):
            result.append(s)
        elif isinstance(s, dict):
            signal = s.get("signal", "")
            strength = s.get("strength", "")
            rationale = s.get("rationale", "")
            if signal:
                entry = signal
                if strength:
                    entry = f"[{strength.upper()}] {entry}"
                if rationale:
                    entry = f"{entry}（{rationale[:80]}）"
                result.append(entry)
    return result


def _fallback_clustering(db: Session, news_list: List[RawNews]) -> List[Dict]:
    """回退：TF-IDF相似度分组，失败再按地区"""
    try:
        return _tfidf_fallback(db, news_list)
    except Exception as e:
        logger.warning(f"[clustering] TF-IDF回退失败({e})，使用地区分组")
        return _region_fallback(db, news_list)


def _tfidf_fallback(db: Session, news_list: List[RawNews]) -> List[Dict]:
    """TF-IDF + 余弦相似度聚类回退"""
    docs = []
    for news in news_list:
        text = f"{news.title or ''} {news.body or ''}"
        entities = news.raw_entities or {}
        countries = entities.get("countries", [])
        orgs = entities.get("organizations", [])
        persons = entities.get("persons", [])
        for c in countries:
            text += f" {c}"
        for o in orgs:
            text += f" {o}"
        for p in persons:
            text += f" {p}"
        docs.append(text)

    tfidf_matrix, vocab = _compute_tfidf(docs)
    if not vocab:
        return _region_fallback(db, news_list)

    n = len(news_list)
    similarity_threshold = 0.15
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            sim = _cosine_similarity(tfidf_matrix[i], tfidf_matrix[j], len(vocab))
            if sim >= similarity_threshold:
                union(i, j)

    groups: Dict[int, List[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    clusters = []
    for root, indices in groups.items():
        if len(indices) < 2:
            continue
        group_news = [news_list[i] for i in indices]
        cluster_id = str(uuid.uuid4())
        related_ids = [news_list[i].news_id for i in indices]

        regions = set()
        actors = []
        for news in group_news:
            for r in (news.region_tags or [])[:1]:
                regions.add(r)
            entities = news.raw_entities or {}
            for c in entities.get("countries", [])[:3]:
                if c not in actors:
                    actors.append(c)

        titles = [news_list[i].title or "" for i in indices]
        common_words = _extract_common_keywords(titles)

        region_str = ", ".join(regions) if regions else "Global"
        keyword_str = "、".join(common_words[:3]) if common_words else "相关事件"
        cluster_title = f"{region_str}：{keyword_str}（TF-IDF分组）"

        cluster = NewsCluster(
            cluster_id=cluster_id,
            cluster_title=cluster_title,
            related_news_ids=related_ids,
            key_actors=actors[:10],
            key_locations=list(regions),
            primary_issue=keyword_str,
            cluster_confidence=0.55,
        )
        db.add(cluster)
        for i in indices:
            news_list[i].cluster_id = cluster_id
            news_list[i].status = "clustered"
        clusters.append({
            "cluster_id": cluster_id,
            "cluster_title": cluster_title,
            "news_count": len(indices),
        })

    unclustered = [i for i in range(n) if find(i) == i and len(groups.get(i, [])) < 2]
    if unclustered:
        cluster_id = str(uuid.uuid4())
        related_ids = [news_list[i].news_id for i in unclustered]
        cluster = NewsCluster(
            cluster_id=cluster_id,
            cluster_title="其他未关联新闻（TF-IDF分组）",
            related_news_ids=related_ids,
            key_actors=[],
            key_locations=[],
            primary_issue="待进一步分析",
            cluster_confidence=0.3,
        )
        db.add(cluster)
        for i in unclustered:
            news_list[i].cluster_id = cluster_id
            news_list[i].status = "clustered"
        clusters.append({
            "cluster_id": cluster_id,
            "cluster_title": cluster.cluster_title,
            "news_count": len(unclustered),
        })

    logger.info(f"[clustering] TF-IDF回退：{len(clusters)} 个簇")
    return clusters


def _region_fallback(db: Session, news_list: List[RawNews]) -> List[Dict]:
    """地区分组回退（最底层）"""
    region_groups: Dict[str, List[RawNews]] = {}
    for news in news_list:
        region = (news.region_tags or ["Global"])[0]
        region_groups.setdefault(region, []).append(news)

    clusters = []
    for region, group in region_groups.items():
        if len(group) < 2:
            continue
        cluster_id = str(uuid.uuid4())
        related_ids = [n.news_id for n in group]
        cluster = NewsCluster(
            cluster_id=cluster_id,
            cluster_title=f"{region} 地区事件簇（自动分组）",
            related_news_ids=related_ids,
            key_actors=[],
            key_locations=[region],
            primary_issue="待进一步分析",
            cluster_confidence=0.4,
        )
        db.add(cluster)
        for n in group:
            n.cluster_id = cluster_id
            n.status = "clustered"
        clusters.append({
            "cluster_id": cluster_id,
            "cluster_title": cluster.cluster_title,
            "news_count": len(group),
        })

    return clusters


# --- TF-IDF 工具函数 ---

_STOP_WORDS = frozenset([
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
    "neither", "each", "every", "all", "any", "few", "more", "most", "other",
    "some", "such", "no", "only", "own", "same", "than", "too", "very",
    "just", "because", "if", "when", "where", "how", "what", "which", "who",
    "that", "this", "these", "those", "it", "its", "he", "she", "they",
    "we", "you", "i", "me", "him", "her", "us", "them", "my", "your",
    "his", "our", "their",
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这",
])


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r'[a-zA-Z]{2,}|[\u4e00-\u9fff]{2,}', text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) >= 2]


def _compute_tfidf(docs: List[str]) -> Tuple[List[Dict[str, float]], List[str]]:
    if not docs:
        return [], []

    tokenized = [_tokenize(doc) for doc in docs]
    doc_freq = Counter()
    for tokens in tokenized:
        unique = set(tokens)
        for t in unique:
            doc_freq[t] += 1

    min_df = max(1, len(docs) // 10)
    max_df = len(docs) * 8 // 10
    vocab = [t for t, df in doc_freq.items() if min_df <= df <= max_df]
    vocab_set = set(vocab)

    n_docs = len(docs)
    idf = {}
    for t in vocab:
        idf[t] = math.log((n_docs + 1) / (doc_freq[t] + 1)) + 1

    tfidf_matrix = []
    for tokens in tokenized:
        tf = Counter(t for t in tokens if t in vocab_set)
        total = sum(tf.values()) or 1
        vec = {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}
        tfidf_matrix.append(vec)

    return tfidf_matrix, vocab


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float], vocab_size: int) -> float:
    common = set(vec_a.keys()) & set(vec_b.keys())
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _extract_common_keywords(titles: List[str], top_k: int = 5) -> List[str]:
    all_tokens = []
    for title in titles:
        all_tokens.extend(_tokenize(title))
    if not all_tokens:
        return []
    counter = Counter(all_tokens)
    return [t for t, _ in counter.most_common(top_k)]
