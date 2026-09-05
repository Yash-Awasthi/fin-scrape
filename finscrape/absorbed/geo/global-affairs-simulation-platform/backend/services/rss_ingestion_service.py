"""RSS新闻采集 - 多源并发/去重/规范化/重试"""
import uuid
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models.raw_news import RawNews
from backend.services.source_registry import NewsSource, get_enabled_sources
from backend.services._ingestion_utils import compute_dedupe_hash, extract_region_tags, simple_entity_extract

logger = logging.getLogger("ingestion")

DATA_STATUS_LIVE = "live"
DATA_STATUS_STALE_SNAPSHOT = "stale_snapshot"
DATA_STATUS_MOCK = "mock"
DATA_STATUS_EMPTY = "empty"


class IngestionResult:
    def __init__(self):
        self.total_fetched = 0
        self.total_saved = 0
        self.total_skipped_dup = 0
        self.total_failed_sources = 0
        self.source_results: List[Dict] = []
        self.data_status: str = DATA_STATUS_EMPTY
        self.errors: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "total_fetched": self.total_fetched,
            "total_saved": self.total_saved,
            "total_skipped_dup": self.total_skipped_dup,
            "total_failed_sources": self.total_failed_sources,
            "data_status": self.data_status,
            "source_results": self.source_results,
            "errors": self.errors,
        }


# --- 核心采集 ---

def fetch_all_sources(
    db: Session,
    source_ids: Optional[List[str]] = None,
    max_per_source: Optional[int] = None,
    timeout_seconds: int = 15,
) -> IngestionResult:
    """从所有启用源采集新闻"""
    try:
        import feedparser
    except ImportError:
        logger.error("feedparser 未安装，请运行: pip install feedparser")
        result = IngestionResult()
        result.errors.append("feedparser not installed")
        result.data_status = DATA_STATUS_EMPTY
        return result

    # 代理配置：环境变量优先，兼容Windows系统代理
    import os
    proxy_url = (
        os.environ.get("RSS_PROXY") or
        os.environ.get("HTTPS_PROXY") or
        os.environ.get("HTTP_PROXY") or
        os.environ.get("https_proxy") or
        os.environ.get("http_proxy")
    )

    # 尝试读Windows注册表代理
    if not proxy_url:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
                enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if enabled:
                    server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    if server and ":" in server:
                        proxy_url = f"http://{server}"
                        logger.info(f"[ingestion] 自动检测到 Windows 系统代理: {proxy_url}")
        except Exception:
            pass

    # SSL容错 + urllib opener
    import ssl
    import urllib.request
    import urllib.error

    from backend.core.config import settings

    ssl_ctx = ssl.create_default_context()

    if settings.SSL_VERIFY:
        logger.info("[ingestion] SSL 证书验证已启用（安全模式）")
    else:
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        logger.warning(
            "⚠️  [安全] SSL 证书验证已禁用（SSL_VERIFY=false），"
            "存在中间人攻击(MITM)风险！仅限开发环境使用。"
        )

    try:
        ssl_ctx.options |= ssl.OP_IGNORE_UNEXPECTED_EOF
    except AttributeError:
        pass

    try:
        ssl_ctx.options |= 0x4
    except Exception:
        pass

    https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)

    handlers_list: list = [https_handler]
    if proxy_url:
        logger.info(f"[ingestion] 使用代理采集 RSS: {proxy_url}")
        handlers_list.append(urllib.request.ProxyHandler({
            "http": proxy_url,
            "https": proxy_url,
        }))
    else:
        logger.info("[ingestion] 无代理配置，直连采集 RSS")

    # 自建opener，SSL+proxy完全自己控制
    _opener = urllib.request.build_opener(*handlers_list)

    FETCH_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }

    sources = get_enabled_sources()
    if source_ids:
        sources = [s for s in sources if s.source_id in source_ids]

    result = IngestionResult()

    # Phase 1: 并发HTTP拉取，不碰DB
    max_workers = min(10, len(sources))
    # sources为空时跳过，否则ThreadPoolExecutor会报错
    if max_workers == 0:
        return result
    raw_feeds: Dict[str, Tuple] = {}

    def _fetch_http(source: "NewsSource") -> Tuple:
        """纯HTTP拉取，返回(source, entries, error)，不碰DB

        用自建opener拉bytes再喂feedparser，SSL/proxy完全由我们控制
        """
        retry_count = 2
        last_error = None
        max_items = max_per_source or source.max_per_fetch

        for attempt in range(retry_count + 1):
            try:
                req = urllib.request.Request(source.feed_url, headers=FETCH_HEADERS)
                with _opener.open(req, timeout=timeout_seconds) as resp:
                    raw_bytes = resp.read()

                # feedparser只做XML解析，不发网络请求
                feed = feedparser.parse(raw_bytes)

                if feed.bozo and not feed.entries:
                    # bozo但有条目仍可用，完全没条目才判失败
                    bozo_msg = str(feed.bozo_exception) if feed.bozo_exception else "unknown bozo error"
                    raise ValueError(f"Feed bozo error: {bozo_msg}")

                entries = feed.entries[:max_items]
                logger.info(f"[ingestion/fetch] {source.source_name}: 拉取 {len(entries)} 条")
                return (source, entries, None)

            except Exception as e:
                last_error = str(e)
                if attempt < retry_count:
                    time.sleep(1.5 * (attempt + 1))
                    logger.warning(
                        f"[ingestion/fetch] {source.source_name} 重试 {attempt+1}/{retry_count}: {e}"
                    )
                else:
                    logger.error(f"[ingestion/fetch] {source.source_name} 失败: {e}")

        return (source, [], last_error)

    logger.info(f"[ingestion] 开始并发拉取 {len(sources)} 个源（最大并发={max_workers}）...")
    t_start = time.time()

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="rss") as executor:
        future_map = {executor.submit(_fetch_http, s): s for s in sources}
        for future in as_completed(future_map):
            source_obj, entries, err = future.result()
            raw_feeds[source_obj.source_id] = (source_obj, entries, err)

    t_fetch = time.time() - t_start
    logger.info(f"[ingestion] 并发拉取完成，耗时 {t_fetch:.1f}s")

    # Phase 2: 顺序DB写入，SQLite单连接安全
    for source in sources:
        source_obj, entries, err = raw_feeds.get(source.source_id, (source, [], "fetch skipped"))

        src_result = {
            "source_id": source.source_id,
            "source_name": source.source_name,
            "fetched": len(entries),
            "saved": 0,
            "skipped_dup": 0,
            "status": "ok",
            "error": None,
        }

        if err:
            src_result["status"] = "error"
            src_result["error"] = err
            result.total_failed_sources += 1
            result.errors.append(f"{source.source_name}: {err}")
        elif entries:
            saved, skipped = _process_feed_entries(db=db, entries=entries, source=source)
            src_result["saved"] = saved
            src_result["skipped_dup"] = skipped
            logger.info(f"[ingestion/save] {source.source_name}: 新增={saved} 去重={skipped}")

        result.source_results.append(src_result)
        result.total_fetched += src_result["fetched"]
        result.total_saved += src_result["saved"]
        result.total_skipped_dup += src_result["skipped_dup"]

    # 决定数据状态
    if result.total_saved > 0:
        result.data_status = DATA_STATUS_LIVE
    elif result.total_fetched > 0:
        result.data_status = DATA_STATUS_STALE_SNAPSHOT  # 全是重复
    elif result.total_failed_sources == len(sources):
        result.data_status = DATA_STATUS_EMPTY
    else:
        result.data_status = DATA_STATUS_STALE_SNAPSHOT

    logger.info(
        f"[ingestion] 采集完成: "
        f"获取={result.total_fetched} 新增={result.total_saved} "
        f"去重跳过={result.total_skipped_dup} 失败源={result.total_failed_sources} "
        f"状态={result.data_status}"
    )
    return result


def _process_feed_entries(
    db: Session,
    entries: list,
    source: NewsSource,
) -> Tuple[int, int]:
    """处理feed条目，返回(saved, skipped_dup)"""
    saved = 0
    skipped = 0

    for entry in entries:
        try:
            title, body, url, published_at = _normalize_entry(entry)
            if not title or len(title.strip()) < 5:
                continue

            # 简单关键词过滤非IR内容
            if not _is_ir_relevant(title, body):
                continue

            dedupe_hash = compute_dedupe_hash(title, source.source_name)

            existing = db.query(RawNews).filter_by(dedupe_hash=dedupe_hash).first()
            if existing:
                skipped += 1
                continue

            region_tags = extract_region_tags(f"{title} {body}")
            raw_entities = simple_entity_extract(f"{title} {body}")

            news = RawNews(
                news_id=str(uuid.uuid4()),
                source_name=source.source_name,
                source_type=source.source_type,
                title=title.strip(),
                body=body[:3000],
                url=url,
                published_at=published_at,
                language=source.language,
                region_tags=region_tags,
                raw_entities=raw_entities,
                dedupe_hash=dedupe_hash,
                status="raw",
            )
            db.add(news)
            saved += 1

        except Exception as e:
            logger.warning(f"[ingestion] 处理条目失败: {e}")
            continue

    try:
        db.commit()
    except Exception as e:
        logger.error(f"[ingestion] 数据库提交失败: {e}")
        db.rollback()
        return 0, skipped

    return saved, skipped


def _normalize_entry(entry) -> Tuple[str, str, str, Optional[datetime]]:
    """规范化feedparser entry"""
    title = getattr(entry, "title", "") or ""

    # 正文：content > summary > description
    body = ""
    if hasattr(entry, "content") and entry.content:
        body = entry.content[0].get("value", "")
    elif hasattr(entry, "summary") and entry.summary:
        body = entry.summary
    elif hasattr(entry, "description") and entry.description:
        body = entry.description

    # 清HTML标签
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()

    url = getattr(entry, "link", "") or ""

    # 发布时间，多格式兼容
    published_at = None
    for attr in ["published_parsed", "updated_parsed", "created_parsed"]:
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                published_at = datetime(*parsed[:6], tzinfo=timezone.utc).replace(tzinfo=None)
                break
            except Exception:
                pass

    return title, body, url, published_at


def _is_ir_relevant(title: str, body: str) -> bool:
    """IR相关性过滤，宽松策略，宁可多收不漏"""
    combined = (title + " " + body[:300]).lower()

    exclude_keywords = [
        "celebrity", "fashion", "recipe", "cooking", "sports score",
        "box office", "album", "music chart", "reality tv", "gossip",
        "nfl", "nba", "premier league", "world cup goal", "wimbledon",
        "oscar", "grammy", "emmy",
    ]
    if any(kw in combined for kw in exclude_keywords):
        pass  # 不直接排除，由下面IR词决定

    ir_keywords = [
        "war", "warfare", "conflict", "military", "nuclear", "missile",
        "sanction", "troops", "soldiers", "army", "navy", "air force",
        "weapon", "arms", "attack", "strike", "bombardment", "ceasefire",
        "invasion", "occupation", "annexation", "offensive", "defense",
        "drone", "ballistic", "warship", "carrier", "fighter jet",
        "blockade", "siege", "hostage", "terrorism", "extremism",
        "insurgency", "rebel", "coup", "junta", "militia",
        "diplomat", "diplomacy", "ambassador", "embassy", "consul",
        "foreign minister", "secretary of state", "chancellor",
        "president", "prime minister", "premier", "minister",
        "government", "parliament", "congress", "senate",
        "treaty", "agreement", "accord", "pact", "deal",
        "alliance", "coalition", "partnership",
        "nato", "united nations", "un ", "security council",
        "eu ", "european union", "g7", "g20", "asean", "opec",
        "summit", "negotiat", "bilateral", "multilateral",
        "sanction", "embargo", "tariff", "trade war",
        "sovereignty", "territorial", "border dispute",
        "geopolit", "strategic", "intelligence", "espionage",
        "election", "referendum", "protest", "uprising",
        "tension", "crisis", "escalat", "de-escalat",
        "china", "chinese", "beijing", "pla", "ccp",
        "russia", "russian", "moscow", "kremlin", "putin",
        "ukraine", "ukrainian", "kyiv", "zelensky",
        "usa", "united states", "american", "washington", "pentagon",
        "white house", "state department",
        "iran", "iranian", "tehran", "irgc",
        "israel", "israeli", "hamas", "hezbollah", "netanyahu",
        "taiwan", "taiwanese", "strait",
        "north korea", "kim jong", "pyongyang",
        "south korea", "india", "pakistan", "kashmir",
        "saudi arabia", "riyadh", "mbs",
        "turkey", "erdogan", "ankara",
        "france", "macron", "germany", "uk", "britain",
        "syria", "iraq", "lebanon", "yemen", "afghanistan",
        "myanmar", "philippines", "south china sea",
        "oil", "gas", "energy", "pipeline", "lng",
        "semiconductor", "chip", "supply chain", "tech war",
        "cyber attack", "hacking", "espionage",
        "外交", "军事", "核", "制裁", "冲突", "战争", "谈判", "条约",
        "边境", "领土", "主权", "危机", "紧张", "升级", "停火",
        "总统", "总理", "外长", "国防", "联合国", "北约",
        "美国", "中国", "俄罗斯", "乌克兰", "以色列", "伊朗",
        "台湾", "朝鲜", "印度", "巴基斯坦",
    ]

    return any(kw in combined for kw in ir_keywords)


# --- 向后兼容旧接口 ---

def fetch_rss_news(db: Session, max_per_source: int = 20) -> List[Dict]:
    """兼容旧接口"""
    result = fetch_all_sources(db, max_per_source=max_per_source)
    saved_news = db.query(RawNews).filter_by(status="raw").order_by(
        RawNews.fetched_at.desc()
    ).limit(result.total_saved).all()
    return [
        {"news_id": n.news_id, "title": n.title, "source": n.source_name}
        for n in saved_news
    ]
