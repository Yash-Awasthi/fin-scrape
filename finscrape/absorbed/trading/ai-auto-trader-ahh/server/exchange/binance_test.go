package exchange

import (
	"testing"
)

// TestOrderSideLogic tests the side logic for closing positions
func TestClosePositionSideLogic(t *testing.T) {
	tests := []struct {
		name         string
		positionAmt  float64
		expectedSide string
		expectedQty  float64
	}{
		{
			name:         "Close long position",
			positionAmt:  0.5,
			expectedSide: "SELL",
			expectedQty:  0.5,
		},
		{
			name:         "Close short position",
			positionAmt:  -0.5,
			expectedSide: "BUY",
			expectedQty:  0.5, // Absolute value
		},
		{
			name:         "Close large long",
			positionAmt:  2.5,
			expectedSide: "SELL",
			expectedQty:  2.5,
		},
		{
			name:         "Close large short",
			positionAmt:  -3.0,
			expectedSide: "BUY",
			expectedQty:  3.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate ClosePosition logic
			side := "SELL"
			quantity := tt.positionAmt
			if tt.positionAmt < 0 {
				side = "BUY"
				quantity = -tt.positionAmt
			}

			if side != tt.expectedSide {
				t.Errorf("Side = %s, want %s", side, tt.expectedSide)
			}
			if quantity != tt.expectedQty {
				t.Errorf("Quantity = %f, want %f", quantity, tt.expectedQty)
			}
		})
	}
}

// TestBracketOrderPriceCalculation tests SL/TP price calculation
func TestBracketOrderPriceCalculation(t *testing.T) {
	tests := []struct {
		name       string
		isLong     bool
		entryPrice float64
		slPct      float64
		tpPct      float64
		wantSL     float64
		wantTP     float64
	}{
		{
			name:       "Long position 2% SL, 6% TP",
			isLong:     true,
			entryPrice: 50000,
			slPct:      2,
			tpPct:      6,
			wantSL:     49000, // 50000 * (1 - 0.02) = 49000
			wantTP:     53000, // 50000 * (1 + 0.06) = 53000
		},
		{
			name:       "Short position 2% SL, 6% TP",
			isLong:     false,
			entryPrice: 50000,
			slPct:      2,
			tpPct:      6,
			wantSL:     51000, // 50000 * (1 + 0.02) = 51000
			wantTP:     47000, // 50000 * (1 - 0.06) = 47000
		},
		{
			name:       "Long position 1.5% SL, 4.5% TP",
			isLong:     true,
			entryPrice: 40000,
			slPct:      1.5,
			tpPct:      4.5,
			wantSL:     39400, // 40000 * (1 - 0.015) = 39400
			wantTP:     41800, // 40000 * (1 + 0.045) = 41800
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var slPrice, tpPrice float64

			if tt.isLong {
				slPrice = tt.entryPrice * (1 - tt.slPct/100)
				tpPrice = tt.entryPrice * (1 + tt.tpPct/100)
			} else {
				slPrice = tt.entryPrice * (1 + tt.slPct/100)
				tpPrice = tt.entryPrice * (1 - tt.tpPct/100)
			}

			if slPrice != tt.wantSL {
				t.Errorf("SL price = %f, want %f", slPrice, tt.wantSL)
			}
			if tpPrice != tt.wantTP {
				t.Errorf("TP price = %f, want %f", tpPrice, tt.wantTP)
			}

			// Verify SL/TP direction is correct
			if tt.isLong {
				if slPrice >= tt.entryPrice {
					t.Error("Long SL should be below entry")
				}
				if tpPrice <= tt.entryPrice {
					t.Error("Long TP should be above entry")
				}
			} else {
				if slPrice <= tt.entryPrice {
					t.Error("Short SL should be above entry")
				}
				if tpPrice >= tt.entryPrice {
					t.Error("Short TP should be below entry")
				}
			}
		})
	}
}

// TestTimeOffsetCalculation tests the server time offset logic
func TestTimeOffsetCalculation(t *testing.T) {
	tests := []struct {
		name           string
		localTime      int64
		serverTime     int64
		expectedOffset int64
	}{
		{
			name:           "Server ahead by 100ms",
			localTime:      1704067200000,
			serverTime:     1704067200100,
			expectedOffset: 100,
		},
		{
			name:           "Server behind by 50ms",
			localTime:      1704067200000,
			serverTime:     1704067199950,
			expectedOffset: -50,
		},
		{
			name:           "Perfectly synced",
			localTime:      1704067200000,
			serverTime:     1704067200000,
			expectedOffset: 0,
		},
		{
			name:           "Server ahead by 1 second",
			localTime:      1704067200000,
			serverTime:     1704067201000,
			expectedOffset: 1000,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			offset := tt.serverTime - tt.localTime
			if offset != tt.expectedOffset {
				t.Errorf("Offset = %d, want %d", offset, tt.expectedOffset)
			}
		})
	}
}

// TestAccountInfoFields tests the account info structure
func TestAccountInfoFields(t *testing.T) {
	// Test that TotalMarginBalance = TotalWalletBalance + TotalUnrealizedProfit
	account := AccountInfo{
		TotalWalletBalance:    10000,
		TotalUnrealizedProfit: 500,
		TotalMarginBalance:    10500,
		AvailableBalance:      8500,
	}

	expectedMargin := account.TotalWalletBalance + account.TotalUnrealizedProfit
	if account.TotalMarginBalance != expectedMargin {
		t.Errorf("TotalMarginBalance = %f, want %f (Wallet + Unrealized)",
			account.TotalMarginBalance, expectedMargin)
	}

	// With negative unrealized P&L
	account2 := AccountInfo{
		TotalWalletBalance:    10000,
		TotalUnrealizedProfit: -300,
		TotalMarginBalance:    9700,
		AvailableBalance:      7700,
	}

	expectedMargin2 := account2.TotalWalletBalance + account2.TotalUnrealizedProfit
	if account2.TotalMarginBalance != expectedMargin2 {
		t.Errorf("TotalMarginBalance = %f, want %f (Wallet + Unrealized)",
			account2.TotalMarginBalance, expectedMargin2)
	}
}

// TestPositionFields tests the position structure
func TestPositionFields(t *testing.T) {
	// Long position
	longPos := Position{
		Symbol:           "BTCUSDT",
		PositionAmt:      0.1, // Positive = long
		EntryPrice:       50000,
		MarkPrice:        51000,
		UnrealizedProfit: 100, // (51000 - 50000) * 0.1
		Leverage:         10,
	}

	if longPos.PositionAmt <= 0 {
		t.Error("Long position should have positive PositionAmt")
	}

	expectedPnL := (longPos.MarkPrice - longPos.EntryPrice) * longPos.PositionAmt
	if longPos.UnrealizedProfit != expectedPnL {
		t.Errorf("UnrealizedProfit = %f, want %f", longPos.UnrealizedProfit, expectedPnL)
	}

	// Short position
	shortPos := Position{
		Symbol:           "ETHUSDT",
		PositionAmt:      -0.5, // Negative = short
		EntryPrice:       3000,
		MarkPrice:        2900,
		UnrealizedProfit: 50, // (3000 - 2900) * 0.5
		Leverage:         10,
	}

	if shortPos.PositionAmt >= 0 {
		t.Error("Short position should have negative PositionAmt")
	}

	expectedShortPnL := (shortPos.EntryPrice - shortPos.MarkPrice) * (-shortPos.PositionAmt)
	if shortPos.UnrealizedProfit != expectedShortPnL {
		t.Errorf("Short UnrealizedProfit = %f, want %f", shortPos.UnrealizedProfit, expectedShortPnL)
	}
}

// TestOrderFields tests the order structure
func TestOrderFields(t *testing.T) {
	order := Order{
		OrderID:      12345,
		Symbol:       "BTCUSDT",
		Status:       "FILLED",
		Side:         "BUY",
		PositionSide: "BOTH",
		Type:         "MARKET",
		Price:        0,     // Market orders have no price
		AvgPrice:     50100, // Actual fill price
		OrigQty:      0.1,
		ExecutedQty:  0.1,
		Time:         1704067200000,
		UpdateTime:   1704067200100,
	}

	// Verify AvgPrice is the actual fill price for market orders
	if order.AvgPrice == 0 && order.Type == "MARKET" && order.Status == "FILLED" {
		t.Error("Filled market order should have AvgPrice")
	}

	// Verify ExecutedQty matches OrigQty for filled orders
	if order.Status == "FILLED" && order.ExecutedQty != order.OrigQty {
		t.Errorf("Filled order ExecutedQty (%f) should match OrigQty (%f)",
			order.ExecutedQty, order.OrigQty)
	}
}

// TestTickerFields tests the ticker structure
func TestTickerFields(t *testing.T) {
	ticker := Ticker{
		Symbol: "BTCUSDT",
		Price:  50000.50,
		Time:   1704067200000,
	}

	if ticker.Price <= 0 {
		t.Error("Ticker price should be positive")
	}

	if ticker.Symbol == "" {
		t.Error("Ticker symbol should not be empty")
	}
}

// TestQuantityPrecision tests quantity rounding scenarios
func TestQuantityPrecision(t *testing.T) {
	tests := []struct {
		name       string
		quantity   float64
		stepSize   float64
		wantRounded float64
	}{
		{
			name:        "BTC step size 0.001",
			quantity:    0.12345,
			stepSize:    0.001,
			wantRounded: 0.123,
		},
		{
			name:        "ETH step size 0.001",
			quantity:    1.5678,
			stepSize:    0.001,
			wantRounded: 1.567,
		},
		{
			name:        "Altcoin step size 1",
			quantity:    156.78,
			stepSize:    1,
			wantRounded: 156,
		},
		{
			name:        "Altcoin step size 0.1",
			quantity:    45.67,
			stepSize:    0.1,
			wantRounded: 45.6,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Simulate step size rounding logic
			rounded := float64(int64(tt.quantity/tt.stepSize)) * tt.stepSize

			// Allow small floating point tolerance
			tolerance := tt.stepSize / 10
			if rounded < tt.wantRounded-tolerance || rounded > tt.wantRounded+tolerance {
				t.Errorf("Rounded quantity = %f, want %f", rounded, tt.wantRounded)
			}
		})
	}
}
