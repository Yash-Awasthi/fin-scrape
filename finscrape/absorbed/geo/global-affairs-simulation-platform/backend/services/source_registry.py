"""新闻源注册表 - RSS/Atom源管理，启用/禁用/采集间隔"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NewsSource:
    source_id: str
    source_name: str
    source_type: str          # rss / atom / api
    base_url: str
    feed_url: str
    region: str               # Global / Middle East / East Asia / Europe / etc.
    language: str             # en / zh / ar / fr / etc.
    enabled: bool = True
    polling_interval_minutes: int = 30
    max_per_fetch: int = 25
    parser_type: str = "feedparser"   # feedparser / custom
    tags: List[str] = field(default_factory=list)
    description: str = ""


# --- 已注册新闻源（20个，代理由rss_ingestion_service自动配置）---
REGISTERED_SOURCES: List[NewsSource] = [

    # --- 直连可用 ---

    NewsSource(
        source_id="france24_en",
        source_name="France 24 English",
        source_type="rss",
        base_url="https://www.france24.com",
        feed_url="https://www.france24.com/en/rss",
        region="Europe",
        language="en",
        enabled=True,
        polling_interval_minutes=20,
        max_per_fetch=25,
        tags=["global", "europe", "france_perspective"],
        description="法国24小时英语新闻 ✅",
    ),
    NewsSource(
        source_id="kyivpost",
        source_name="Kyiv Post",
        source_type="rss",
        base_url="https://www.kyivpost.com",
        feed_url="https://www.kyivpost.com/feed",
        region="Europe",
        language="en",
        enabled=True,
        polling_interval_minutes=25,
        max_per_fetch=30,
        tags=["europe", "ukraine", "russia"],
        description="基辅邮报（乌克兰/俄罗斯局势）✅",
    ),
    NewsSource(
        source_id="politico_world",
        source_name="Politico",
        source_type="rss",
        base_url="https://www.politico.com",
        feed_url="https://rss.politico.com/politics-news.xml",
        region="Americas",
        language="en",
        enabled=True,
        polling_interval_minutes=25,
        max_per_fetch=25,
        tags=["americas", "us_politics", "diplomacy"],
        description="Politico 政治新闻 ✅",
    ),
    NewsSource(
        source_id="cgtn_world",
        source_name="CGTN World",
        source_type="rss",
        base_url="https://www.cgtn.com",
        feed_url="https://www.cgtn.com/subscribe/rss/section/world.xml",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=25,
        max_per_fetch=30,
        tags=["global", "china_perspective", "east_asia"],
        description="中国国际电视台英文世界新闻 ✅",
    ),
    NewsSource(
        source_id="straitstimes_world",
        source_name="The Straits Times - World",
        source_type="rss",
        base_url="https://www.straitstimes.com",
        feed_url="https://www.straitstimes.com/news/world/rss.xml",
        region="Southeast Asia",
        language="en",
        enabled=True,
        polling_interval_minutes=30,
        max_per_fetch=25,
        tags=["southeast_asia", "asia_perspective", "global"],
        description="新加坡海峡时报国际新闻 ✅",
    ),
    NewsSource(
        source_id="hindustantimes_world",
        source_name="Hindustan Times - World",
        source_type="rss",
        base_url="https://www.hindustantimes.com",
        feed_url="https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
        region="South Asia",
        language="en",
        enabled=True,
        polling_interval_minutes=30,
        max_per_fetch=20,
        tags=["south_asia", "india", "global"],
        description="印度斯坦时报国际新闻 ✅",
    ),
    NewsSource(
        source_id="channelnewsasia",
        source_name="Channel News Asia",
        source_type="rss",
        base_url="https://www.channelnewsasia.com",
        feed_url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
        region="Southeast Asia",
        language="en",
        enabled=True,
        polling_interval_minutes=25,
        max_per_fetch=20,
        tags=["southeast_asia", "asia", "global"],
        description="新加坡第八频道英文新闻 ✅",
    ),

    # --- 需代理 ---

    NewsSource(
        source_id="bbc_world",
        source_name="BBC World News",
        source_type="rss",
        base_url="https://www.bbc.com",
        feed_url="http://feeds.bbci.co.uk/news/world/rss.xml",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=20,
        max_per_fetch=30,
        tags=["mainstream", "global"],
        description="BBC 国际新闻 RSS 🔒",
    ),
    NewsSource(
        source_id="guardian_world",
        source_name="The Guardian - World",
        source_type="rss",
        base_url="https://www.theguardian.com",
        feed_url="https://www.theguardian.com/world/rss",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=20,
        max_per_fetch=30,
        tags=["mainstream", "global", "breaking"],
        description="卫报国际新闻 🔒",
    ),
    NewsSource(
        source_id="dw_world",
        source_name="Deutsche Welle - World",
        source_type="rss",
        base_url="https://www.dw.com",
        feed_url="https://rss.dw.com/rdf/rss-en-world",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=25,
        max_per_fetch=25,
        tags=["global", "europe_perspective"],
        description="德国之声英文国际新闻 🔒",
    ),
    NewsSource(
        source_id="aljazeera_all",
        source_name="Al Jazeera English",
        source_type="rss",
        base_url="https://www.aljazeera.com",
        feed_url="https://www.aljazeera.com/xml/rss/all.xml",
        region="Middle East",
        language="en",
        enabled=True,
        polling_interval_minutes=25,
        max_per_fetch=25,
        tags=["middle_east", "global", "alternative"],
        description="半岛电视台英文 RSS 🔒",
    ),
    NewsSource(
        source_id="rfi_english",
        source_name="RFI English",
        source_type="rss",
        base_url="https://www.rfi.fr",
        feed_url="https://www.rfi.fr/en/rss",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=30,
        max_per_fetch=20,
        tags=["global", "africa", "france_perspective"],
        description="法国国际广播英文 🔒",
    ),
    NewsSource(
        source_id="nhk_world",
        source_name="NHK World - Asia Pacific",
        source_type="rss",
        base_url="https://www3.nhk.or.jp",
        feed_url="https://www3.nhk.or.jp/rss/news/cat6.xml",
        region="East Asia",
        language="en",
        enabled=True,
        polling_interval_minutes=30,
        max_per_fetch=20,
        tags=["east_asia", "japan_perspective", "asia"],
        description="日本NHK国际频道英文新闻 🔒",
    ),
    NewsSource(
        source_id="the_diplomat",
        source_name="The Diplomat",
        source_type="rss",
        base_url="https://thediplomat.com",
        feed_url="https://thediplomat.com/feed/",
        region="East Asia",
        language="en",
        enabled=True,
        polling_interval_minutes=60,
        max_per_fetch=15,
        tags=["east_asia", "asia", "ir_specialty", "geopolitics"],
        description="外交家杂志（专注亚太IR）🔒",
    ),
    NewsSource(
        source_id="war_on_rocks",
        source_name="War on the Rocks",
        source_type="rss",
        base_url="https://warontherocks.com",
        feed_url="https://warontherocks.com/feed/",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=60,
        max_per_fetch=10,
        tags=["security", "military", "strategy", "ir_specialty"],
        description="战略与安全政策专业媒体 🔒",
    ),
    NewsSource(
        source_id="worldpoliticsreview",
        source_name="World Politics Review",
        source_type="rss",
        base_url="https://www.worldpoliticsreview.com",
        feed_url="https://www.worldpoliticsreview.com/rss/",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=60,
        max_per_fetch=10,
        tags=["global", "ir_specialty", "analysis"],
        description="世界政治评论（深度IR分析）🔒",
    ),
    NewsSource(
        source_id="middleeasteye",
        source_name="Middle East Eye",
        source_type="rss",
        base_url="https://www.middleeasteye.net",
        feed_url="https://www.middleeasteye.net/rss",
        region="Middle East",
        language="en",
        enabled=True,
        polling_interval_minutes=30,
        max_per_fetch=20,
        tags=["middle_east"],
        description="中东之眼（中东局势独立报道）🔒",
    ),
    NewsSource(
        source_id="scmp_world",
        source_name="South China Morning Post",
        source_type="rss",
        base_url="https://www.scmp.com",
        feed_url="https://www.scmp.com/rss/2/feed",
        region="East Asia",
        language="en",
        enabled=True,
        polling_interval_minutes=30,
        max_per_fetch=15,
        tags=["east_asia", "china", "asia_perspective"],
        description="南华早报国际版 🔒",
    ),
    NewsSource(
        source_id="bbc_uk_politics",
        source_name="BBC UK Politics",
        source_type="rss",
        base_url="https://www.bbc.com",
        feed_url="http://feeds.bbci.co.uk/news/politics/rss.xml",
        region="Europe",
        language="en",
        enabled=True,
        polling_interval_minutes=30,
        max_per_fetch=15,
        tags=["europe", "uk", "politics"],
        description="BBC 英国政治新闻 🔒",
    ),
    NewsSource(
        source_id="foreignpolicy",
        source_name="Foreign Policy",
        source_type="rss",
        base_url="https://foreignpolicy.com",
        feed_url="https://foreignpolicy.com/feed/",
        region="Global",
        language="en",
        enabled=True,
        polling_interval_minutes=60,
        max_per_fetch=10,
        tags=["global", "ir_specialty", "us_perspective", "analysis"],
        description="外交政策杂志（顶级IR专业媒体）🔒",
    ),
]


def get_enabled_sources() -> List[NewsSource]:
    """获取所有启用的新闻源"""
    return [s for s in REGISTERED_SOURCES if s.enabled]


def get_source_by_id(source_id: str) -> Optional[NewsSource]:
    """根据ID获取新闻源"""
    for source in REGISTERED_SOURCES:
        if source.source_id == source_id:
            return source
    return None


def list_source_info() -> List[dict]:
    """所有新闻源的可序列化信息"""
    return [
        {
            "source_id": s.source_id,
            "source_name": s.source_name,
            "source_type": s.source_type,
            "region": s.region,
            "language": s.language,
            "enabled": s.enabled,
            "polling_interval_minutes": s.polling_interval_minutes,
            "max_per_fetch": s.max_per_fetch,
            "tags": s.tags,
            "description": s.description,
            "feed_url": s.feed_url,
        }
        for s in REGISTERED_SOURCES
    ]
