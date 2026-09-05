package backtest

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"auto-trader-ahh/exchange"
	"auto-trader-ahh/mcp"
)

// Manager manages multiple backtest runs
type Manager struct {
	runners  map[string]*Runner
	metadata map[string]*RunMetadata
	cancels  map[string]context.CancelFunc
	client   mcp.AIClient
	exchange *exchange.BinanceClient
	mu       sync.RWMutex
}

// NewManager creates a new backtest manager
func NewManager(client mcp.AIClient, exch *exchange.BinanceClient) *Manager {
	return &Manager{
		runners:  make(map[string]*Runner),
		metadata: make(map[string]*RunMetadata),
		cancels:  make(map[string]context.CancelFunc),
		client:   client,
		exchange: exch,
	}
}

// Start starts a new backtest run
func (m *Manager) Start(ctx context.Context, cfg *Config) (string, error) {
	if cfg.RunID == "" {
		cfg.RunID = fmt.Sprintf("bt_%d", time.Now().UnixNano())
	}

	// Default timeframe if not set
	if cfg.DecisionTimeframe == "" {
		cfg.DecisionTimeframe = "5m"
	}

	m.mu.Lock()
	if _, exists := m.runners[cfg.RunID]; exists {
		m.mu.Unlock()
		return "", fmt.Errorf("backtest %s already exists", cfg.RunID)
	}

	runner := NewRunner(cfg, m.client)
	m.runners[cfg.RunID] = runner
	m.metadata[cfg.RunID] = runner.GetMetadata()
	m.mu.Unlock()

	// Start in background
	go func() {
		runCtx, cancel := context.WithCancel(ctx)
		m.mu.Lock()
		m.cancels[cfg.RunID] = cancel
		m.mu.Unlock()

		// Fetch klines from Binance if exchange client is available
		if m.exchange != nil {
			for _, symbol := range cfg.Symbols {
				exchKlines, err := m.exchange.GetHistoricalKlines(runCtx, symbol, cfg.DecisionTimeframe, cfg.StartTS, cfg.EndTS)
				if err != nil {
					log.Printf("Backtest %s: failed to fetch klines for %s: %v\n", cfg.RunID, symbol, err)
					continue
				}
				// Convert exchange.Kline to backtest.Kline
				klines := make([]Kline, len(exchKlines))
				for i, k := range exchKlines {
					klines[i] = Kline{
						OpenTime:  k.OpenTime,
						Open:      k.Open,
						High:      k.High,
						Low:       k.Low,
						Close:     k.Close,
						Volume:    k.Volume,
						CloseTime: k.CloseTime,
					}
				}
				runner.LoadKlines(symbol, klines)
				log.Printf("Backtest %s: loaded %d klines for %s\n", cfg.RunID, len(klines), symbol)
			}
		}

		if err := runner.Start(runCtx); err != nil {
			log.Printf("Backtest %s failed: %v\n", cfg.RunID, err)
		}

		// Update metadata
		m.mu.Lock()
		m.metadata[cfg.RunID] = runner.GetMetadata()
		m.mu.Unlock()
	}()

	return cfg.RunID, nil
}

// Stop stops a running backtest
func (m *Manager) Stop(runID string) error {
	m.mu.RLock()
	cancel, exists := m.cancels[runID]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("backtest %s not found", runID)
	}

	cancel()
	return nil
}

// GetStatus returns the status of a backtest
func (m *Manager) GetStatus(runID string) (*RunMetadata, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	runner, exists := m.runners[runID]
	if !exists {
		return nil, fmt.Errorf("backtest %s not found", runID)
	}

	return runner.GetMetadata(), nil
}

// GetMetrics returns the metrics of a backtest
func (m *Manager) GetMetrics(runID string) (*Metrics, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	runner, exists := m.runners[runID]
	if !exists {
		return nil, fmt.Errorf("backtest %s not found", runID)
	}

	return runner.GetMetrics(), nil
}

// GetEquityCurve returns the equity curve of a backtest
func (m *Manager) GetEquityCurve(runID string) ([]EquityPoint, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	runner, exists := m.runners[runID]
	if !exists {
		return nil, fmt.Errorf("backtest %s not found", runID)
	}

	return runner.GetEquityCurve(), nil
}

// GetTrades returns the trades of a backtest
func (m *Manager) GetTrades(runID string) ([]TradeEvent, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	runner, exists := m.runners[runID]
	if !exists {
		return nil, fmt.Errorf("backtest %s not found", runID)
	}

	return runner.GetTrades(), nil
}

// ListRuns returns all backtest runs
func (m *Manager) ListRuns() []*RunMetadata {
	m.mu.RLock()
	defer m.mu.RUnlock()

	runs := make([]*RunMetadata, 0, len(m.runners))
	for _, runner := range m.runners {
		runs = append(runs, runner.GetMetadata())
	}
	return runs
}

// Delete removes a completed backtest
func (m *Manager) Delete(runID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	runner, exists := m.runners[runID]
	if !exists {
		return fmt.Errorf("backtest %s not found", runID)
	}

	meta := runner.GetMetadata()
	if meta.Status == StatusRunning {
		return fmt.Errorf("cannot delete running backtest")
	}

	delete(m.runners, runID)
	delete(m.metadata, runID)
	delete(m.cancels, runID)

	return nil
}

// LoadKlines loads klines for a backtest
func (m *Manager) LoadKlines(runID, symbol string, klines []Kline) error {
	m.mu.RLock()
	defer m.mu.RUnlock()

	runner, exists := m.runners[runID]
	if !exists {
		return fmt.Errorf("backtest %s not found", runID)
	}

	runner.LoadKlines(symbol, klines)
	return nil
}
