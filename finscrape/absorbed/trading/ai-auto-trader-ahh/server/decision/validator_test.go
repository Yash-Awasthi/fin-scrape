package decision

import (
	"strings"
	"testing"
)

func TestValidateDecision_ValidActions(t *testing.T) {
	cfg := DefaultValidationConfig()
	cfg.MinRiskReward = 0 // Disable R:R validation for this test

	tests := []struct {
		name       string
		action     string
		stopLoss   float64
		takeProfit float64
		wantErr    bool
	}{
		{"open_long valid", ActionOpenLong, 45000, 55000, false},
		{"open_short valid", ActionOpenShort, 55000, 45000, false}, // Short: SL above, TP below
		{"close_long valid", ActionCloseLong, 0, 0, false},
		{"close_short valid", ActionCloseShort, 0, 0, false},
		{"hold valid", ActionHold, 0, 0, false},
		{"wait valid", ActionWait, 0, 0, false},
		{"invalid action", "moon", 0, 0, true},
		{"empty action", "", 0, 0, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			d := &Decision{
				Symbol:          "BTCUSDT",
				Action:          tt.action,
				Leverage:        10,
				PositionSizeUSD: 100,
				StopLoss:        tt.stopLoss,
				TakeProfit:      tt.takeProfit,
			}
			err := ValidateDecision(d, cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateDecision() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestValidateDecision_RejectsALLSymbol(t *testing.T) {
	cfg := DefaultValidationConfig()
	cfg.MinRiskReward = 0 // Disable R:R validation to focus on symbol validation

	tests := []struct {
		name    string
		symbol  string
		action  string
		wantErr bool
	}{
		{"ALL symbol with open_long rejected", "ALL", ActionOpenLong, true},
		{"ALL symbol with open_short rejected", "ALL", ActionOpenShort, true},
		{"empty symbol with open_long rejected", "", ActionOpenLong, true},
		{"ALL symbol with wait allowed", "ALL", ActionWait, false},
		{"ALL symbol with hold allowed", "ALL", ActionHold, false},
		{"valid symbol with open_long allowed", "BTCUSDT", ActionOpenLong, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			d := &Decision{
				Symbol:          tt.symbol,
				Action:          tt.action,
				Leverage:        10,
				PositionSizeUSD: 100,
				StopLoss:        45000,
				TakeProfit:      55000,
			}
			err := ValidateDecision(d, cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateDecision() error = %v, wantErr %v", err, tt.wantErr)
			}
			if tt.wantErr && err != nil && !strings.Contains(err.Error(), "symbol") {
				t.Errorf("Expected symbol-related error, got: %v", err)
			}
		})
	}
}

func TestValidateDecision_LeverageRejection(t *testing.T) {
	cfg := &ValidationConfig{
		AccountEquity:     10000,
		BTCETHLeverage:    20,
		AltcoinLeverage:   10,
		BTCETHPosRatio:    0.3,
		AltcoinPosRatio:   0.15,
		MinPositionBTCETH: 60,
		MinPositionAlt:    12,
		MinRiskReward:     0, // Disable R:R validation to focus on leverage validation
	}

	tests := []struct {
		name           string
		symbol         string
		leverage       int
		wantErr        bool
		errContains    string
		leverageAfter  int // leverage should NOT change (no auto-adjust)
	}{
		{
			name:          "BTC leverage within limit",
			symbol:        "BTCUSDT",
			leverage:      15,
			wantErr:       false,
			leverageAfter: 15,
		},
		{
			name:          "BTC leverage at max",
			symbol:        "BTCUSDT",
			leverage:      20,
			wantErr:       false,
			leverageAfter: 20,
		},
		{
			name:          "BTC leverage exceeds max - REJECTED not adjusted",
			symbol:        "BTCUSDT",
			leverage:      25,
			wantErr:       true,
			errContains:   "exceeds maximum",
			leverageAfter: 25, // Should NOT be adjusted
		},
		{
			name:          "Altcoin leverage within limit",
			symbol:        "SOLUSDT",
			leverage:      8,
			wantErr:       false,
			leverageAfter: 8,
		},
		{
			name:          "Altcoin leverage exceeds max - REJECTED",
			symbol:        "SOLUSDT",
			leverage:      15,
			wantErr:       true,
			errContains:   "exceeds maximum",
			leverageAfter: 15, // Should NOT be adjusted
		},
		{
			name:          "Zero leverage rejected",
			symbol:        "BTCUSDT",
			leverage:      0,
			wantErr:       true,
			errContains:   "greater than 0",
			leverageAfter: 0,
		},
		{
			name:          "Negative leverage rejected",
			symbol:        "BTCUSDT",
			leverage:      -5,
			wantErr:       true,
			errContains:   "greater than 0",
			leverageAfter: -5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			d := &Decision{
				Symbol:          tt.symbol,
				Action:          ActionOpenLong,
				Leverage:        tt.leverage,
				PositionSizeUSD: 100,
				StopLoss:        40000,
				TakeProfit:      50000,
			}

			originalLeverage := d.Leverage
			err := ValidateDecision(d, cfg)

			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateDecision() error = %v, wantErr %v", err, tt.wantErr)
			}

			if tt.wantErr && err != nil && tt.errContains != "" {
				if !strings.Contains(err.Error(), tt.errContains) {
					t.Errorf("Expected error containing %q, got: %v", tt.errContains, err)
				}
			}

			// CRITICAL: Verify leverage was NOT silently adjusted
			if d.Leverage != originalLeverage {
				t.Errorf("Leverage was silently adjusted from %d to %d - this should NOT happen",
					originalLeverage, d.Leverage)
			}
		})
	}
}

func TestValidateRiskReward_LongPositions(t *testing.T) {
	// R:R validation estimates entry as midpoint between SL and TP
	// This means asymmetric SL/TP placements create different R:R ratios
	// Example: SL=45000, TP=60000 -> entry~52500 -> risk=7500, reward=7500 -> 1:1
	// To get 2:1, TP needs to be further from entry than SL
	tests := []struct {
		name       string
		stopLoss   float64
		takeProfit float64
		minRatio   float64
		wantErr    bool
	}{
		{
			name:       "Symmetric SL/TP gives 1:1 R:R",
			stopLoss:   45000,
			takeProfit: 55000, // Midpoint entry=50000, risk=5000, reward=5000 -> 1:1
			minRatio:   1.0,
			wantErr:    false,
		},
		{
			name:       "Symmetric SL/TP fails 2:1 minimum",
			stopLoss:   45000,
			takeProfit: 55000, // 1:1 ratio fails 2:1 minimum
			minRatio:   2.0,
			wantErr:    true,
		},
		{
			name:       "No SL/TP - skips validation",
			stopLoss:   0,
			takeProfit: 0,
			minRatio:   3.0,
			wantErr:    false,
		},
		{
			name:       "Validation disabled (minRatio=0)",
			stopLoss:   45000,
			takeProfit: 46000,
			minRatio:   0,
			wantErr:    false,
		},
		{
			name:       "R:R exactly at minimum passes",
			stopLoss:   48000,
			takeProfit: 52000, // Midpoint=50000, risk=2000, reward=2000 -> 1:1
			minRatio:   1.0,
			wantErr:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			d := &Decision{
				Action:     ActionOpenLong,
				StopLoss:   tt.stopLoss,
				TakeProfit: tt.takeProfit,
			}
			err := validateRiskReward(d, tt.minRatio)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateRiskReward() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestValidateRiskReward_ShortPositions(t *testing.T) {
	// For shorts: SL above entry, TP below entry
	// Same midpoint logic applies
	tests := []struct {
		name       string
		stopLoss   float64
		takeProfit float64
		minRatio   float64
		wantErr    bool
	}{
		{
			name:       "Symmetric SL/TP short gives 1:1",
			stopLoss:   55000, // Midpoint=50000, SL above
			takeProfit: 45000, // TP below, risk=5000, reward=5000 -> 1:1
			minRatio:   1.0,
			wantErr:    false,
		},
		{
			name:       "Short 1:1 fails 2:1 minimum",
			stopLoss:   55000,
			takeProfit: 45000, // 1:1 ratio
			minRatio:   2.0,
			wantErr:    true,
		},
		{
			name:       "Short validation disabled",
			stopLoss:   52000,
			takeProfit: 48000,
			minRatio:   0,
			wantErr:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			d := &Decision{
				Action:     ActionOpenShort,
				StopLoss:   tt.stopLoss,
				TakeProfit: tt.takeProfit,
			}
			err := validateRiskReward(d, tt.minRatio)
			if (err != nil) != tt.wantErr {
				t.Errorf("validateRiskReward() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestValidateOpeningDecision_PositionSize(t *testing.T) {
	cfg := &ValidationConfig{
		AccountEquity:     10000,
		BTCETHLeverage:    20,
		AltcoinLeverage:   10,
		BTCETHPosRatio:    0.3,  // 30% max = $3000
		AltcoinPosRatio:   0.15, // 15% max = $1500
		MinPositionBTCETH: 60,
		MinPositionAlt:    12,
		MinRiskReward:     0, // Disable R:R for this test
	}

	tests := []struct {
		name        string
		symbol      string
		positionUSD float64
		wantErr     bool
		errContains string
	}{
		{
			name:        "BTC position within limit",
			symbol:      "BTCUSDT",
			positionUSD: 2000,
			wantErr:     false,
		},
		{
			name:        "BTC position at minimum",
			symbol:      "BTCUSDT",
			positionUSD: 60,
			wantErr:     false,
		},
		{
			name:        "BTC position below minimum",
			symbol:      "BTCUSDT",
			positionUSD: 50,
			wantErr:     true,
			errContains: "too small",
		},
		{
			name:        "BTC position exceeds max",
			symbol:      "BTCUSDT",
			positionUSD: 5000,
			wantErr:     true,
			errContains: "exceed",
		},
		{
			name:        "Altcoin position within limit",
			symbol:      "SOLUSDT",
			positionUSD: 1000,
			wantErr:     false,
		},
		{
			name:        "Altcoin position below minimum",
			symbol:      "SOLUSDT",
			positionUSD: 10,
			wantErr:     true,
			errContains: "too small",
		},
		{
			name:        "Zero position rejected",
			symbol:      "BTCUSDT",
			positionUSD: 0,
			wantErr:     true,
			errContains: "greater than 0",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			d := &Decision{
				Symbol:          tt.symbol,
				Action:          ActionOpenLong,
				Leverage:        10,
				PositionSizeUSD: tt.positionUSD,
				StopLoss:        40000,
				TakeProfit:      60000,
			}
			err := ValidateDecision(d, cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateDecision() error = %v, wantErr %v", err, tt.wantErr)
			}
			if tt.wantErr && err != nil && tt.errContains != "" {
				if !strings.Contains(err.Error(), tt.errContains) {
					t.Errorf("Expected error containing %q, got: %v", tt.errContains, err)
				}
			}
		})
	}
}

func TestIsBTCOrETH(t *testing.T) {
	tests := []struct {
		symbol string
		want   bool
	}{
		{"BTCUSDT", true},
		{"ETHUSDT", true},
		{"BTC-USDT", true},
		{"ETH-USDT", true},
		{"BTCUSD", true},
		{"ETHUSD", true},
		{"SOLUSDT", false},
		{"DOGEUSDT", false},
		{"btcusdt", false}, // Case sensitive
		{"", false},
	}

	for _, tt := range tests {
		t.Run(tt.symbol, func(t *testing.T) {
			if got := isBTCOrETH(tt.symbol); got != tt.want {
				t.Errorf("isBTCOrETH(%q) = %v, want %v", tt.symbol, got, tt.want)
			}
		})
	}
}

func TestIsOpeningAction(t *testing.T) {
	tests := []struct {
		action string
		want   bool
	}{
		{ActionOpenLong, true},
		{ActionOpenShort, true},
		{ActionCloseLong, false},
		{ActionCloseShort, false},
		{ActionHold, false},
		{ActionWait, false},
		{"BUY", false},  // Legacy action not considered "opening"
		{"SELL", false}, // Legacy action not considered "opening"
	}

	for _, tt := range tests {
		t.Run(tt.action, func(t *testing.T) {
			if got := IsOpeningAction(tt.action); got != tt.want {
				t.Errorf("IsOpeningAction(%q) = %v, want %v", tt.action, got, tt.want)
			}
		})
	}
}

func TestIsClosingAction(t *testing.T) {
	tests := []struct {
		action string
		want   bool
	}{
		{ActionCloseLong, true},
		{ActionCloseShort, true},
		{ActionOpenLong, false},
		{ActionOpenShort, false},
		{ActionHold, false},
		{ActionWait, false},
	}

	for _, tt := range tests {
		t.Run(tt.action, func(t *testing.T) {
			if got := IsClosingAction(tt.action); got != tt.want {
				t.Errorf("IsClosingAction(%q) = %v, want %v", tt.action, got, tt.want)
			}
		})
	}
}
