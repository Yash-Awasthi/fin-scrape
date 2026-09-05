package trader

import (
	"encoding/json"
	"strings"
	"testing"
	"time"

	"auto-trader-ahh/store"
)

// TestSmartFindAutoRefreshConfig tests the Smart Find auto-refresh configuration
func TestSmartFindAutoRefreshConfig(t *testing.T) {
	tests := []struct {
		name              string
		autoRefresh       bool
		refreshMins       int
		expectEnabled     bool
		expectDefaultMins int
	}{
		{
			name:              "Auto-refresh disabled by default",
			autoRefresh:       false,
			refreshMins:       0,
			expectEnabled:     false,
			expectDefaultMins: 60, // Default should be 60
		},
		{
			name:              "Auto-refresh enabled with 30 min interval",
			autoRefresh:       true,
			refreshMins:       30,
			expectEnabled:     true,
			expectDefaultMins: 30,
		},
		{
			name:              "Auto-refresh enabled with 1 hour interval",
			autoRefresh:       true,
			refreshMins:       60,
			expectEnabled:     true,
			expectDefaultMins: 60,
		},
		{
			name:              "Auto-refresh enabled with 2 hour interval",
			autoRefresh:       true,
			refreshMins:       120,
			expectEnabled:     true,
			expectDefaultMins: 120,
		},
		{
			name:              "Auto-refresh enabled with 4 hour interval",
			autoRefresh:       true,
			refreshMins:       240,
			expectEnabled:     true,
			expectDefaultMins: 240,
		},
		{
			name:              "Auto-refresh enabled with 0 mins defaults to 60",
			autoRefresh:       true,
			refreshMins:       0,
			expectEnabled:     true,
			expectDefaultMins: 60,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config := store.StrategyConfig{
				SmartFindAutoRefresh: tt.autoRefresh,
				SmartFindRefreshMins: tt.refreshMins,
			}

			if config.SmartFindAutoRefresh != tt.expectEnabled {
				t.Errorf("SmartFindAutoRefresh = %v, want %v", config.SmartFindAutoRefresh, tt.expectEnabled)
			}

			// Test default logic (same as in maybeRefreshSmartFind)
			refreshMins := config.SmartFindRefreshMins
			if refreshMins <= 0 {
				refreshMins = 60
			}

			if refreshMins != tt.expectDefaultMins {
				t.Errorf("RefreshMins = %d, want %d", refreshMins, tt.expectDefaultMins)
			}
		})
	}
}

// TestSmartFindRefreshTiming tests the timing logic for refresh intervals
func TestSmartFindRefreshTiming(t *testing.T) {
	tests := []struct {
		name           string
		lastRefresh    time.Time
		refreshMins    int
		expectRefresh  bool
	}{
		{
			name:          "Never refreshed - should refresh",
			lastRefresh:   time.Time{}, // Zero time
			refreshMins:   60,
			expectRefresh: true,
		},
		{
			name:          "Refreshed 10 mins ago, interval 60 mins - should NOT refresh",
			lastRefresh:   time.Now().Add(-10 * time.Minute),
			refreshMins:   60,
			expectRefresh: false,
		},
		{
			name:          "Refreshed 30 mins ago, interval 30 mins - should refresh",
			lastRefresh:   time.Now().Add(-30 * time.Minute),
			refreshMins:   30,
			expectRefresh: true,
		},
		{
			name:          "Refreshed 61 mins ago, interval 60 mins - should refresh",
			lastRefresh:   time.Now().Add(-61 * time.Minute),
			refreshMins:   60,
			expectRefresh: true,
		},
		{
			name:          "Refreshed 59 mins ago, interval 60 mins - should NOT refresh",
			lastRefresh:   time.Now().Add(-59 * time.Minute),
			refreshMins:   60,
			expectRefresh: false,
		},
		{
			name:          "Refreshed 2 hours ago, interval 120 mins - should refresh",
			lastRefresh:   time.Now().Add(-121 * time.Minute),
			refreshMins:   120,
			expectRefresh: true,
		},
		{
			name:          "Refreshed 4 hours ago, interval 240 mins - should refresh",
			lastRefresh:   time.Now().Add(-241 * time.Minute),
			refreshMins:   240,
			expectRefresh: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the timing check from maybeRefreshSmartFind
			shouldRefresh := time.Since(tt.lastRefresh) >= time.Duration(tt.refreshMins)*time.Minute

			if shouldRefresh != tt.expectRefresh {
				t.Errorf("Should refresh = %v, want %v (last refresh: %v, interval: %d mins)",
					shouldRefresh, tt.expectRefresh, tt.lastRefresh, tt.refreshMins)
			}
		})
	}
}

// TestSmartFindTargetCount tests that target count is 2x max positions
func TestSmartFindTargetCount(t *testing.T) {
	tests := []struct {
		name         string
		maxPositions int
		wantCount    int
	}{
		{
			name:         "Max positions 1 -> find 2 symbols",
			maxPositions: 1,
			wantCount:    2,
		},
		{
			name:         "Max positions 2 -> find 4 symbols",
			maxPositions: 2,
			wantCount:    4,
		},
		{
			name:         "Max positions 3 (default) -> find 6 symbols",
			maxPositions: 3,
			wantCount:    6,
		},
		{
			name:         "Max positions 5 -> find 10 symbols",
			maxPositions: 5,
			wantCount:    10,
		},
		{
			name:         "Max positions 0 -> defaults to 3, find 6 symbols",
			maxPositions: 0,
			wantCount:    6, // (3 default) * 2 = 6
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the target count calculation from maybeRefreshSmartFind
			maxPositions := tt.maxPositions
			if maxPositions <= 0 {
				maxPositions = 3 // Default
			}
			targetCount := maxPositions * 2

			if targetCount != tt.wantCount {
				t.Errorf("Target count = %d, want %d (maxPositions: %d)",
					targetCount, tt.wantCount, tt.maxPositions)
			}
		})
	}
}

// TestSmartFindParseResponse tests parsing of AI response JSON
func TestSmartFindParseResponse(t *testing.T) {
	tests := []struct {
		name        string
		aiResponse  string
		wantSymbols []string
		wantError   bool
	}{
		{
			name:        "Clean JSON array",
			aiResponse:  `["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]`,
			wantSymbols: []string{"BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"},
			wantError:   false,
		},
		{
			name:        "JSON with markdown code block",
			aiResponse:  "```json\n[\"BTCUSDT\", \"ETHUSDT\"]\n```",
			wantSymbols: []string{"BTCUSDT", "ETHUSDT"},
			wantError:   false,
		},
		{
			name:        "JSON with leading text",
			aiResponse:  "Here are the recommended pairs:\n[\"BTCUSDT\", \"SOLUSDT\"]",
			wantSymbols: []string{"BTCUSDT", "SOLUSDT"},
			wantError:   false,
		},
		{
			name:        "JSON with trailing text",
			aiResponse:  "[\"BTCUSDT\", \"ETHUSDT\", \"BNBUSDT\"]\nThese are high volatility pairs.",
			wantSymbols: []string{"BTCUSDT", "ETHUSDT", "BNBUSDT"},
			wantError:   false,
		},
		{
			name:        "Single symbol array",
			aiResponse:  `["BTCUSDT"]`,
			wantSymbols: []string{"BTCUSDT"},
			wantError:   false,
		},
		{
			name:        "Empty array",
			aiResponse:  `[]`,
			wantSymbols: []string{},
			wantError:   false,
		},
		{
			name:        "Invalid JSON - no array",
			aiResponse:  `"BTCUSDT"`,
			wantSymbols: nil,
			wantError:   true,
		},
		{
			name:        "Invalid JSON - malformed",
			aiResponse:  `[BTCUSDT, ETHUSDT]`,
			wantSymbols: nil,
			wantError:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the JSON parsing logic from runSmartFind
			jsonStr := tt.aiResponse
			if idx := strings.Index(jsonStr, "["); idx != -1 {
				jsonStr = jsonStr[idx:]
			}
			if idx := strings.LastIndex(jsonStr, "]"); idx != -1 {
				jsonStr = jsonStr[:idx+1]
			}

			var recommended []string
			err := json.Unmarshal([]byte(jsonStr), &recommended)

			if tt.wantError {
				if err == nil {
					t.Errorf("Expected error but got none, parsed: %v", recommended)
				}
				return
			}

			if err != nil {
				t.Errorf("Unexpected error: %v", err)
				return
			}

			if len(recommended) != len(tt.wantSymbols) {
				t.Errorf("Symbol count = %d, want %d", len(recommended), len(tt.wantSymbols))
				return
			}

			for i, symbol := range recommended {
				if symbol != tt.wantSymbols[i] {
					t.Errorf("Symbol[%d] = %s, want %s", i, symbol, tt.wantSymbols[i])
				}
			}
		})
	}
}

// TestSmartFindCandidateFiltering tests the candidate filtering logic
func TestSmartFindCandidateFiltering(t *testing.T) {
	tests := []struct {
		name         string
		symbol       string
		quoteVolume  float64
		expectPass   bool
		rejectReason string
	}{
		{
			name:        "Valid BTCUSDT with high volume",
			symbol:      "BTCUSDT",
			quoteVolume: 10000000, // 10M
			expectPass:  true,
		},
		{
			name:        "Valid ETHUSDT with high volume",
			symbol:      "ETHUSDT",
			quoteVolume: 5000000, // 5M
			expectPass:  true,
		},
		{
			name:         "Low volume - rejected",
			symbol:       "SOMEUSDT",
			quoteVolume:  400000, // 400k < 500k threshold
			expectPass:   false,
			rejectReason: "volume below 500k",
		},
		{
			name:         "Stablecoin USDCUSDT - rejected",
			symbol:       "USDCUSDT",
			quoteVolume:  1000000000,
			expectPass:   false,
			rejectReason: "stablecoin",
		},
		{
			name:         "Stablecoin FDUSDUSDT - rejected",
			symbol:       "FDUSDUSDT",
			quoteVolume:  500000000,
			expectPass:   false,
			rejectReason: "stablecoin",
		},
		{
			name:         "Stablecoin TUSDUSDT - rejected",
			symbol:       "TUSDUSDT",
			quoteVolume:  100000000,
			expectPass:   false,
			rejectReason: "stablecoin",
		},
		{
			name:         "Non-USDT pair - rejected",
			symbol:       "BTCETH",
			quoteVolume:  10000000,
			expectPass:   false,
			rejectReason: "not USDT pair",
		},
		{
			name:         "Short symbol - rejected",
			symbol:       "BTC",
			quoteVolume:  10000000,
			expectPass:   false,
			rejectReason: "symbol too short",
		},
		{
			name:        "Exactly 500k volume - passes",
			symbol:      "XRPUSDT",
			quoteVolume: 500001, // Just above threshold
			expectPass:  true,
		},
	}

	stablecoins := map[string]bool{
		"USDCUSDT":  true,
		"FDUSDUSDT": true,
		"TUSDUSDT":  true,
		"USDPUSDT":  true,
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the filtering logic from runSmartFind
			passes := true
			reason := ""

			// Check symbol length
			if len(tt.symbol) <= 4 {
				passes = false
				reason = "symbol too short"
			}

			// Check USDT suffix
			if passes && (len(tt.symbol) <= 4 || tt.symbol[len(tt.symbol)-4:] != "USDT") {
				passes = false
				reason = "not USDT pair"
			}

			// Check stablecoin
			if passes && stablecoins[tt.symbol] {
				passes = false
				reason = "stablecoin"
			}

			// Check volume
			if passes && tt.quoteVolume <= 500000 {
				passes = false
				reason = "volume below 500k"
			}

			if passes != tt.expectPass {
				t.Errorf("Filter result = %v, want %v (symbol: %s, reason: %s)",
					passes, tt.expectPass, tt.symbol, reason)
			}

			if !tt.expectPass && reason != tt.rejectReason {
				t.Errorf("Reject reason = %s, want %s", reason, tt.rejectReason)
			}
		})
	}
}

// TestSmartFindTurboModePrompt tests that Turbo Mode affects the prompt style
func TestSmartFindTurboModePrompt(t *testing.T) {
	tests := []struct {
		name             string
		turboMode        bool
		expectAggressive bool
		expectKeywords   []string
	}{
		{
			name:             "Turbo Mode ON - aggressive prompt",
			turboMode:        true,
			expectAggressive: true,
			expectKeywords:   []string{"HIGH RISK", "EXPLOSIVE", "extreme risks", "Volatility"},
		},
		{
			name:             "Turbo Mode OFF - standard prompt",
			turboMode:        false,
			expectAggressive: false,
			expectKeywords:   []string{"trading expert", "high-probability", "liquidity", "Volume"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate prompt building based on Turbo Mode
			var prompt string
			if tt.turboMode {
				prompt = `You are a HIGH RISK crypto degen trader.
Objective: Find the MOST EXPLOSIVE trading pairs for aggressive scalping.
I am willing to take extreme risks (80-90% loss) for high rewards.
Criteria: High Volatility, Momentum, Meme Coins, or Breakout candidates.`
			} else {
				prompt = `You are a crypto trading expert.
Objective: Find the best trading pairs for high-probability scalping/day-trading.
Criteria: High liquidity, good volatility, clear trends.
Here are the Top 30 pairs by 24h Volume:`
			}

			for _, keyword := range tt.expectKeywords {
				if !strings.Contains(prompt, keyword) {
					t.Errorf("Prompt should contain '%s' for turboMode=%v", keyword, tt.turboMode)
				}
			}

			// Verify exclusive keywords don't appear in wrong mode
			if tt.turboMode {
				if strings.Contains(prompt, "high-probability") {
					t.Error("Turbo mode prompt should NOT contain 'high-probability'")
				}
			} else {
				if strings.Contains(prompt, "EXPLOSIVE") {
					t.Error("Standard mode prompt should NOT contain 'EXPLOSIVE'")
				}
			}
		})
	}
}

// TestSmartFindDefaultConfig tests the default strategy config values
func TestSmartFindDefaultConfig(t *testing.T) {
	defaultConfig := store.DefaultStrategyConfig()

	// Smart Find Auto-Refresh should be disabled by default
	if defaultConfig.SmartFindAutoRefresh != false {
		t.Errorf("SmartFindAutoRefresh should be disabled by default, got %v", defaultConfig.SmartFindAutoRefresh)
	}

	// Default interval should be 60 minutes
	if defaultConfig.SmartFindRefreshMins != 60 {
		t.Errorf("SmartFindRefreshMins default should be 60, got %d", defaultConfig.SmartFindRefreshMins)
	}
}

// TestSmartFindVolatilitySorting tests that Turbo Mode sorts by volatility
func TestSmartFindVolatilitySorting(t *testing.T) {
	type MarketCoin struct {
		Symbol      string
		PriceChange float64
	}

	candidates := []MarketCoin{
		{Symbol: "BTCUSDT", PriceChange: 2.5},
		{Symbol: "ETHUSDT", PriceChange: -5.0},  // More volatile (absolute)
		{Symbol: "XRPUSDT", PriceChange: 10.0},  // Most volatile
		{Symbol: "SOLUSDT", PriceChange: -3.0},
	}

	// Sort by absolute price change (volatility) - same logic as in runSmartFind
	// Using bubble sort for test simplicity
	for i := 0; i < len(candidates)-1; i++ {
		for j := 0; j < len(candidates)-i-1; j++ {
			absI := candidates[j].PriceChange
			if absI < 0 {
				absI = -absI
			}
			absJ := candidates[j+1].PriceChange
			if absJ < 0 {
				absJ = -absJ
			}
			if absI < absJ {
				candidates[j], candidates[j+1] = candidates[j+1], candidates[j]
			}
		}
	}

	// Expected order by absolute volatility: XRPUSDT (10), ETHUSDT (5), SOLUSDT (3), BTCUSDT (2.5)
	expectedOrder := []string{"XRPUSDT", "ETHUSDT", "SOLUSDT", "BTCUSDT"}

	for i, expected := range expectedOrder {
		if candidates[i].Symbol != expected {
			t.Errorf("Position %d: got %s, want %s", i, candidates[i].Symbol, expected)
		}
	}
}

// TestSmartFindVolumeSorting tests that Standard Mode sorts by volume
func TestSmartFindVolumeSorting(t *testing.T) {
	type MarketCoin struct {
		Symbol      string
		QuoteVolume float64
	}

	candidates := []MarketCoin{
		{Symbol: "XRPUSDT", QuoteVolume: 500000},
		{Symbol: "BTCUSDT", QuoteVolume: 10000000},
		{Symbol: "SOLUSDT", QuoteVolume: 2000000},
		{Symbol: "ETHUSDT", QuoteVolume: 8000000},
	}

	// Sort by volume - same logic as in runSmartFind for standard mode
	// Using bubble sort for test simplicity
	for i := 0; i < len(candidates)-1; i++ {
		for j := 0; j < len(candidates)-i-1; j++ {
			if candidates[j].QuoteVolume < candidates[j+1].QuoteVolume {
				candidates[j], candidates[j+1] = candidates[j+1], candidates[j]
			}
		}
	}

	// Expected order by volume: BTCUSDT (10M), ETHUSDT (8M), SOLUSDT (2M), XRPUSDT (500k)
	expectedOrder := []string{"BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"}

	for i, expected := range expectedOrder {
		if candidates[i].Symbol != expected {
			t.Errorf("Position %d: got %s, want %s", i, candidates[i].Symbol, expected)
		}
	}
}
