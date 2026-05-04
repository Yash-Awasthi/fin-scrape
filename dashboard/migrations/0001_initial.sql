-- Initial schema for FinScrape D1 database
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'other',
    tickers TEXT NOT NULL DEFAULT '[]',
    impact_direction TEXT NOT NULL DEFAULT 'neutral',
    signal_score INTEGER NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0.5,
    verdict TEXT NOT NULL DEFAULT 'OBSERVE',
    heuristic_impact REAL NOT NULL DEFAULT 0.0,
    divergence_flag INTEGER NOT NULL DEFAULT 0,
    sources TEXT NOT NULL DEFAULT '[]',
    articles TEXT NOT NULL DEFAULT '[]',
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    reasoning TEXT NOT NULL DEFAULT '',
    magnitude TEXT NOT NULL DEFAULT '',
    novelty TEXT NOT NULL DEFAULT '',
    actionability TEXT NOT NULL DEFAULT '',
    sector_impact TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_events_verdict ON events(verdict);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);

CREATE TABLE IF NOT EXISTS telegram_chats (
    chat_id TEXT PRIMARY KEY,
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    filters TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS portfolio_positions (
    ticker TEXT PRIMARY KEY,
    shares REAL NOT NULL DEFAULT 0,
    avg_cost REAL NOT NULL DEFAULT 0,
    current_price REAL NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS portfolio_watchlists (
    name TEXT PRIMARY KEY,
    tickers TEXT NOT NULL DEFAULT '[]',
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ai_analysis_cache (
    event_id INTEGER PRIMARY KEY,
    summary TEXT NOT NULL DEFAULT '',
    ticker_impacts TEXT NOT NULL DEFAULT '[]',
    verdict_reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
