-- One outcome per event, enforced by the database rather than by a read-then-write.
--
-- `server.accuracy.backtest` skipped already-scored events with `NOT EXISTS`, which is
-- only sound while exactly one worker runs. The deployment has two paths that can
-- overlap — the scheduled `worker.main --once` GitHub Action and the always-on worker's
-- hourly job — so two concurrent runs could both pass the check and double-score an
-- event, silently inflating the hit-rate denominator behind /api/accuracy.

-- Collapse any duplicates already stored, keeping the first outcome recorded for each
-- event. NULL event_ids never compare equal, so orphaned rows are left alone.
DELETE FROM accuracy_outcomes a
USING accuracy_outcomes b
WHERE a.event_id = b.event_id
  AND a.id > b.id;

-- Supersedes the non-unique idx_accuracy_event from 0001 (same column, weaker).
DROP INDEX IF EXISTS idx_accuracy_event;
CREATE UNIQUE INDEX IF NOT EXISTS idx_accuracy_event_unique
    ON accuracy_outcomes (event_id);

-- `queries.get_recent_predictions` joins the cache to events by event_id; the table
-- only had its cache_key primary key, so that join was a sequential scan.
CREATE INDEX IF NOT EXISTS idx_ai_cache_event ON ai_analysis_cache (event_id);
