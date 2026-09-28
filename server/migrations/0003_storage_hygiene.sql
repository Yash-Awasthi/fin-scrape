-- Storage hygiene: indexes for the queries the API actually runs, one row per
-- correlation signal, and range checks on the scored columns.

-- The worker re-emits every live signal each cycle, and each emission was a new
-- row: one signal became one row per 15 minutes forever. Keep the newest per key,
-- then let the unique index turn re-emission into an upsert.
DELETE FROM correlations a
USING correlations b
WHERE a.dedupe_key = b.dedupe_key
  AND (a.detected_at, a.id) < (b.detected_at, b.id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_correlations_dedupe ON correlations (dedupe_key);

-- URLs the worker has already judged, so a feed item is sent to the LLM once
-- rather than once per cycle. Keyed on the canonical URL (server.ingest).
CREATE TABLE IF NOT EXISTS visited_urls (
    url         TEXT        PRIMARY KEY,
    source      TEXT        NOT NULL,
    visited_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_visited_urls_at ON visited_urls (visited_at);

-- /api/sectors groups and filters on sector_impact, skipping blanks.
CREATE INDEX IF NOT EXISTS idx_events_sector
    ON events (sector_impact) WHERE sector_impact <> '';

-- The feed filters by verdict and orders by time in one query.
CREATE INDEX IF NOT EXISTS idx_events_verdict_ts ON events (verdict, timestamp DESC);

-- Retention prunes these by age.
CREATE INDEX IF NOT EXISTS idx_scrape_runs_started ON scrape_runs (started_at);
CREATE INDEX IF NOT EXISTS idx_ai_cache_created ON ai_analysis_cache (created_at);

-- NOT VALID: enforced for new writes without failing on any legacy row.
ALTER TABLE events DROP CONSTRAINT IF EXISTS events_signal_score_range;
ALTER TABLE events ADD CONSTRAINT events_signal_score_range
    CHECK (signal_score BETWEEN -5 AND 5) NOT VALID;
ALTER TABLE events DROP CONSTRAINT IF EXISTS events_confidence_range;
ALTER TABLE events ADD CONSTRAINT events_confidence_range
    CHECK (confidence BETWEEN 0 AND 1) NOT VALID;
