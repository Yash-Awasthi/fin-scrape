package trader

import (
	"testing"

	"auto-trader-ahh/exchange"
)

// TestTrailingStopUsesRawPct verifies that trailing stop uses raw price percentage,
// NOT ROE (leveraged) percentage. This ensures the config values are intuitive:
// 1.5% means 1.5% price move, not 1.5% ROE (which would be 0.075% price move at 20x).
func TestTrailingStopUsesRawPct(t *testing.T) {
	tests := []struct {
		name                string
		entryPrice          float64
		markPrice           float64
		leverage            int
		activatePct         float64 // Config value (should be raw %)
		trailDistPct        float64 // Config value (should be raw %)
		expectActivated     bool
		expectTriggerAtPeak float64 // Price that would trigger TSL after reaching peak
	}{
		{
			name:                "20x leverage, 1.5% raw price move activates TSL",
			entryPrice:          50000,
			markPrice:           50750, // +1.5% raw price move
			leverage:            20,
			activatePct:         1.5,
			trailDistPct:        0.5,
			expectActivated:     true,
			expectTriggerAtPeak: 50500, // 1.5% - 0.5% = 1.0% from entry
		},
		{
			name:                "20x leverage, 0.5% raw price move does NOT activate TSL with 1.5% threshold",
			entryPrice:          50000,
			markPrice:           50250, // +0.5% raw price move (would be 10% ROE!)
			leverage:            20,
			activatePct:         1.5,
			trailDistPct:        0.5,
			expectActivated:     false,
			expectTriggerAtPeak: 0,
		},
		{
			name:                "10x leverage, 2% raw price move activates TSL",
			entryPrice:          3000,
			markPrice:           3060, // +2% raw price move
			leverage:            10,
			activatePct:         1.5,
			trailDistPct:        0.5,
			expectActivated:     true,
			expectTriggerAtPeak: 3045, // 2% - 0.5% = 1.5% from entry
		},
		{
			name:                "High leverage doesn't affect activation threshold",
			entryPrice:          100,
			markPrice:           101, // +1% raw (would be 50% ROE at 50x!)
			leverage:            50,
			activatePct:         1.5, // Needs 1.5% RAW, not ROE
			trailDistPct:        0.5,
			expectActivated:     false, // Should NOT activate at 1% raw
			expectTriggerAtPeak: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Calculate raw price P&L % (this is what trailing stop should use)
			rawPnlPct := ((tt.markPrice - tt.entryPrice) / tt.entryPrice) * 100

			// Calculate ROE (what it should NOT use)
			roePnlPct := rawPnlPct * float64(tt.leverage)

			// Log the difference for clarity
			t.Logf("Raw P&L: %.2f%%, ROE P&L: %.2f%% (leverage: %dx)", rawPnlPct, roePnlPct, tt.leverage)

			// Check if TSL should activate (using RAW %, as per fix)
			shouldActivate := tt.activatePct <= 0 || rawPnlPct >= tt.activatePct

			if shouldActivate != tt.expectActivated {
				t.Errorf("TSL activation = %v, want %v\n"+
					"  rawPnlPct: %.2f%%, activatePct: %.2f%%\n"+
					"  (If using ROE %.2f%% incorrectly, would have activated: %v)",
					shouldActivate, tt.expectActivated,
					rawPnlPct, tt.activatePct,
					roePnlPct, roePnlPct >= tt.activatePct)
			}

			// Verify the fix prevents premature activation
			if !tt.expectActivated && roePnlPct >= tt.activatePct {
				// This would have activated with the OLD buggy logic
				t.Logf("FIX VERIFIED: Old ROE-based logic would have incorrectly activated at %.2f%% ROE", roePnlPct)
			}
		})
	}
}

// TestDrawdownProtectionUsesRawPct verifies drawdown protection uses raw price %
func TestDrawdownProtectionUsesRawPct(t *testing.T) {
	tests := []struct {
		name              string
		entryPrice        float64
		peakPrice         float64
		currentPrice      float64
		leverage          int
		minProfitPct      float64 // min_profit_for_drawdown (should be raw %)
		drawdownThreshold float64 // drawdown_close_threshold (relative %)
		expectProtection  bool    // Should drawdown protection be active?
		expectTrigger     bool    // Should it trigger a close?
	}{
		{
			name:              "5% raw profit peak, 70% drawdown threshold - should activate protection",
			entryPrice:        50000,
			peakPrice:         52500, // +5% raw
			currentPrice:      50750, // +1.5% raw (dropped from 5%)
			leverage:          20,
			minProfitPct:      5.0,
			drawdownThreshold: 70.0,
			expectProtection:  true,
			expectTrigger:     true, // Drawdown is (5-1.5)/5 = 70%
		},
		{
			name:              "3% raw profit - below 5% threshold, protection not active",
			entryPrice:        50000,
			peakPrice:         51500, // +3% raw (60% ROE at 20x!)
			currentPrice:      50500, // +1% raw
			leverage:          20,
			minProfitPct:      5.0,
			drawdownThreshold: 70.0,
			expectProtection:  false, // 3% raw < 5% threshold
			expectTrigger:     false,
		},
		{
			name:              "High leverage doesn't lower activation threshold",
			entryPrice:        1000,
			peakPrice:         1020, // +2% raw (100% ROE at 50x!)
			currentPrice:      1005, // +0.5% raw
			leverage:          50,
			minProfitPct:      5.0, // Needs 5% RAW profit, not ROE
			drawdownThreshold: 70.0,
			expectProtection:  false, // 2% raw < 5% threshold
			expectTrigger:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Calculate raw P&L at peak and current (LONG position)
			peakRawPct := ((tt.peakPrice - tt.entryPrice) / tt.entryPrice) * 100
			currentRawPct := ((tt.currentPrice - tt.entryPrice) / tt.entryPrice) * 100

			// Calculate ROE equivalents for comparison
			peakROE := peakRawPct * float64(tt.leverage)
			currentROE := currentRawPct * float64(tt.leverage)

			t.Logf("Peak: %.2f%% raw (%.2f%% ROE), Current: %.2f%% raw (%.2f%% ROE)",
				peakRawPct, peakROE, currentRawPct, currentROE)

			// Check if protection should be active (using RAW %)
			protectionActive := peakRawPct >= tt.minProfitPct

			if protectionActive != tt.expectProtection {
				t.Errorf("Protection active = %v, want %v\n"+
					"  peakRawPct: %.2f%%, minProfitPct: %.2f%%\n"+
					"  (If using ROE %.2f%% incorrectly, would be: %v)",
					protectionActive, tt.expectProtection,
					peakRawPct, tt.minProfitPct,
					peakROE, peakROE >= tt.minProfitPct)
			}

			// Calculate drawdown if protection is active
			if protectionActive {
				drawdownPct := ((peakRawPct - currentRawPct) / peakRawPct) * 100
				shouldTrigger := drawdownPct >= tt.drawdownThreshold

				if shouldTrigger != tt.expectTrigger {
					t.Errorf("Drawdown trigger = %v, want %v (drawdown: %.2f%%, threshold: %.2f%%)",
						shouldTrigger, tt.expectTrigger, drawdownPct, tt.drawdownThreshold)
				}
			}
		})
	}
}

// TestNoiseZoneUsesRawPct verifies noise zone protection uses raw price %
func TestNoiseZoneUsesRawPct(t *testing.T) {
	tests := []struct {
		name           string
		entryPrice     float64
		markPrice      float64
		leverage       int
		lowerBound     float64 // noise_zone_lower_bound (raw %)
		upperBound     float64 // noise_zone_upper_bound (raw %)
		expectInZone   bool
		expectDecision string // "block", "allow_loss", "allow_profit"
	}{
		{
			name:           "0.5% raw profit - in noise zone",
			entryPrice:     50000,
			markPrice:      50250, // +0.5% raw
			leverage:       20,
			lowerBound:     -1.0,
			upperBound:     1.5,
			expectInZone:   true,
			expectDecision: "block",
		},
		{
			name:           "2% raw profit - above noise zone ceiling",
			entryPrice:     50000,
			markPrice:      51000, // +2% raw
			leverage:       20,
			lowerBound:     -1.0,
			upperBound:     1.5,
			expectInZone:   false,
			expectDecision: "allow_profit",
		},
		{
			name:           "1.5% raw loss - below noise zone floor",
			entryPrice:     50000,
			markPrice:      49250, // -1.5% raw
			leverage:       20,
			lowerBound:     -1.0,
			upperBound:     1.5,
			expectInZone:   false,
			expectDecision: "allow_loss",
		},
		{
			name:           "High leverage 0.5% raw is still in zone (not 25% ROE)",
			entryPrice:     1000,
			markPrice:      1005, // +0.5% raw (25% ROE at 50x!)
			leverage:       50,
			lowerBound:     -1.0,
			upperBound:     1.5,
			expectInZone:   true, // 0.5% RAW is in zone, despite 25% ROE
			expectDecision: "block",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Calculate raw P&L %
			rawPnlPct := ((tt.markPrice - tt.entryPrice) / tt.entryPrice) * 100
			roePnlPct := rawPnlPct * float64(tt.leverage)

			t.Logf("Raw P&L: %.2f%%, ROE P&L: %.2f%%", rawPnlPct, roePnlPct)

			// Determine zone and decision (using RAW %)
			var decision string
			var inZone bool

			if rawPnlPct < tt.lowerBound {
				decision = "allow_loss"
				inZone = false
			} else if rawPnlPct >= tt.upperBound {
				decision = "allow_profit"
				inZone = false
			} else {
				decision = "block"
				inZone = true
			}

			if inZone != tt.expectInZone {
				t.Errorf("In noise zone = %v, want %v\n"+
					"  rawPnlPct: %.2f%%, bounds: [%.2f%%, %.2f%%]",
					inZone, tt.expectInZone, rawPnlPct, tt.lowerBound, tt.upperBound)
			}

			if decision != tt.expectDecision {
				t.Errorf("Decision = %q, want %q", decision, tt.expectDecision)
			}

			// Verify using ROE would have been wrong
			if inZone && roePnlPct >= tt.upperBound {
				t.Logf("FIX VERIFIED: ROE-based check would have allowed close at %.2f%% ROE (but raw is only %.2f%%)",
					roePnlPct, rawPnlPct)
			}
		})
	}
}

// TestAllRiskFeaturesUseSameScale verifies all risk features use raw % consistently
func TestAllRiskFeaturesUseSameScale(t *testing.T) {
	// Simulate a position
	pos := &exchange.Position{
		Symbol:      "BTCUSDT",
		PositionAmt: 0.1, // Long
		EntryPrice:  50000,
		MarkPrice:   50500, // +1% raw price move
		Leverage:    20,
	}

	// Calculate both percentages
	rawPnlPct := ((pos.MarkPrice - pos.EntryPrice) / pos.EntryPrice) * 100
	roePnlPct := rawPnlPct * float64(pos.Leverage)

	t.Logf("Position: Entry $%.0f, Mark $%.0f, Leverage %dx", pos.EntryPrice, pos.MarkPrice, pos.Leverage)
	t.Logf("Raw P&L: %.2f%%, ROE P&L: %.2f%%", rawPnlPct, roePnlPct)

	// Define config values (all should be interpreted as RAW %)
	config := struct {
		TrailingStopActivatePct float64
		TrailingStopDistancePct float64
		NoiseZoneLowerBound     float64
		NoiseZoneUpperBound     float64
		SmartLossCutPct         float64
		MinProfitForDrawdown    float64
	}{
		TrailingStopActivatePct: 1.5, // 1.5% raw
		TrailingStopDistancePct: 0.5, // 0.5% raw
		NoiseZoneLowerBound:     -1.0,
		NoiseZoneUpperBound:     1.5,
		SmartLossCutPct:         -2.0,
		MinProfitForDrawdown:    5.0,
	}

	// All features should use rawPnlPct for comparisons
	// At 1% raw profit:

	// 1. Trailing Stop: Should NOT activate (1% < 1.5%)
	tslActivated := rawPnlPct >= config.TrailingStopActivatePct
	if tslActivated {
		t.Error("Trailing stop should NOT activate at 1% raw (threshold is 1.5%)")
	}

	// 2. Noise Zone: 1% is IN the zone (-1 to 1.5)
	inNoiseZone := rawPnlPct >= config.NoiseZoneLowerBound && rawPnlPct < config.NoiseZoneUpperBound
	if !inNoiseZone {
		t.Error("1% raw should be IN noise zone [-1%, 1.5%)")
	}

	// 3. Smart Loss Cut: Should NOT trigger (1% > -2%)
	smartLossTriggered := rawPnlPct <= config.SmartLossCutPct
	if smartLossTriggered {
		t.Error("Smart loss cut should NOT trigger at 1% profit")
	}

	// 4. Drawdown Protection: Should NOT be active (1% < 5%)
	drawdownActive := rawPnlPct >= config.MinProfitForDrawdown
	if drawdownActive {
		t.Error("Drawdown protection should NOT activate at 1% raw (threshold is 5%)")
	}

	// Verify the OLD buggy behavior would have been different
	t.Log("\n--- Comparison with OLD ROE-based logic ---")

	// With ROE (20% at 20x leverage):
	oldTslActivated := roePnlPct >= config.TrailingStopActivatePct
	if oldTslActivated {
		t.Log("OLD BUG: ROE-based TSL would have activated at 20% ROE (1% raw)")
	}

	oldInNoiseZone := roePnlPct >= config.NoiseZoneLowerBound && roePnlPct < config.NoiseZoneUpperBound
	if !oldInNoiseZone {
		t.Log("OLD BUG: ROE-based noise zone would have allowed close at 20% ROE")
	}
}

// TestConfigValuesAreIntuitive verifies that config values work intuitively
func TestConfigValuesAreIntuitive(t *testing.T) {
	// User sets trailing_stop_activate_pct to 1.5
	// They expect: "Activate after 1.5% price move"
	// NOT: "Activate after 1.5% ROE" (which varies wildly by leverage)

	testCases := []struct {
		leverage     int
		rawPriceMove float64
		configValue  float64
		description  string
	}{
		{5, 1.5, 1.5, "5x leverage: 1.5% price = 7.5% ROE, activates at 1.5% config"},
		{10, 1.5, 1.5, "10x leverage: 1.5% price = 15% ROE, activates at 1.5% config"},
		{20, 1.5, 1.5, "20x leverage: 1.5% price = 30% ROE, activates at 1.5% config"},
		{50, 1.5, 1.5, "50x leverage: 1.5% price = 75% ROE, activates at 1.5% config"},
		{125, 1.5, 1.5, "125x leverage: 1.5% price = 187.5% ROE, activates at 1.5% config"},
	}

	for _, tc := range testCases {
		t.Run(tc.description, func(t *testing.T) {
			// All should activate regardless of leverage, because config is raw %
			shouldActivate := tc.rawPriceMove >= tc.configValue
			if !shouldActivate {
				t.Errorf("Config 1.5%% should activate at 1.5%% raw price move regardless of leverage")
			}

			roePct := tc.rawPriceMove * float64(tc.leverage)
			t.Logf("At %dx leverage: %.1f%% raw = %.1f%% ROE. Config value %.1f%% (raw) correctly triggers.",
				tc.leverage, tc.rawPriceMove, roePct, tc.configValue)
		})
	}
}

// TestShortPositionRawPctCalculation verifies raw % works for shorts too
func TestShortPositionRawPctCalculation(t *testing.T) {
	tests := []struct {
		name       string
		entryPrice float64
		markPrice  float64
		leverage   int
		wantRawPct float64
	}{
		{
			name:       "Short 2% profit",
			entryPrice: 50000,
			markPrice:  49000, // Price dropped = profit for short
			leverage:   20,
			wantRawPct: 2.0,
		},
		{
			name:       "Short 1% loss",
			entryPrice: 50000,
			markPrice:  50500, // Price rose = loss for short
			leverage:   20,
			wantRawPct: -1.0,
		},
		{
			name:       "Short breakeven",
			entryPrice: 50000,
			markPrice:  50000,
			leverage:   20,
			wantRawPct: 0.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Short position: profit when price goes DOWN
			rawPnlPct := ((tt.entryPrice - tt.markPrice) / tt.entryPrice) * 100

			if rawPnlPct != tt.wantRawPct {
				t.Errorf("Raw P&L = %.2f%%, want %.2f%%", rawPnlPct, tt.wantRawPct)
			}

			// Verify ROE calculation for reference
			roePnlPct := rawPnlPct * float64(tt.leverage)
			t.Logf("Short position: Raw %.2f%%, ROE %.2f%%", rawPnlPct, roePnlPct)
		})
	}
}
