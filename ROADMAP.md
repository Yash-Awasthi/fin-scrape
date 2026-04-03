# 🗺️ Project Roadmap: FinIntelligence

> **[Back to README.md](README.md)**

This roadmap outlines the strategic direction and future enhancements for the FinIntelligence engine.

---

## 🏗️ Phase 1: High-Performance Ingestion (Next Steps)

### 🦎 Scrapling Integration
Migrate current BeautifulSoup-based scrapers to [Scrapling](https://github.com/D4Vinci/Scrapling), an adaptive, anti-bot bypass framework. 
- **Goal**: Zero-maintenance scraping with self-healing selectors.
- **Benefit**: Bypass Cloudflare/Turnstile and handle front-end structural changes automatically.

### 🌐 SERP API Integration
Incorporate Search Engine Results Page (SERP) results for proactive news discovery.
- **Sources**: Google Search, Bing, and DuckDuckGo via SerpApi or similar.
- **Benefit**: Detect "breaking news" that hasn't yet appeared on major finance portals.

### 🤖 Apify Actors
Offload heavy or distributed scraping tasks to [Apify](https://apify.com/).
- **Use Case**: Deep crawling of corporate press release IR portals or social media signals (X/Twitter).
- **Benefit**: Highly scalable and distributed ingestion without IP blocking.

---

## 🧠 Phase 2: Intelligence & Advanced Models

### 🐟 TinyFish AI
Integration of [TinyFish](https://github.com/TinyFish-AI) or similar lightweight local LLMs.
- **Goal**: Edge processing for sensitive data or initial "relevance" filtering without cloud API costs.
- **Benefit**: Reduced latency and offline capability for Tier-1 event filtering.

### 📈 Multi-Agent Orchestration
Evolve the current pipeline into a multi-agent "Council" (AI Council).
- **Agent 1 (Scout)**: Ingestion & URL Discovery.
- **Agent 2 (Analyst)**: Event Extraction & Entity Linking.
- **Agent 3 (Reviewer)**: Heuristic Cross-Check & Divergence Flagging.

---

## ⚙️ Phase 3: Automation & Ecosystem

### 🛡️ Autonomous News Hunting
Scheduled "Hunters" that monitor specific keywords or sectors 24/7.
- **Feature**: Real-time push notifications (Discord/Telegram/Slack) for high-impact (>0.85) signals.

### 💰 Automated Trading Signal Bridge
Integrate with trading platforms (Interactive Brokers, Alpaca, MetaTrader).
- **Goal**: One-click or fully automated trade execution based on high-confidence earnings or M&A signals.
- **Safety**: Human-in-the-loop mandatory for orders > $X.

---

## 📊 Summary of Planned Integrations

| Feature | Category | Purpose | Priority |
| :--- | :--- | :--- | :--- |
| **Scrapling** | Ingestion | Anti-bot bypass & Self-healing | **High** |
| **Apify** | Scalability | Distributed crawling | **Medium** |
| **SERP API** | Discovery | Proactive news surface | **Medium** |
| **TinyFish AI** | Models | Local/Edge processing | **Low** |
| **Trading APIs**| Ecosystem | Automated Execution | **Low** |

---

> [!TIP]
> We are committed to an open-source, modular ecosystem. If you'd like to contribute a new scraper or analysis model, please open a PR!
