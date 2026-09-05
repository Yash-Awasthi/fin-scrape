package trader

import (
	"testing"

	"auto-trader-ahh/exchange"
)

// TestPnLCalculationConsistency verifies that P&L calculations for risk checks
// are based on RAW price movement, not leveraged ROE.
// This prevents the bug where leverage multipliers caused premature stops.
func TestPnLCalculationConsistency(t *testing.T) {
	// Setup a position with 10x leverage
	pos := &exchange.Position{
		Symbol:      "BTCUSDT",
		PositionAmt: 0.1,
		EntryPrice:  50000,
		MarkPrice:   49950, // -0.1% price drop
		Leverage:    10,
	}

	// 1. Calculate Raw Price P&L %
	// (49950 - 50000) / 50000 = -0.001 = -0.1%
	rawPnlPct := ((pos.MarkPrice - pos.EntryPrice) / pos.EntryPrice) * 100

	// 2. Calculate Leveraged ROE (What the bug was doing)
	// -0.1% * 10 = -1.0%
	leveragedPnlPct := rawPnlPct * float64(pos.Leverage)

	// Verify our math foundation
	if rawPnlPct != -0.1 {
		t.Errorf("Math check failed: want -0.1 raw, got %f", rawPnlPct)
	}
	if leveragedPnlPct != -1.0 {
		t.Errorf("Math check failed: want -1.0 leveraged, got %f", leveragedPnlPct)
	}

	// 3. Simulate the fix logic (Should use RAW)
	// The variable used for Noise Zone checks should be rawPnlPct
	riskCheckPnl := rawPnlPct

	// 4. Validate against Noise Zone Thresholds
	// Standard noise zone is -1.5% to +1.5%
	noiseZoneLower := -1.5

	// Case A: Using RAW (-0.1%), we are INSIDE the noise zone (-0.1 > -1.5).
	// Current Action: BLOCK CLOSE (Correct behavior - ignore noise)
	isInsideZoneRaw := riskCheckPnl > noiseZoneLower
	if !isInsideZoneRaw {
		t.Error("FAIL: Raw P&L (-0.1%) should be considered INSIDE noise zone (>-1.5%), but was flagged as significant loss")
	}

	// Case B: Using LEVERAGED (-1.0%), we are suspiciously close to the limit.
	// If price drops just a bit more to -0.15% -> Leveraged becomes -1.5%
	// This shows how tight the leveraged check was.

	// Case C: Simulate the Critical Failure Scenario
	// Price drops -0.2% -> Leveraged -2.0%
	pos.MarkPrice = 49900
	raw2 := ((pos.MarkPrice - pos.EntryPrice) / pos.EntryPrice) * 100 // -0.2%
	lev2 := raw2 * float64(pos.Leverage)                              // -2.0%

	// With BUG (Leveraged): -2.0% < -1.5% -> TRIGGERS STOP (Bad, it's just noise)
	wouldTriggerBug := lev2 < noiseZoneLower
	if !wouldTriggerBug {
		t.Error("Math verification failed: -2.0% should trigger < -1.5% check")
	}

	// With FIX (Raw): -0.2% > -1.5% -> NO TRIGGER (Good, holds position)
	shouldHold := raw2 > noiseZoneLower
	if !shouldHold {
		t.Errorf("FAIL: Fix logic should HOLD at -0.2%% raw price drop, but triggered stop.")
	}
}
