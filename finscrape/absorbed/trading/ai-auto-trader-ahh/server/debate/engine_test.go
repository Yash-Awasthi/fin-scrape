package debate

import (
	"testing"
)

func TestDetermineConsensus_ConfidenceThreshold(t *testing.T) {
	e := &Engine{}

	tests := []struct {
		name           string
		votes          []*Vote
		wantDecisions  int
		description    string
	}{
		{
			name: "Low confidence decisions filtered out",
			votes: []*Vote{
				{
					Personality: "Bull",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "open_long", Confidence: 30}, // Below 50%
					},
				},
				{
					Personality: "Bear",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "wait", Confidence: 40}, // Below 50%
					},
				},
			},
			wantDecisions: 0, // All filtered out
			description:   "Both decisions below 50% confidence should be filtered",
		},
		{
			name: "High confidence decisions included",
			votes: []*Vote{
				{
					Personality: "Bull",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "open_long", Confidence: 85, Leverage: 10, PositionPct: 0.1},
					},
				},
				{
					Personality: "Analyst",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "open_long", Confidence: 75, Leverage: 8, PositionPct: 0.15},
					},
				},
			},
			wantDecisions: 1, // BTCUSDT consensus
			description:   "Both high confidence votes should contribute to consensus",
		},
		{
			name: "Mixed confidence - only high included",
			votes: []*Vote{
				{
					Personality: "Bull",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "open_long", Confidence: 90, Leverage: 10},
					},
				},
				{
					Personality: "Bear",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "open_short", Confidence: 30}, // Filtered
					},
				},
			},
			wantDecisions: 1,
			description:   "Only 90% confidence vote should count, bear's 30% filtered",
		},
		{
			name: "Exactly 50% confidence included",
			votes: []*Vote{
				{
					Personality: "Bull",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "open_long", Confidence: 50, Leverage: 5},
					},
				},
			},
			wantDecisions: 1,
			description:   "50% is the threshold, should be included",
		},
		{
			name: "49% confidence filtered",
			votes: []*Vote{
				{
					Personality: "Bull",
					Decisions: []*Decision{
						{Symbol: "BTCUSDT", Action: "open_long", Confidence: 49, Leverage: 5},
					},
				},
			},
			wantDecisions: 0,
			description:   "49% is below threshold, should be filtered",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := e.determineConsensus(tt.votes)
			if len(results) != tt.wantDecisions {
				t.Errorf("determineConsensus() returned %d decisions, want %d. %s",
					len(results), tt.wantDecisions, tt.description)
			}
		})
	}
}

func TestDetermineConsensus_PreservesPositionSizeUSD(t *testing.T) {
	e := &Engine{}

	votes := []*Vote{
		{
			Personality: "Bull",
			Decisions: []*Decision{
				{
					Symbol:          "BTCUSDT",
					Action:          "open_long",
					Confidence:      80,
					Leverage:        10,
					PositionPct:     0.1,
					PositionSizeUSD: 1000,
				},
			},
		},
		{
			Personality: "Analyst",
			Decisions: []*Decision{
				{
					Symbol:          "BTCUSDT",
					Action:          "open_long",
					Confidence:      70,
					Leverage:        8,
					PositionPct:     0.15,
					PositionSizeUSD: 2000,
				},
			},
		},
	}

	results := e.determineConsensus(votes)

	if len(results) != 1 {
		t.Fatalf("Expected 1 decision, got %d", len(results))
	}

	decision := results[0]

	// Check that PositionSizeUSD is preserved (average of 1000 and 2000 = 1500)
	expectedPosUSD := 1500.0
	if decision.PositionSizeUSD != expectedPosUSD {
		t.Errorf("PositionSizeUSD = %f, want %f (average)", decision.PositionSizeUSD, expectedPosUSD)
	}

	// Check that PositionPct is also preserved (average of 0.1 and 0.15 = 0.125)
	expectedPosPct := 0.125
	if decision.PositionPct != expectedPosPct {
		t.Errorf("PositionPct = %f, want %f (average)", decision.PositionPct, expectedPosPct)
	}
}

func TestDetermineConsensus_WeightsByConfidence(t *testing.T) {
	e := &Engine{}

	// Test that higher confidence votes have more weight
	votes := []*Vote{
		{
			Personality: "Bull",
			Decisions: []*Decision{
				{Symbol: "BTCUSDT", Action: "open_long", Confidence: 95, Leverage: 10},
			},
		},
		{
			Personality: "Bear",
			Decisions: []*Decision{
				{Symbol: "BTCUSDT", Action: "open_short", Confidence: 55, Leverage: 5},
			},
		},
	}

	results := e.determineConsensus(votes)

	if len(results) != 1 {
		t.Fatalf("Expected 1 decision, got %d", len(results))
	}

	// The Bull's 95% confidence vote should win over Bear's 55%
	if results[0].Action != "open_long" {
		t.Errorf("Expected open_long to win (95%% confidence), got %s", results[0].Action)
	}
}

func TestDetermineConsensus_MultipleSymbols(t *testing.T) {
	e := &Engine{}

	votes := []*Vote{
		{
			Personality: "Bull",
			Decisions: []*Decision{
				{Symbol: "BTCUSDT", Action: "open_long", Confidence: 80, Leverage: 10},
				{Symbol: "ETHUSDT", Action: "open_long", Confidence: 75, Leverage: 8},
			},
		},
		{
			Personality: "Analyst",
			Decisions: []*Decision{
				{Symbol: "BTCUSDT", Action: "open_long", Confidence: 85, Leverage: 12},
				{Symbol: "SOLUSDT", Action: "wait", Confidence: 60},
			},
		},
	}

	results := e.determineConsensus(votes)

	// Should have decisions for BTCUSDT, ETHUSDT, and SOLUSDT
	if len(results) != 3 {
		t.Errorf("Expected 3 decisions (BTC, ETH, SOL), got %d", len(results))
	}

	// Verify each symbol has a decision
	symbols := make(map[string]bool)
	for _, d := range results {
		symbols[d.Symbol] = true
	}

	for _, expected := range []string{"BTCUSDT", "ETHUSDT", "SOLUSDT"} {
		if !symbols[expected] {
			t.Errorf("Missing decision for %s", expected)
		}
	}
}

func TestDetermineConsensus_DefaultValues(t *testing.T) {
	e := &Engine{}

	votes := []*Vote{
		{
			Personality: "Bull",
			Decisions: []*Decision{
				{
					Symbol:     "BTCUSDT",
					Action:     "open_long",
					Confidence: 80,
					Leverage:   0, // Missing leverage
					// Missing position info
				},
			},
		},
	}

	results := e.determineConsensus(votes)

	if len(results) != 1 {
		t.Fatalf("Expected 1 decision, got %d", len(results))
	}

	decision := results[0]

	// Should apply default leverage of 5
	if decision.Leverage != 5 {
		t.Errorf("Expected default leverage 5, got %d", decision.Leverage)
	}

	// Should apply default position of 0.2 (20%) when no position info provided
	if decision.PositionPct != 0.2 {
		t.Errorf("Expected default PositionPct 0.2, got %f", decision.PositionPct)
	}
}

func TestDetermineConsensus_NoDefaultWhenPositionProvided(t *testing.T) {
	e := &Engine{}

	votes := []*Vote{
		{
			Personality: "Bull",
			Decisions: []*Decision{
				{
					Symbol:          "BTCUSDT",
					Action:          "open_long",
					Confidence:      80,
					Leverage:        15,
					PositionSizeUSD: 500, // Only USD provided, no Pct
				},
			},
		},
	}

	results := e.determineConsensus(votes)

	if len(results) != 1 {
		t.Fatalf("Expected 1 decision, got %d", len(results))
	}

	decision := results[0]

	// Should NOT apply default position since PositionSizeUSD was provided
	if decision.PositionPct != 0 {
		t.Errorf("Expected PositionPct 0 (since USD was provided), got %f", decision.PositionPct)
	}

	if decision.PositionSizeUSD != 500 {
		t.Errorf("Expected PositionSizeUSD 500, got %f", decision.PositionSizeUSD)
	}
}

func TestConvertRawDecisions_PreservesPositionSizeUSD(t *testing.T) {
	rawDecisions := []struct {
		Symbol          string  `json:"symbol"`
		Action          string  `json:"action"`
		Confidence      int     `json:"confidence"`
		Leverage        int     `json:"leverage"`
		PositionPct     float64 `json:"position_pct"`
		PositionSizeUSD float64 `json:"position_size_usd"`
		StopLoss        float64 `json:"stop_loss"`
		TakeProfit      float64 `json:"take_profit"`
		Reasoning       string  `json:"reasoning"`
	}{
		{
			Symbol:          "BTCUSDT",
			Action:          "open_long",
			Confidence:      85,
			Leverage:        10,
			PositionPct:     0,    // Not provided
			PositionSizeUSD: 2500, // Absolute size provided
			StopLoss:        45000,
			TakeProfit:      55000,
			Reasoning:       "Strong momentum",
		},
	}

	decisions, avgConf := convertRawDecisions(rawDecisions)

	if len(decisions) != 1 {
		t.Fatalf("Expected 1 decision, got %d", len(decisions))
	}

	if avgConf != 85 {
		t.Errorf("Expected avg confidence 85, got %d", avgConf)
	}

	d := decisions[0]

	// CRITICAL: PositionSizeUSD should be preserved, NOT converted to percentage
	if d.PositionSizeUSD != 2500 {
		t.Errorf("PositionSizeUSD should be 2500, got %f", d.PositionSizeUSD)
	}

	// PositionPct should remain 0 since it wasn't provided
	if d.PositionPct != 0 {
		t.Errorf("PositionPct should be 0 (not provided), got %f", d.PositionPct)
	}
}

func TestConvertRawDecisions_DefaultsWhenNothingProvided(t *testing.T) {
	rawDecisions := []struct {
		Symbol          string  `json:"symbol"`
		Action          string  `json:"action"`
		Confidence      int     `json:"confidence"`
		Leverage        int     `json:"leverage"`
		PositionPct     float64 `json:"position_pct"`
		PositionSizeUSD float64 `json:"position_size_usd"`
		StopLoss        float64 `json:"stop_loss"`
		TakeProfit      float64 `json:"take_profit"`
		Reasoning       string  `json:"reasoning"`
	}{
		{
			Symbol:          "BTCUSDT",
			Action:          "open_long",
			Confidence:      75,
			Leverage:        10,
			PositionPct:     0, // Nothing provided
			PositionSizeUSD: 0, // Nothing provided
			StopLoss:        45000,
			TakeProfit:      55000,
		},
	}

	decisions, _ := convertRawDecisions(rawDecisions)

	if len(decisions) != 1 {
		t.Fatalf("Expected 1 decision, got %d", len(decisions))
	}

	d := decisions[0]

	// Should apply default 20% when nothing provided
	if d.PositionPct != 0.2 {
		t.Errorf("Expected default PositionPct 0.2, got %f", d.PositionPct)
	}
}
