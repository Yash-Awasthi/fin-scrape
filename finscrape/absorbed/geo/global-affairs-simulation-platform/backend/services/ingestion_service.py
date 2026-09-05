"""
ingestion_service - 新闻采集服务
支持 RSS 源采集 + Mock 数据回退
"""
import uuid
import feedparser
import re
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.orm import Session

from backend.models.raw_news import RawNews
from backend.services._ingestion_utils import compute_dedupe_hash, extract_region_tags, simple_entity_extract


DEFAULT_RSS_FEEDS = [
    {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "region": "Global"},
    {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/worldNews", "region": "Global"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "region": "Middle East"},
    {"name": "Reuters Politics", "url": "https://feeds.reuters.com/reuters/politicsNews", "region": "Global"},
    {"name": "AP News", "url": "https://rsshub.app/apnews/topics/ap-top-news", "region": "Global"},
]


def fetch_rss_news(db: Session, max_per_source: int = 20) -> List[Dict]:
    """从 RSS 源获取新闻，存入数据库"""
    collected = []

    for feed_info in DEFAULT_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            count = 0
            for entry in feed.entries[:max_per_source]:
                title = getattr(entry, "title", "").strip()
                body = getattr(entry, "summary", "") or getattr(entry, "description", "")
                # 去HTML标签
                body = re.sub(r"<[^>]+>", "", body)
                url = getattr(entry, "link", "")

                # 解析发布时间
                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                if not title:
                    continue

                dedupe_hash = compute_dedupe_hash(title, feed_info["name"])

                # 去重检查
                existing = db.query(RawNews).filter_by(dedupe_hash=dedupe_hash).first()
                if existing:
                    continue

                region_tags = extract_region_tags(f"{title} {body}")
                raw_entities = simple_entity_extract(f"{title} {body}")

                news = RawNews(
                    news_id=str(uuid.uuid4()),
                    source_name=feed_info["name"],
                    source_type="rss",
                    title=title,
                    body=body[:2000],  # 截断过长内容
                    url=url,
                    published_at=published_at,
                    language="en",
                    region_tags=region_tags,
                    raw_entities=raw_entities,
                    dedupe_hash=dedupe_hash,
                    status="raw",
                )
                db.add(news)
                collected.append({
                    "news_id": news.news_id,
                    "title": title,
                    "source": feed_info["name"],
                })
                count += 1

            db.commit()
            print(f"[ingestion] {feed_info['name']}: 新增 {count} 条")

        except Exception as e:
            print(f"[ingestion] {feed_info['name']} 采集失败: {e}")
            db.rollback()

    return collected


def get_mock_news(db: Session) -> List[Dict]:
    """Mock数据，RSS不可用时用"""
    mock_articles = [
        {
            "title": "Iran Advances Nuclear Enrichment Despite US Warnings",
            "body": "Iran has accelerated uranium enrichment at Natanz facility to 60%, drawing sharp condemnation from Washington. US officials warn of 'serious consequences' while Iran insists the program is for peaceful purposes.",
            "source_name": "MOCK_Reuters",
            "region": ["Middle East"],
            "entities": {"countries": ["Iran", "USA", "Israel"], "persons": [], "organizations": ["IAEA"], "locations": ["Natanz"]},
        },
        {
            "title": "IAEA Reports Reduced Access to Iranian Nuclear Sites",
            "body": "The International Atomic Energy Agency says Iran has denied inspectors access to two key surveillance cameras at nuclear facilities, raising concerns about monitoring gaps in the nuclear deal.",
            "source_name": "MOCK_BBC",
            "region": ["Middle East"],
            "entities": {"countries": ["Iran"], "persons": [], "organizations": ["IAEA", "UN"], "locations": ["Tehran"]},
        },
        {
            "title": "US Congress Pushes New Iran Sanctions Package",
            "body": "Bipartisan legislation targets Iran's oil exports and Revolutionary Guards financial networks. The package would impose secondary sanctions on countries purchasing Iranian crude.",
            "source_name": "MOCK_AP",
            "region": ["Middle East", "Americas"],
            "entities": {"countries": ["USA", "Iran"], "persons": [], "organizations": ["US Congress", "IRGC"], "locations": []},
        },
        {
            "title": "China-Taiwan Military Tensions Escalate Over Strait Incursions",
            "body": "People's Liberation Army aircraft crossed the median line of the Taiwan Strait 47 times this month, a record high. Taiwan's defense ministry has scrambled jets in response.",
            "source_name": "MOCK_Reuters",
            "region": ["East Asia"],
            "entities": {"countries": ["China", "Taiwan", "USA"], "persons": [], "organizations": ["PLA"], "locations": ["Taiwan Strait"]},
        },
        {
            "title": "US Carrier Strike Group Deploys to South China Sea",
            "body": "USS Ronald Reagan and its carrier strike group has entered the South China Sea in what the Pentagon calls a 'routine freedom of navigation operation.' China's foreign ministry called the deployment 'provocative.'",
            "source_name": "MOCK_BBC",
            "region": ["East Asia"],
            "entities": {"countries": ["USA", "China"], "persons": [], "organizations": ["Pentagon", "PLA Navy"], "locations": ["South China Sea"]},
        },
        {
            "title": "Taiwan Announces Record Defense Budget Amid China Tensions",
            "body": "Taiwan's government announced a 15% increase in defense spending, the largest in two decades, focused on asymmetric warfare capabilities and air defense systems.",
            "source_name": "MOCK_AP",
            "region": ["East Asia"],
            "entities": {"countries": ["Taiwan", "China", "USA"], "persons": [], "organizations": ["Taiwan MND"], "locations": []},
        },
        {
            "title": "Ukraine Front Lines Stabilize as Winter Sets In",
            "body": "Military analysts report reduced ground activity along the 1,000km front as freezing conditions make offensive operations difficult. Both sides are reinforcing positions and accumulating supplies.",
            "source_name": "MOCK_Reuters",
            "region": ["Europe"],
            "entities": {"countries": ["Ukraine", "Russia"], "persons": [], "organizations": ["NATO"], "locations": ["Zaporizhzhia", "Kherson"]},
        },
        {
            "title": "EU Approves 14th Sanctions Package Against Russia",
            "body": "European Union member states unanimously approved new sanctions targeting Russia's shadow fleet, circumvention networks, and dual-use technology exports.",
            "source_name": "MOCK_BBC",
            "region": ["Europe"],
            "entities": {"countries": ["Russia", "USA"], "persons": [], "organizations": ["EU", "NATO"], "locations": []},
        },
        {
            "title": "North Korea Tests New Hypersonic Missile System",
            "body": "North Korea conducted a test of what state media called a 'Hwasong-16B' hypersonic glide vehicle, capable of evading missile defense systems. South Korea and Japan called emergency security consultations.",
            "source_name": "MOCK_AP",
            "region": ["East Asia"],
            "entities": {"countries": ["North Korea", "South Korea", "Japan", "USA"], "persons": ["Kim Jong-un"], "organizations": [], "locations": []},
        },
        {
            "title": "Saudi Arabia and Iran Resume Diplomatic Relations at Ambassadorial Level",
            "body": "In a significant regional development, Saudi Arabia and Iran have exchanged ambassadors for the first time in seven years, following Chinese-mediated rapprochement. Analysts note implications for Yemen conflict and regional stability.",
            "source_name": "MOCK_Reuters",
            "region": ["Middle East"],
            "entities": {"countries": ["Saudi Arabia", "Iran", "China", "Yemen"], "persons": [], "organizations": [], "locations": ["Riyadh", "Tehran"]},
        },
    ]

    collected = []
    for article in mock_articles:
        dedupe_hash = compute_dedupe_hash(article["title"], article["source_name"])
        existing = db.query(RawNews).filter_by(dedupe_hash=dedupe_hash).first()
        if existing:
            collected.append({"news_id": existing.news_id, "title": existing.title, "source": existing.source_name})
            continue

        news = RawNews(
            news_id=str(uuid.uuid4()),
            source_name=article["source_name"],
            source_type="mock",
            title=article["title"],
            body=article["body"],
            url="",
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
            language="en",
            region_tags=article["region"],
            raw_entities=article["entities"],
            dedupe_hash=dedupe_hash,
            status="raw",
        )
        db.add(news)
        collected.append({"news_id": news.news_id, "title": article["title"], "source": article["source_name"]})

    db.commit()
    return collected
