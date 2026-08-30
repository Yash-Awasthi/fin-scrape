"""Tests for options_pricing.py — Black-Scholes and Greeks."""

import math
import pytest
from finscrape.services.options_pricing import (
    black_scholes, binomial_tree, implied_volatility,
    calculate_max_pain, calculate_put_call_ratio,
    OptionQuote,
)


class TestBlackScholes:
    def test_call_in_the_money(self):
        result = black_scholes(spot=105, strike=100, time_to_expiry=0.25, risk_free_rate=0.05, volatility=0.2)
        assert result.price > 0
        assert result.price > result.intrinsic  # Has time value
        assert result.delta > 0

    def test_put_in_the_money(self):
        result = black_scholes(spot=95, strike=100, time_to_expiry=0.25, risk_free_rate=0.05, volatility=0.2, option_type="put")
        assert result.price > 0
        assert result.delta < 0

    def test_call_at_the_money(self):
        result = black_scholes(spot=100, strike=100, time_to_expiry=0.25, risk_free_rate=0.05, volatility=0.2)
        assert result.price > 0
        assert 0.4 < result.delta < 0.6  # ATM delta ~0.5

    def test_call_out_of_the_money(self):
        result = black_scholes(spot=90, strike=100, time_to_expiry=0.25, risk_free_rate=0.05, volatility=0.2)
        assert result.price > 0
        assert result.intrinsic == 0

    def test_expired_option(self):
        result = black_scholes(spot=105, strike=100, time_to_expiry=0, risk_free_rate=0.05, volatility=0.2)
        assert result.price == 5.0  # Pure intrinsic
        assert result.time_value == 0

    def test_greeks_positive(self):
        result = black_scholes(spot=100, strike=100, time_to_expiry=0.25, risk_free_rate=0.05, volatility=0.2)
        assert result.gamma > 0
        assert result.vega > 0
        assert result.theta < 0  # Time decay

    def test_put_call_parity(self):
        spot, strike, t, r, vol = 100, 100, 0.25, 0.05, 0.2
        call = black_scholes(spot, strike, t, r, vol, "call")
        put = black_scholes(spot, strike, t, r, vol, "put")
        # C - P = S - K * e^(-rT)
        parity_left = call.price - put.price
        parity_right = spot - strike * math.exp(-r * t)
        assert abs(parity_left - parity_right) < 0.01


class TestBinomialTree:
    def test_converges_to_bs(self):
        spot, strike, t, r, vol = 100, 100, 0.25, 0.05, 0.2
        bs = black_scholes(spot, strike, t, r, vol, "call")
        tree = binomial_tree(spot, strike, t, r, vol, steps=200)
        assert abs(tree.price - bs.price) < 0.05  # Close convergence

    def test_american_put_has_early_exercise_premium(self):
        # Deep ITM American put should be worth more than European
        american = binomial_tree(spot=80, strike=100, time_to_expiry=0.5, risk_free_rate=0.05, volatility=0.2, steps=100, option_type="put")
        european = black_scholes(spot=80, strike=100, time_to_expiry=0.5, risk_free_rate=0.05, volatility=0.2, option_type="put")
        assert american.price >= european.price


class TestImpliedVolatility:
    def test_roundtrip(self):
        """BS price → IV → BS price should match."""
        spot, strike, t, r, vol = 100, 100, 0.25, 0.05, 0.25
        bs = black_scholes(spot, strike, t, r, vol, "call")
        solved_vol = implied_volatility(bs.price, spot, strike, t, r, "call")
        assert abs(solved_vol - vol) < 0.001

    def test_higher_price_higher_iv(self):
        """Higher market price → higher implied volatility."""
        spot, strike, t, r = 100, 100, 0.25, 0.05
        vol1 = implied_volatility(3.0, spot, strike, t, r)
        vol2 = implied_volatility(5.0, spot, strike, t, r)
        assert vol2 > vol1


class TestMaxPain:
    def test_calculates(self):
        calls = [OptionQuote(symbol="C1", option_type="call", strike=100, expiry="", bid=0, ask=0, last=0, volume=0, open_interest=100, implied_volatility=0)]
        puts = [OptionQuote(symbol="P1", option_type="put", strike=90, expiry="", bid=0, ask=0, last=0, volume=0, open_interest=100, implied_volatility=0)]
        mp = calculate_max_pain(calls, puts, 95)
        assert 90 <= mp <= 100


class TestPutCallRatio:
    def test_ratio(self):
        calls = [OptionQuote(symbol="C", option_type="call", strike=100, expiry="", bid=0, ask=0, last=0, volume=1000, open_interest=0, implied_volatility=0)]
        puts = [OptionQuote(symbol="P", option_type="put", strike=100, expiry="", bid=0, ask=0, last=0, volume=500, open_interest=0, implied_volatility=0)]
        ratio = calculate_put_call_ratio(calls, puts)
        assert ratio == 0.5
