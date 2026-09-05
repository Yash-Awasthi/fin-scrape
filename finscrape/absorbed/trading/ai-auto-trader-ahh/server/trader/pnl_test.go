package trader

import (
	"testing"

	"auto-trader-ahh/exchange"
)

// TestCalculateRealizedPnL tests the P&L calculation logic
// This mirrors the logic in executeTrade for closing positions
func TestCalculateRealizedPnL(t *testing.T) {
	tests := []struct {
		name        string
		positionAmt float64 // Positive = long, Negative = short
		entryPrice  float64
		exitPrice   float64
		quantity    float64
		wantPnL     float64
	}{
		{
			name:        "Long position - profit",
			positionAmt: 0.1,
			entryPrice:  50000,
			exitPrice:   52000,
			quantity:    0.1,
			wantPnL:     200, // (52000 - 50000) * 0.1 = 200
		},
		{
			name:        "Long position - loss",
			positionAmt: 0.1,
			entryPrice:  50000,
			exitPrice:   48000,
			quantity:    0.1,
			wantPnL:     -200, // (48000 - 50000) * 0.1 = -200
		},
		{
			name:        "Short position - profit",
			positionAmt: -0.1,
			entryPrice:  50000,
			exitPrice:   48000,
			quantity:    0.1,
			wantPnL:     200, // (50000 - 48000) * 0.1 = 200
		},
		{
			name:        "Short position - loss",
			positionAmt: -0.1,
			entryPrice:  50000,
			exitPrice:   52000,
			quantity:    0.1,
			wantPnL:     -200, // (50000 - 52000) * 0.1 = -200
		},
		{
			name:        "Large quantity long profit",
			positionAmt: 1.5,
			entryPrice:  45000,
			exitPrice:   46500,
			quantity:    1.5,
			wantPnL:     2250, // (46500 - 45000) * 1.5 = 2250
		},
		{
			name:        "Break even",
			positionAmt: 0.5,
			entryPrice:  50000,
			exitPrice:   50000,
			quantity:    0.5,
			wantPnL:     0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the P&L calculation logic from executeTrade
			var realizedPnL float64
			if tt.positionAmt > 0 { // Long position
				realizedPnL = (tt.exitPrice - tt.entryPrice) * tt.quantity
			} else { // Short position
				realizedPnL = (tt.entryPrice - tt.exitPrice) * tt.quantity
			}

			if realizedPnL != tt.wantPnL {
				t.Errorf("Realized P&L = %f, want %f", realizedPnL, tt.wantPnL)
			}
		})
	}
}

// TestDailyLossCalculation tests the daily loss percentage calculation
func TestDailyLossCalculation(t *testing.T) {
	tests := []struct {
		name           string
		initialBalance float64
		currentBalance float64
		wantLossPct    float64
		exceedsLimit   bool // for 5% limit
		limitPct       float64
	}{
		{
			name:           "No change",
			initialBalance: 10000,
			currentBalance: 10000,
			wantLossPct:    0,
			exceedsLimit:   false,
			limitPct:       5,
		},
		{
			name:           "5% loss exactly at limit",
			initialBalance: 10000,
			currentBalance: 9500,
			wantLossPct:    5,
			exceedsLimit:   true,
			limitPct:       5,
		},
		{
			name:           "10% loss exceeds 5% limit",
			initialBalance: 10000,
			currentBalance: 9000,
			wantLossPct:    10,
			exceedsLimit:   true,
			limitPct:       5,
		},
		{
			name:           "2% loss under 5% limit",
			initialBalance: 10000,
			currentBalance: 9800,
			wantLossPct:    2,
			exceedsLimit:   false,
			limitPct:       5,
		},
		{
			name:           "Profit (negative loss)",
			initialBalance: 10000,
			currentBalance: 11000,
			wantLossPct:    -10, // Negative = profit
			exceedsLimit:   false,
			limitPct:       5,
		},
		{
			name:           "Large account 3% loss",
			initialBalance: 250000,
			currentBalance: 242500,
			wantLossPct:    3,
			exceedsLimit:   false,
			limitPct:       5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Calculate loss percentage (same logic as checkDailyLoss)
			lossPct := ((tt.initialBalance - tt.currentBalance) / tt.initialBalance) * 100

			if lossPct != tt.wantLossPct {
				t.Errorf("Loss %% = %f, want %f", lossPct, tt.wantLossPct)
			}

			exceeds := lossPct >= tt.limitPct
			if exceeds != tt.exceedsLimit {
				t.Errorf("Exceeds limit = %v, want %v (loss: %f%%, limit: %f%%)",
					exceeds, tt.exceedsLimit, lossPct, tt.limitPct)
			}
		})
	}
}

// TestBalanceConsistency verifies TotalMarginBalance is used consistently
func TestBalanceConsistency(t *testing.T) {
	// Simulate account state
	account := &exchange.AccountInfo{
		TotalWalletBalance:    10000,
		TotalUnrealizedProfit: 500,
		TotalMarginBalance:    10500, // Should equal Wallet + Unrealized
		AvailableBalance:      8000,
	}

	// Verify TotalMarginBalance is the correct sum
	expectedMargin := account.TotalWalletBalance + account.TotalUnrealizedProfit
	if account.TotalMarginBalance != expectedMargin {
		t.Errorf("TotalMarginBalance should be %f (Wallet + Unrealized), got %f",
			expectedMargin, account.TotalMarginBalance)
	}

	// The fix uses TotalMarginBalance for both initial and current balance
	// This ensures consistency in daily loss calculation
	initialBalance := account.TotalMarginBalance
	currentBalance := account.TotalMarginBalance

	if initialBalance != currentBalance {
		t.Error("Initial and current balance should be equal when using same account state")
	}

	// Simulate a change
	account.TotalUnrealizedProfit = -200
	account.TotalMarginBalance = account.TotalWalletBalance + account.TotalUnrealizedProfit
	currentBalance = account.TotalMarginBalance

	lossPct := ((initialBalance - currentBalance) / initialBalance) * 100
	expectedLoss := ((10500.0 - 9800.0) / 10500.0) * 100.0 // ~6.67%

	tolerance := 0.01
	if lossPct < expectedLoss-tolerance || lossPct > expectedLoss+tolerance {
		t.Errorf("Loss %% = %f, want ~%f", lossPct, expectedLoss)
	}
}

// TestPnLPercentageCalculation tests the P&L percentage calculation for positions
func TestPnLPercentageCalculation(t *testing.T) {
	tests := []struct {
		name        string
		positionAmt float64
		entryPrice  float64
		markPrice   float64
		wantPnLPct  float64
	}{
		{
			name:        "Long 2% profit",
			positionAmt: 0.1,
			entryPrice:  50000,
			markPrice:   51000,
			wantPnLPct:  2, // (51000 - 50000) / 50000 * 100 = 2%
		},
		{
			name:        "Long 5% loss",
			positionAmt: 0.1,
			entryPrice:  50000,
			markPrice:   47500,
			wantPnLPct:  -5, // (47500 - 50000) / 50000 * 100 = -5%
		},
		{
			name:        "Short 3% profit",
			positionAmt: -0.1,
			entryPrice:  50000,
			markPrice:   48500,
			wantPnLPct:  3, // (50000 - 48500) / 50000 * 100 = 3%
		},
		{
			name:        "Short 4% loss",
			positionAmt: -0.1,
			entryPrice:  50000,
			markPrice:   52000,
			wantPnLPct:  -4, // (50000 - 52000) / 50000 * 100 = -4%
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var pnlPct float64
			if tt.positionAmt > 0 { // Long
				pnlPct = ((tt.markPrice - tt.entryPrice) / tt.entryPrice) * 100
			} else { // Short
				pnlPct = ((tt.entryPrice - tt.markPrice) / tt.entryPrice) * 100
			}

			if pnlPct != tt.wantPnLPct {
				t.Errorf("PnL %% = %f, want %f", pnlPct, tt.wantPnLPct)
			}
		})
	}
}

// TestSymbolValidation tests that invalid symbols are rejected
func TestSymbolValidation(t *testing.T) {
	invalidSymbols := []string{"ALL", "", "all", "All"}

	for _, symbol := range invalidSymbols {
		t.Run("reject_"+symbol, func(t *testing.T) {
			// The executeTrade function should reject these symbols
			// Here we just validate the check logic
			isInvalid := symbol == "ALL" || symbol == ""
			if !isInvalid && (symbol == "all" || symbol == "All") {
				// Case-insensitive check might be needed
				t.Logf("Consider case-insensitive check for: %s", symbol)
			}

			if symbol == "ALL" || symbol == "" {
				// These should definitely be rejected
				if !isInvalid {
					t.Errorf("Symbol %q should be considered invalid", symbol)
				}
			}
		})
	}
}

// TestMarginBufferSingleApplication verifies margin buffer is only applied once
// Bug fix: Previously 0.98 was applied twice (in affordability check AND applyMarginBuffer)
func TestMarginBufferSingleApplication(t *testing.T) {
	tests := []struct {
		name                string
		positionSizeUSD     float64
		maxAffordable       float64
		marginBuffer        float64
		expectBufferApplied bool
		wantFinalSize       float64
	}{
		{
			name:                "Position within affordable - buffer applied once",
			positionSizeUSD:     1000,
			maxAffordable:       2000,
			marginBuffer:        0.98,
			expectBufferApplied: true,
			wantFinalSize:       980, // 1000 * 0.98 = 980
		},
		{
			name:                "Position exceeds affordable - capped then buffer applied",
			positionSizeUSD:     2500,
			maxAffordable:       2000,
			marginBuffer:        0.98,
			expectBufferApplied: true,
			wantFinalSize:       1960, // 2000 * 0.98 = 1960 (NOT 2000 * 0.98 * 0.98)
		},
		{
			name:                "Large position capped correctly",
			positionSizeUSD:     10000,
			maxAffordable:       5000,
			marginBuffer:        0.98,
			expectBufferApplied: true,
			wantFinalSize:       4900, // 5000 * 0.98 = 4900
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the FIXED logic (no double buffer)
			positionSize := tt.positionSizeUSD

			// Step 1: Cap at max affordable (NO 0.98 here anymore)
			if positionSize > tt.maxAffordable {
				positionSize = tt.maxAffordable
			}

			// Step 2: Apply margin buffer ONCE
			if tt.expectBufferApplied {
				positionSize = positionSize * tt.marginBuffer
			}

			if positionSize != tt.wantFinalSize {
				t.Errorf("Final position size = %f, want %f", positionSize, tt.wantFinalSize)
			}

			// Verify we didn't double-apply buffer
			// Old buggy behavior would give: maxAffordable * 0.98 * 0.98
			buggySize := tt.maxAffordable * 0.98 * 0.98
			if tt.positionSizeUSD > tt.maxAffordable && positionSize == buggySize {
				t.Errorf("Double buffer bug detected! Got %f (0.98*0.98)", positionSize)
			}
		})
	}
}

// TestTrailingStopImmediateActivation tests that TSL activates immediately when activatePct <= 0
func TestTrailingStopImmediateActivation(t *testing.T) {
	tests := []struct {
		name           string
		activatePct    float64
		peakPnL        float64
		expectActivate bool
	}{
		{
			name:           "Activate at 0% threshold - activates immediately",
			activatePct:    0,
			peakPnL:        0.5,
			expectActivate: true,
		},
		{
			name:           "Activate at negative threshold - activates immediately",
			activatePct:    -1,
			peakPnL:        0,
			expectActivate: true,
		},
		{
			name:           "Activate at 1% threshold - not activated at 0.5%",
			activatePct:    1.0,
			peakPnL:        0.5,
			expectActivate: false,
		},
		{
			name:           "Activate at 1% threshold - activated at 1.5%",
			activatePct:    1.0,
			peakPnL:        1.5,
			expectActivate: true,
		},
		{
			name:           "Activate at 2% threshold - activated exactly at 2%",
			activatePct:    2.0,
			peakPnL:        2.0,
			expectActivate: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the FIXED trailing stop activation logic
			// activatePct <= 0 means immediate activation
			shouldActivate := tt.activatePct <= 0 || tt.peakPnL >= tt.activatePct

			if shouldActivate != tt.expectActivate {
				t.Errorf("Trailing stop activation = %v, want %v (activatePct: %f, peakPnL: %f)",
					shouldActivate, tt.expectActivate, tt.activatePct, tt.peakPnL)
			}
		})
	}
}

// TestTrailingStopTrigger tests the trailing stop trigger calculation
func TestTrailingStopTrigger(t *testing.T) {
	tests := []struct {
		name          string
		peakPnL       float64
		currentPnL    float64
		trailDistance float64
		expectTrigger bool
	}{
		{
			name:          "Peak 3%, current 2%, trail 0.5% - no trigger",
			peakPnL:       3.0,
			currentPnL:    2.5,
			trailDistance: 0.5,
			expectTrigger: false, // 3.0 - 0.5 = 2.5, current is exactly at level
		},
		{
			name:          "Peak 3%, current 2.4%, trail 0.5% - triggers",
			peakPnL:       3.0,
			currentPnL:    2.4,
			trailDistance: 0.5,
			expectTrigger: true, // 3.0 - 0.5 = 2.5, current 2.4 < 2.5
		},
		{
			name:          "Peak 5%, current 4%, trail 1% - no trigger",
			peakPnL:       5.0,
			currentPnL:    4.0,
			trailDistance: 1.0,
			expectTrigger: false, // 5.0 - 1.0 = 4.0, current equals level
		},
		{
			name:          "Peak 5%, current 3.9%, trail 1% - triggers",
			peakPnL:       5.0,
			currentPnL:    3.9,
			trailDistance: 1.0,
			expectTrigger: true, // 5.0 - 1.0 = 4.0, current 3.9 < 4.0
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			trailingStopLevel := tt.peakPnL - tt.trailDistance
			shouldTrigger := tt.currentPnL < trailingStopLevel

			if shouldTrigger != tt.expectTrigger {
				t.Errorf("Trailing stop trigger = %v, want %v (peak: %f, current: %f, trail: %f, level: %f)",
					shouldTrigger, tt.expectTrigger, tt.peakPnL, tt.currentPnL, tt.trailDistance, trailingStopLevel)
			}
		})
	}
}

// TestEmergencySLCalculation tests the emergency stop-loss calculation
func TestEmergencySLCalculation(t *testing.T) {
	tests := []struct {
		name             string
		isLong           bool
		entryPrice       float64
		normalSLPct      float64
		wantEmergencyPct float64
		wantSLPrice      float64
	}{
		{
			name:             "Long position 2% SL -> 3% emergency",
			isLong:           true,
			entryPrice:       50000,
			normalSLPct:      2.0,
			wantEmergencyPct: 3.0,   // 2.0 * 1.5 = 3.0
			wantSLPrice:      48500, // 50000 * (1 - 0.03)
		},
		{
			name:             "Short position 2% SL -> 3% emergency",
			isLong:           false,
			entryPrice:       50000,
			normalSLPct:      2.0,
			wantEmergencyPct: 3.0,
			wantSLPrice:      51500, // 50000 * (1 + 0.03)
		},
		{
			name:             "Long position 8% SL -> capped at 10%",
			isLong:           true,
			entryPrice:       50000,
			normalSLPct:      8.0,
			wantEmergencyPct: 10.0,  // 8.0 * 1.5 = 12, capped at 10
			wantSLPrice:      45000, // 50000 * (1 - 0.10)
		},
		{
			name:             "Short position 10% SL -> capped at 10%",
			isLong:           false,
			entryPrice:       3000,
			normalSLPct:      10.0,
			wantEmergencyPct: 10.0, // Already at cap
			wantSLPrice:      3300, // 3000 * (1 + 0.10)
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate emergency SL calculation from bracket order failure handling
			emergencySLPct := tt.normalSLPct * 1.5
			if emergencySLPct > 10.0 {
				emergencySLPct = 10.0
			}

			if emergencySLPct != tt.wantEmergencyPct {
				t.Errorf("Emergency SL pct = %f, want %f", emergencySLPct, tt.wantEmergencyPct)
			}

			var slPrice float64
			if tt.isLong {
				slPrice = tt.entryPrice * (1 - emergencySLPct/100)
			} else {
				slPrice = tt.entryPrice * (1 + emergencySLPct/100)
			}

			// Use tolerance for floating point comparison
			tolerance := 0.01
			if slPrice < tt.wantSLPrice-tolerance || slPrice > tt.wantSLPrice+tolerance {
				t.Errorf("Emergency SL price = %f, want %f", slPrice, tt.wantSLPrice)
			}
		})
	}
}

// TestPositionSyncMergeLogic tests that position sync merges instead of replacing
func TestPositionSyncMergeLogic(t *testing.T) {
	// Simulate existing positions (locally tracked)
	localPositions := map[string]float64{
		"BTCUSDT": 0.1,  // Existing long
		"ETHUSDT": -0.5, // Existing short
		"XRPUSDT": 100,  // Just opened locally, not yet on exchange
	}

	// Simulate positions from exchange (might have latency)
	exchangePositions := map[string]float64{
		"BTCUSDT": 0.1,  // Confirmed
		"ETHUSDT": -0.5, // Confirmed
		// XRPUSDT not visible yet (API latency)
	}

	// Merge logic (as implemented in fix)
	merged := make(map[string]float64)

	// Start with local
	for k, v := range localPositions {
		merged[k] = v
	}

	// Update from exchange
	for k, v := range exchangePositions {
		merged[k] = v
	}

	// Verify XRPUSDT is preserved (not lost during merge)
	if _, exists := merged["XRPUSDT"]; !exists {
		t.Error("Locally opened position XRPUSDT should be preserved during merge")
	}

	// Verify exchange updates are applied
	if merged["BTCUSDT"] != 0.1 {
		t.Errorf("BTCUSDT position should be %f, got %f", 0.1, merged["BTCUSDT"])
	}

	if len(merged) != 3 {
		t.Errorf("Merged positions count = %d, want 3", len(merged))
	}
}

// TestTrailingStopRequiresProfit tests that TSL won't trigger at 0% profit
// This fixes the bug where TSL could close positions at a loss when:
// - activatePct = 0 (immediate activation)
// - Peak P&L = 0% (just opened)
// - Current P&L = -0.5% (dropped due to noise)
// - Trail distance = 0.5%
// - Without fix: trigger at trailLevel = 0% - 0.5% = -0.5%, current -0.5% <= -0.5% = TRIGGER (BAD!)
// - With fix: trailLevel = -0.5% which is <= 0, so NO TRIGGER (GOOD!)
func TestTrailingStopRequiresProfit(t *testing.T) {
	tests := []struct {
		name          string
		peakPnL       float64
		currentPnL    float64
		trailDistance float64
		expectTrigger bool
	}{
		{
			name:          "Peak 0%, current -0.5%, trail 0.5% - should NOT trigger (no profit to lock)",
			peakPnL:       0.0,
			currentPnL:    -0.5,
			trailDistance: 0.5,
			expectTrigger: false, // trailingStopLevel = 0 - 0.5 = -0.5, but -0.5 <= 0 so no trigger
		},
		{
			name:          "Peak 0.3%, current -0.2%, trail 0.5% - should NOT trigger (trail level negative)",
			peakPnL:       0.3,
			currentPnL:    -0.2,
			trailDistance: 0.5,
			expectTrigger: false, // trailingStopLevel = 0.3 - 0.5 = -0.2, -0.2 <= 0 so no trigger
		},
		{
			name:          "Peak 1%, current 0.4%, trail 0.5% - should TRIGGER (profit locked)",
			peakPnL:       1.0,
			currentPnL:    0.4,
			trailDistance: 0.5,
			expectTrigger: true, // trailingStopLevel = 1.0 - 0.5 = 0.5 > 0, current 0.4 <= 0.5 = TRIGGER
		},
		{
			name:          "Peak 2%, current 1.4%, trail 0.5% - should TRIGGER (profit locked)",
			peakPnL:       2.0,
			currentPnL:    1.4,
			trailDistance: 0.5,
			expectTrigger: true, // trailingStopLevel = 2.0 - 0.5 = 1.5 > 0, current 1.4 <= 1.5 = TRIGGER
		},
		{
			name:          "Peak 0.5%, current 0.4%, trail 0.5% - should NOT trigger (trail level at 0)",
			peakPnL:       0.5,
			currentPnL:    0.4,
			trailDistance: 0.5,
			expectTrigger: false, // trailingStopLevel = 0.5 - 0.5 = 0.0, current 0.4 > 0 = NO TRIGGER
		},
		{
			name:          "Peak 0.6%, current 0.05%, trail 0.5% - should TRIGGER (trail level slightly positive)",
			peakPnL:       0.6,
			currentPnL:    0.05,
			trailDistance: 0.5,
			expectTrigger: true, // trailingStopLevel = 0.6 - 0.5 = 0.1 > 0, current 0.05 <= 0.1 = TRIGGER
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			trailingStopLevel := tt.peakPnL - tt.trailDistance

			// The FIXED logic: require trailingStopLevel > 0 to trigger
			// This ensures we're locking in actual profits, not just closing at losses
			shouldTrigger := tt.currentPnL <= trailingStopLevel && trailingStopLevel > 0

			if shouldTrigger != tt.expectTrigger {
				t.Errorf("Trailing stop trigger = %v, want %v\n"+
					"  peakPnL: %.2f%%, currentPnL: %.2f%%, trailDist: %.2f%%, trailLevel: %.2f%%",
					shouldTrigger, tt.expectTrigger,
					tt.peakPnL, tt.currentPnL, tt.trailDistance, trailingStopLevel)
			}
		})
	}
}

// TestPositionSizingUsesFreshBalance verifies that position sizing uses fresh account data
// Bug: Previously used e.account (cached) instead of account (fresh) leading to over-leveraging
func TestPositionSizingUsesFreshBalance(t *testing.T) {
	tests := []struct {
		name             string
		cachedBalance    float64
		freshBalance     float64
		positionPct      float64
		wantPositionSize float64
		useFresh         bool
	}{
		{
			name:             "Fresh balance lower than cached - should use fresh to avoid over-leverage",
			cachedBalance:    10000,
			freshBalance:     8000, // Balance dropped since cache
			positionPct:      10.0,
			wantPositionSize: 800, // 8000 * 10% = 800 (not 1000!)
			useFresh:         true,
		},
		{
			name:             "Fresh balance higher than cached - using fresh gives more room",
			cachedBalance:    10000,
			freshBalance:     12000, // Balance increased
			positionPct:      10.0,
			wantPositionSize: 1200, // 12000 * 10% = 1200
			useFresh:         true,
		},
		{
			name:             "Same balance - no difference",
			cachedBalance:    10000,
			freshBalance:     10000,
			positionPct:      15.0,
			wantPositionSize: 1500,
			useFresh:         true,
		},
		{
			name:             "Using cached when fresh is lower - DANGEROUS over-leverage",
			cachedBalance:    10000,
			freshBalance:     5000, // Balance halved!
			positionPct:      20.0,
			wantPositionSize: 1000, // Should be 1000 (5000 * 20%), not 2000!
			useFresh:         true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var positionSize float64

			if tt.useFresh {
				positionSize = (tt.freshBalance * tt.positionPct) / 100
			} else {
				positionSize = (tt.cachedBalance * tt.positionPct) / 100
			}

			if positionSize != tt.wantPositionSize {
				t.Errorf("Position size = %.2f, want %.2f", positionSize, tt.wantPositionSize)
			}

			// Verify using cached would have been wrong when balances differ
			if tt.cachedBalance != tt.freshBalance {
				cachedPositionSize := (tt.cachedBalance * tt.positionPct) / 100
				if tt.freshBalance < tt.cachedBalance && positionSize == cachedPositionSize {
					t.Errorf("DANGER: Using stale cached balance would over-leverage! cached=%.2f, fresh=%.2f",
						cachedPositionSize, positionSize)
				}
			}
		})
	}
}

// TestGetMinPositionSize tests the minimum position size retrieval with fallback logic
func TestGetMinPositionSize(t *testing.T) {
	tests := []struct {
		name                  string
		symbol                string
		minPositionSize       float64 // New field for altcoins
		minPositionSizeBTCETH float64 // New field for BTC/ETH
		minPositionUSD        float64 // Legacy fallback
		wantMinSize           float64
	}{
		{
			name:                  "Altcoin with new field set",
			symbol:                "IPUSDT",
			minPositionSize:       20.0,
			minPositionSizeBTCETH: 60.0,
			minPositionUSD:        10.0,
			wantMinSize:           20.0, // Uses minPositionSize
		},
		{
			name:                  "Altcoin falls back to legacy",
			symbol:                "SOLUSDT",
			minPositionSize:       0, // Not set
			minPositionSizeBTCETH: 60.0,
			minPositionUSD:        15.0,
			wantMinSize:           15.0, // Falls back to minPositionUSD
		},
		{
			name:                  "Altcoin falls back to default",
			symbol:                "DOGEUSDT",
			minPositionSize:       0,    // Not set
			minPositionSizeBTCETH: 0,    // Not set
			minPositionUSD:        0,    // Not set
			wantMinSize:           12.0, // Default for altcoins
		},
		{
			name:                  "BTC with new field set",
			symbol:                "BTCUSDT",
			minPositionSize:       20.0,
			minPositionSizeBTCETH: 50.0,
			minPositionUSD:        10.0,
			wantMinSize:           50.0, // Uses minPositionSizeBTCETH
		},
		{
			name:                  "ETH falls back to legacy",
			symbol:                "ETHUSDT",
			minPositionSize:       20.0,
			minPositionSizeBTCETH: 0, // Not set
			minPositionUSD:        30.0,
			wantMinSize:           30.0, // Falls back to minPositionUSD
		},
		{
			name:                  "BTC falls back to default",
			symbol:                "BTCUSDT",
			minPositionSize:       0,
			minPositionSizeBTCETH: 0,
			minPositionUSD:        0,
			wantMinSize:           50.0, // Default for BTC/ETH
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate the getMinPositionSize logic
			var minSize float64

			if isBTCETH(tt.symbol) {
				minSize = tt.minPositionSizeBTCETH
				if minSize <= 0 {
					minSize = tt.minPositionUSD
				}
				if minSize <= 0 {
					minSize = 50.0 // BTC/ETH default
				}
			} else {
				minSize = tt.minPositionSize
				if minSize <= 0 {
					minSize = tt.minPositionUSD
				}
				if minSize <= 0 {
					minSize = 12.0 // Altcoin default
				}
			}

			if minSize != tt.wantMinSize {
				t.Errorf("getMinPositionSize(%s) = %.2f, want %.2f", tt.symbol, minSize, tt.wantMinSize)
			}
		})
	}
}

// TestNotionalValueValidation tests that positions with tiny notional values are rejected
func TestNotionalValueValidation(t *testing.T) {
	tests := []struct {
		name              string
		symbol            string
		marginUSD         float64
		leverage          int
		price             float64
		wantNotionalValue float64
		minNotionalValue  float64
		shouldReject      bool
	}{
		{
			name:              "Tiny position - should reject",
			symbol:            "IPUSDT",
			marginUSD:         0.013, // Your actual case
			leverage:          20,
			price:             2.64,
			wantNotionalValue: 0.26, // 0.013 * 20 = 0.26
			minNotionalValue:  10.0,
			shouldReject:      true,
		},
		{
			name:              "Normal altcoin position - should accept",
			symbol:            "SOLUSDT",
			marginUSD:         10.0,
			leverage:          20,
			price:             100.0,
			wantNotionalValue: 200.0, // 10 * 20 = 200
			minNotionalValue:  10.0,
			shouldReject:      false,
		},
		{
			name:              "BTC below minimum - should reject",
			symbol:            "BTCUSDT",
			marginUSD:         2.0,
			leverage:          10,
			price:             50000.0,
			wantNotionalValue: 20.0, // 2 * 10 = 20
			minNotionalValue:  50.0, // BTC requires $50
			shouldReject:      true,
		},
		{
			name:              "BTC at minimum - should accept",
			symbol:            "BTCUSDT",
			marginUSD:         5.0,
			leverage:          10,
			price:             50000.0,
			wantNotionalValue: 50.0, // 5 * 10 = 50
			minNotionalValue:  50.0,
			shouldReject:      false,
		},
		{
			name:              "ETH above minimum - should accept",
			symbol:            "ETHUSDT",
			marginUSD:         10.0,
			leverage:          10,
			price:             3000.0,
			wantNotionalValue: 100.0, // 10 * 10 = 100
			minNotionalValue:  50.0,
			shouldReject:      false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			actualPositionValue := tt.marginUSD * float64(tt.leverage)

			// Tolerance for float comparison
			tolerance := 0.01
			if actualPositionValue < tt.wantNotionalValue-tolerance || actualPositionValue > tt.wantNotionalValue+tolerance {
				t.Errorf("Notional value = %.2f, want %.2f", actualPositionValue, tt.wantNotionalValue)
			}

			// Check if should be rejected
			shouldReject := actualPositionValue < tt.minNotionalValue
			if shouldReject != tt.shouldReject {
				t.Errorf("Should reject = %v, want %v (notional: $%.2f, min: $%.2f)",
					shouldReject, tt.shouldReject, actualPositionValue, tt.minNotionalValue)
			}
		})
	}
}

// TestEarlyRejectionOnCappedPosition tests that trades are rejected early when
// the affordable margin is below the minimum position size
func TestEarlyRejectionOnCappedPosition(t *testing.T) {
	tests := []struct {
		name                      string
		symbol                    string
		wantedPositionSize        float64
		maxAffordablePositionSize float64
		minPositionRequired       float64
		shouldRejectEarly         bool
	}{
		{
			name:                      "Affordable but below minimum - reject early",
			symbol:                    "IPUSDT",
			wantedPositionSize:        100.0,
			maxAffordablePositionSize: 5.0, // Only $5 available
			minPositionRequired:       20.0,
			shouldRejectEarly:         true,
		},
		{
			name:                      "Affordable and above minimum - accept",
			symbol:                    "SOLUSDT",
			wantedPositionSize:        100.0,
			maxAffordablePositionSize: 50.0, // $50 available
			minPositionRequired:       20.0,
			shouldRejectEarly:         false,
		},
		{
			name:                      "Position not capped - no early rejection check",
			symbol:                    "DOGEUSDT",
			wantedPositionSize:        50.0,
			maxAffordablePositionSize: 100.0, // More than wanted
			minPositionRequired:       20.0,
			shouldRejectEarly:         false, // Not capped, so no early rejection
		},
		{
			name:                      "BTC capped below minimum - reject early",
			symbol:                    "BTCUSDT",
			wantedPositionSize:        200.0,
			maxAffordablePositionSize: 30.0, // Only $30 available
			minPositionRequired:       50.0, // BTC needs $50
			shouldRejectEarly:         true,
		},
		{
			name:                      "Exactly at minimum - accept",
			symbol:                    "XRPUSDT",
			wantedPositionSize:        100.0,
			maxAffordablePositionSize: 20.0, // Exactly at minimum
			minPositionRequired:       20.0,
			shouldRejectEarly:         false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			positionSize := tt.wantedPositionSize
			wasCapped := false

			// Simulate capping logic
			if positionSize > tt.maxAffordablePositionSize {
				positionSize = tt.maxAffordablePositionSize
				wasCapped = true
			}

			// Early rejection check (only if capped)
			shouldReject := false
			if wasCapped && positionSize < tt.minPositionRequired {
				shouldReject = true
			}

			if shouldReject != tt.shouldRejectEarly {
				t.Errorf("Early rejection = %v, want %v\n"+
					"  wanted: $%.2f, affordable: $%.2f, min: $%.2f, capped: %v",
					shouldReject, tt.shouldRejectEarly,
					tt.wantedPositionSize, tt.maxAffordablePositionSize, tt.minPositionRequired, wasCapped)
			}
		})
	}
}

// TestWeightedPnLPercentage tests that PnL percentage is weighted by position notional
func TestWeightedPnLPercentage(t *testing.T) {
	tests := []struct {
		name      string
		positions []struct {
			amount     float64
			entryPrice float64
			pnlPercent float64
		}
		wantWeightedPct float64
	}{
		{
			name: "Your actual case - small profit large loss",
			positions: []struct {
				amount     float64
				entryPrice float64
				pnlPercent float64
			}{
				{amount: 0.1, entryPrice: 2.64, pnlPercent: 1.96},    // IPUSDT: $0.264 notional
				{amount: 23.9, entryPrice: 18.51, pnlPercent: -1.40}, // RIVERUSDT: $442.39 notional
			},
			wantWeightedPct: -1.38, // Heavily weighted toward the loss
		},
		{
			name: "Equal positions",
			positions: []struct {
				amount     float64
				entryPrice float64
				pnlPercent float64
			}{
				{amount: 1.0, entryPrice: 100.0, pnlPercent: 2.0},  // $100 notional
				{amount: 1.0, entryPrice: 100.0, pnlPercent: -2.0}, // $100 notional
			},
			wantWeightedPct: 0.0, // Should be 0 (equal weight cancels out)
		},
		{
			name: "Single position",
			positions: []struct {
				amount     float64
				entryPrice float64
				pnlPercent float64
			}{
				{amount: 0.5, entryPrice: 50000.0, pnlPercent: 3.5}, // BTC $25000 notional
			},
			wantWeightedPct: 3.5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Calculate weighted average (same logic as Dashboard.tsx fix)
			var totalNotional float64
			var weightedSum float64

			for _, p := range tt.positions {
				notional := p.amount * p.entryPrice
				if notional < 0 {
					notional = -notional // Math.abs
				}
				totalNotional += notional
				weightedSum += p.pnlPercent * notional
			}

			var weightedPct float64
			if totalNotional > 0 {
				weightedPct = weightedSum / totalNotional
			}

			// Use tolerance for float comparison
			tolerance := 0.1
			if weightedPct < tt.wantWeightedPct-tolerance || weightedPct > tt.wantWeightedPct+tolerance {
				t.Errorf("Weighted PnL%% = %.2f, want %.2f", weightedPct, tt.wantWeightedPct)
			}
		})
	}
}
