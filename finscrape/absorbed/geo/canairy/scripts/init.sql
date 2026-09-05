-- Canairy Database Schema
-- Household Resilience Monitoring System

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Domains enum
CREATE TYPE domain_type AS ENUM (
    'economy',
    'jobs_labor',
    'rights_governance',
    'security_infrastructure',
    'oil_axis',
    'ai_window',
    'global_conflict',
    'domestic_control',
    'cult'
);

-- Alert level enum
CREATE TYPE alert_level AS ENUM ('green', 'amber', 'red', 'unknown');

-- Trend enum
CREATE TYPE trend_type AS ENUM ('up', 'down', 'stable');

-- Data source enum
CREATE TYPE data_source AS ENUM ('LIVE', 'MANUAL', 'MOCK', 'CACHED');

-- Indicators table (metadata about each indicator)
CREATE TABLE indicators (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    domain domain_type NOT NULL,
    unit VARCHAR(50),
    data_source_url TEXT,
    update_frequency VARCHAR(20) DEFAULT '60m',
    threshold_green DECIMAL(15, 4),
    threshold_amber DECIMAL(15, 4),
    threshold_red DECIMAL(15, 4),
    is_critical BOOLEAN DEFAULT FALSE,
    is_green_flag BOOLEAN DEFAULT FALSE,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for domain filtering
CREATE INDEX idx_indicators_domain ON indicators(domain);
CREATE INDEX idx_indicators_critical ON indicators(is_critical) WHERE is_critical = TRUE;

-- Indicator readings (historical values)
CREATE TABLE indicator_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_id VARCHAR(100) NOT NULL REFERENCES indicators(id) ON DELETE CASCADE,
    value DECIMAL(15, 4),
    level alert_level NOT NULL DEFAULT 'unknown',
    trend trend_type,
    source data_source NOT NULL DEFAULT 'LIVE',
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for time-series queries
CREATE INDEX idx_readings_indicator_time ON indicator_readings(indicator_id, recorded_at DESC);
CREATE INDEX idx_readings_level ON indicator_readings(level);
CREATE INDEX idx_readings_recorded_at ON indicator_readings(recorded_at DESC);

-- Partition readings by month for better performance (optional, uncomment if needed)
-- CREATE TABLE indicator_readings_y2024m01 PARTITION OF indicator_readings
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_id VARCHAR(100) REFERENCES indicators(id) ON DELETE SET NULL,
    level alert_level NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    triggered_value DECIMAL(15, 4),
    threshold_crossed DECIMAL(15, 4),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_indicator ON alerts(indicator_id);
CREATE INDEX idx_alerts_level ON alerts(level);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);

-- Phases table
CREATE TABLE phases (
    number INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    triggers TEXT[],
    actions TEXT[],
    color VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Current system state
CREATE TABLE system_state (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1), -- Singleton row
    current_phase INTEGER REFERENCES phases(number),
    hopi_score DECIMAL(5, 2),
    tighten_up_active BOOLEAN DEFAULT FALSE,
    last_calculation TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User settings
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_identifier VARCHAR(255) UNIQUE, -- Could be email, device ID, etc.
    notification_email VARCHAR(255),
    notification_phone VARCHAR(50),
    email_alerts_enabled BOOLEAN DEFAULT TRUE,
    sms_alerts_enabled BOOLEAN DEFAULT FALSE,
    push_alerts_enabled BOOLEAN DEFAULT TRUE,
    alert_threshold alert_level DEFAULT 'amber',
    refresh_interval INTEGER DEFAULT 60, -- seconds
    theme VARCHAR(20) DEFAULT 'dark',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_settings_identifier ON user_settings(user_identifier);

-- HOPI score history
CREATE TABLE hopi_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    score DECIMAL(5, 2) NOT NULL,
    phase INTEGER NOT NULL,
    confidence DECIMAL(5, 2),
    domain_scores JSONB NOT NULL,
    red_count INTEGER DEFAULT 0,
    amber_count INTEGER DEFAULT 0,
    green_count INTEGER DEFAULT 0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hopi_history_recorded ON hopi_history(recorded_at DESC);

-- Error log for debugging
CREATE TABLE error_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_type VARCHAR(100),
    message TEXT,
    stack_trace TEXT,
    url TEXT,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_error_log_created ON error_log(created_at DESC);
CREATE INDEX idx_error_log_type ON error_log(error_type);

-- Insert default phases
INSERT INTO phases (number, name, description, triggers, actions, color) VALUES
(0, 'Foundations', 'Build baseline resilience capabilities', ARRAY['default'],
   ARRAY['CPR/First Aid training', 'Password manager setup', 'Resilience notebook', 'Baseline fitness'], '#22c55e'),
(1, '72-hour bin', 'Basic emergency supplies', ARRAY['normal/green overall'],
   ARRAY['48× water + food kit', 'NOAA radio', '$500 cash', 'CO alarm + extinguisher'], '#22c55e'),
(2, 'Digital & comms', 'Communication redundancy', ARRAY['any 1 amber in econ/rights/security'],
   ARRAY['Password manager done', 'Power banks', 'GMRS handhelds', 'PACE card'], '#eab308'),
(3, 'Air, health, mobile', 'Enhanced preparation', ARRAY['1 red anywhere or 2 ambers sustained 7 days'],
   ARRAY['HEPA on', 'N95 cache', 'inReach Mini', 'Weekly comms drill'], '#f97316'),
(4, 'Dry-basement / perimeter', 'Physical security', ARRAY['ACLED or CYBER red or 2 total reds'],
   ARRAY['Avoid protest zones', 'Family curfew', 'Top off fuel', 'Door security'], '#f97316'),
(5, 'Oil-tank → generator prep', 'Power independence prep', ARRAY['OIL red or MARKET ≥30 bp'],
   ARRAY['Dose PRI-D', 'Fuel filter', 'Generator prep', 'Charge routine'], '#ef4444'),
(6, 'Shelter nook build', 'Safe room preparation', ARRAY['2+ reds sustained ≥48h'],
   ARRAY['Tyvek clean-out', 'Storage shelves', 'Security cameras', 'Roles matrix'], '#ef4444'),
(7, 'Harden + genset live', 'Full power backup', ARRAY['Guard activation or court chaos + 2 reds'],
   ARRAY['18-22 kW diesel + ATS', 'Surge protection', 'Power budget', 'Steel/plywood wrap'], '#dc2626'),
(8, 'Water & circuits', 'Water independence', ARRAY['3+ grid outages/quarter'],
   ARRAY['Rainwater totes + pump', 'Shelter circuits to ATS', 'Offline resources'], '#dc2626'),
(9, 'Optional safe-room', 'Maximum protection', ARRAY['only if needed'],
   ARRAY['FEMA/ICC-500 room', 'Not required for most'], '#7c3aed');

-- Initialize system state
INSERT INTO system_state (current_phase, hopi_score, tighten_up_active)
VALUES (0, 0.0, FALSE);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_indicators_updated_at BEFORE UPDATE ON indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_state_updated_at BEFORE UPDATE ON system_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for latest readings per indicator
CREATE VIEW latest_readings AS
SELECT DISTINCT ON (indicator_id)
    ir.*,
    i.name as indicator_name,
    i.domain,
    i.is_critical
FROM indicator_readings ir
JOIN indicators i ON ir.indicator_id = i.id
ORDER BY indicator_id, recorded_at DESC;

-- View for current system status
CREATE VIEW system_status AS
SELECT
    ss.current_phase,
    p.name as phase_name,
    ss.hopi_score,
    ss.tighten_up_active,
    ss.last_calculation,
    (SELECT COUNT(*) FROM latest_readings WHERE level = 'red') as red_count,
    (SELECT COUNT(*) FROM latest_readings WHERE level = 'amber') as amber_count,
    (SELECT COUNT(*) FROM latest_readings WHERE level = 'green') as green_count,
    (SELECT COUNT(*) FROM alerts WHERE NOT acknowledged AND created_at > NOW() - INTERVAL '24 hours') as active_alerts
FROM system_state ss
LEFT JOIN phases p ON ss.current_phase = p.number;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO canairy;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO canairy;
