-- AutoGen Financial Analysis System Database Initialization
-- This script sets up the initial database structure and sample data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analysis_tasks table
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    symbols TEXT[],  -- Array of stock symbols
    parameters JSONB,
    result JSONB,
    error_message TEXT,
    progress DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create financial_data table
CREATE TABLE IF NOT EXISTS financial_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL,  -- 'income_statement', 'balance_sheet', 'cash_flow', 'market_data'
    period VARCHAR(20) NOT NULL,     -- 'annual', 'quarterly'
    year INTEGER,
    quarter INTEGER,
    data JSONB NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, data_type, period, year, quarter)
);

-- Create market_data table
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(15,4),
    high_price DECIMAL(15,4),
    low_price DECIMAL(15,4),
    close_price DECIMAL(15,4),
    volume BIGINT,
    adjusted_close DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES analysis_tasks(id),
    result_type VARCHAR(50) NOT NULL,  -- 'financial_metrics', 'risk_metrics', 'portfolio_analysis'
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id ON analysis_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_created_at ON analysis_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_financial_data_symbol ON financial_data(symbol);
CREATE INDEX IF NOT EXISTS idx_financial_data_type ON financial_data(data_type);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date ON market_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_market_data_date ON market_data(date);

-- Create default admin user (password: admin123 - should be changed)
INSERT INTO users (username, email, password_hash) VALUES
('admin', 'admin@autogen-financial.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6')
ON CONFLICT (email) DO NOTHING;

-- Create sample analysis task
INSERT INTO analysis_tasks (task_id, user_id, task_type, status, symbols, parameters) VALUES
('sample-task-001',
 (SELECT id FROM users WHERE username = 'admin'),
 'comprehensive',
 'completed',
 ARRAY['AAPL', 'MSFT', 'GOOG'],
 '{"analysis_depth": "detailed", "include_risk_analysis": true, "time_period": "5y"}'
)
ON CONFLICT (task_id) DO NOTHING;

-- Create sample financial data for AAPL
INSERT INTO financial_data (symbol, data_type, period, year, data, source) VALUES
('AAPL', 'market_data', 'annual', 2023,
 '{"market_cap": 2950000000000, "pe_ratio": 29.5, "pb_ratio": 45.2, "dividend_yield": 0.0055, "beta": 1.2}',
 'yahoo_finance'),
('AAPL', 'income_statement', 'annual', 2023,
 '{"revenue": 383285000000, "net_income": 96995000000, "gross_profit": 170782000000, "operating_income": 114301000000}',
 'yahoo_finance'),
('AAPL', 'balance_sheet', 'annual', 2023,
 '{"total_assets": 352755000000, "total_equity": 62146000000, "total_debt": 124717000000, "cash_and_equivalents": 29965000000}',
 'yahoo_finance')
ON CONFLICT (symbol, data_type, period, year) DO NOTHING;

-- Create sample market data
INSERT INTO market_data (symbol, date, open_price, high_price, low_price, close_price, volume, adjusted_close) VALUES
('AAPL', '2023-12-29', 192.53, 193.85, 191.23, 192.30, 58440000, 192.30),
('AAPL', '2023-12-28', 193.45, 194.12, 192.10, 192.75, 62300000, 192.75),
('AAPL', '2023-12-27', 194.25, 195.30, 192.85, 193.60, 45800000, 193.60),
('MSFT', '2023-12-29', 374.51, 376.85, 373.20, 375.45, 28500000, 375.45),
('MSFT', '2023-12-28', 373.25, 375.60, 372.10, 374.80, 31200000, 374.80),
('GOOG', '2023-12-29', 139.45, 140.85, 138.90, 139.69, 18500000, 139.69),
('GOOG', '2023-12-28', 138.90, 140.20, 138.50, 139.45, 19800000, 139.45)
ON CONFLICT (symbol, date) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financial_data_updated_at BEFORE UPDATE ON financial_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for active analysis tasks
CREATE OR REPLACE VIEW active_analysis_tasks AS
SELECT
    t.id,
    t.task_id,
    t.task_type,
    t.status,
    t.symbols,
    t.progress,
    t.created_at,
    t.started_at,
    u.username as created_by
FROM analysis_tasks t
LEFT JOIN users u ON t.user_id = u.id
WHERE t.status IN ('pending', 'running');

-- Create view for financial summary
CREATE OR REPLACE VIEW financial_summary AS
SELECT
    symbol,
    data_type,
    year,
    COUNT(*) as record_count,
    MAX(created_at) as last_updated
FROM financial_data
GROUP BY symbol, data_type, year;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO CURRENT_USER;

-- Database initialization completed
SELECT 'Database initialization completed successfully' as status;