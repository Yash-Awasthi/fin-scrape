"""
Options Pricing — Black-Scholes, Greeks, and Binomial Tree models.

Provides European and American option pricing, Greeks calculation,
implied volatility solving, and options chain analysis. Pure math functions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OptionQuote:
    """Single option contract."""
    symbol: str
    option_type: str  # "call" or "put"
    strike: float
    expiry: str  # ISO date
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float


@dataclass
class OptionPricing:
    """Pricing result for an option."""
    price: float
    intrinsic: float
    time_value: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    model: str


@dataclass
class OptionChain:
    """Full option chain for a symbol."""
    underlying: str
    underlying_price: float
    expiry: str
    calls: List[OptionQuote]
    puts: List[OptionQuote]
    max_pain: float
    put_call_ratio: float


@dataclass
class Greeks:
    """Option Greeks."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


# ---------------------------------------------------------------------------
# Black-Scholes
# ---------------------------------------------------------------------------

def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function (approximation)."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def black_scholes(
    spot: float,
    strike: float,
    time_to_expiry: float,  # years
    risk_free_rate: float,
    volatility: float,
    option_type: str = "call",
) -> OptionPricing:
    """
    Black-Scholes pricing for European options.
    
    Args:
        spot: Current underlying price
        strike: Option strike price
        time_to_expiry: Time to expiration in years
        risk_free_rate: Risk-free interest rate (annual)
        volatility: Implied volatility (annual)
        option_type: "call" or "put"
    
    Returns:
        OptionPricing with price and Greeks
    """
    if time_to_expiry <= 0 or volatility <= 0:
        # At or past expiry
        if option_type == "call":
            intrinsic = max(0, spot - strike)
        else:
            intrinsic = max(0, strike - spot)
        return OptionPricing(
            price=intrinsic, intrinsic=intrinsic, time_value=0,
            delta=1.0 if option_type == "call" else -1.0,
            gamma=0, theta=0, vega=0, rho=0, model="black_scholes",
        )
    
    sqrt_t = math.sqrt(time_to_expiry)
    d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    
    if option_type == "call":
        price = spot * _norm_cdf(d1) - strike * math.exp(-risk_free_rate * time_to_expiry) * _norm_cdf(d2)
        delta = _norm_cdf(d1)
        theta = (-(spot * _norm_pdf(d1) * volatility) / (2 * sqrt_t) -
                 risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * _norm_cdf(d2)) / 365
        rho = strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * _norm_cdf(d2) / 100
    else:
        price = strike * math.exp(-risk_free_rate * time_to_expiry) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)
        delta = _norm_cdf(d1) - 1
        theta = (-(spot * _norm_pdf(d1) * volatility) / (2 * sqrt_t) +
                 risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * _norm_cdf(-d2)) / 365
        rho = -strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * _norm_cdf(-d2) / 100
    
    intrinsic = max(0, spot - strike) if option_type == "call" else max(0, strike - spot)
    time_value = max(0, price - intrinsic)
    
    # Common Greeks
    gamma = _norm_pdf(d1) / (spot * volatility * sqrt_t)
    vega = spot * _norm_pdf(d1) * sqrt_t / 100  # per 1% vol change
    
    return OptionPricing(
        price=round(price, 4),
        intrinsic=round(intrinsic, 4),
        time_value=round(time_value, 4),
        delta=round(delta, 4),
        gamma=round(gamma, 4),
        theta=round(theta, 4),
        vega=round(vega, 4),
        rho=round(rho, 4),
        model="black_scholes",
    )


# ---------------------------------------------------------------------------
# Binomial Tree (American options)
# ---------------------------------------------------------------------------

def binomial_tree(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    steps: int = 100,
    option_type: str = "call",
) -> OptionPricing:
    """
    Binomial tree pricing for American options.
    
    Supports early exercise for American-style options.
    """
    dt = time_to_expiry / steps
    u = math.exp(volatility * math.sqrt(dt))
    d = 1 / u
    p = (math.exp(risk_free_rate * dt) - d) / (u - d)
    discount = math.exp(-risk_free_rate * dt)
    
    # Build price tree at expiry
    prices = [spot * (u ** (steps - i)) * (d ** i) for i in range(steps + 1)]
    
    # Option values at expiry
    if option_type == "call":
        values = [max(0, s - strike) for s in prices]
    else:
        values = [max(0, strike - s) for s in prices]
    
    # Backward induction
    for step in range(steps - 1, -1, -1):
        new_values = []
        for i in range(step + 1):
            hold = discount * (p * values[i] + (1 - p) * values[i + 1])
            
            # Early exercise check (American)
            if option_type == "call":
                exercise = max(0, spot * (u ** (step - i)) * (d ** i) - strike)
            else:
                exercise = max(0, strike - spot * (u ** (step - i)) * (d ** i))
            
            new_values.append(max(hold, exercise))
        values = new_values
    
    price = values[0]
    intrinsic = max(0, spot - strike) if option_type == "call" else max(0, strike - spot)
    
    return OptionPricing(
        price=round(price, 4),
        intrinsic=round(intrinsic, 4),
        time_value=round(max(0, price - intrinsic), 4),
        delta=0, gamma=0, theta=0, vega=0, rho=0,  # Greeks not computed for tree
        model=f"binomial_tree_{steps}steps",
    )


# ---------------------------------------------------------------------------
# Implied Volatility
# ---------------------------------------------------------------------------

def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    option_type: str = "call",
    tolerance: float = 1e-6,
    max_iterations: int = 100,
) -> float:
    """
    Solve for implied volatility using Newton-Raphson method.
    
    Finds the volatility that makes the Black-Scholes price
    match the observed market price.
    """
    # Initial guess
    vol = 0.3
    
    for _ in range(max_iterations):
        result = black_scholes(spot, strike, time_to_expiry, risk_free_rate, vol, option_type)
        diff = result.price - market_price
        
        if abs(diff) < tolerance:
            return round(vol, 6)
        
        # Vega for Newton-Raphson
        if result.vega == 0:
            break
        
        vol -= diff / (result.vega * 100)  # vega is per 1% change
    
    return round(vol, 6)


# ---------------------------------------------------------------------------
# Options chain analysis
# ---------------------------------------------------------------------------

def calculate_max_pain(
    calls: List[OptionQuote],
    puts: List[OptionQuote],
    underlying_price: float,
) -> float:
    """
    Calculate max pain — the strike price where the most options
    expire worthless (maximum pain for option holders).
    """
    strikes = sorted(set(c.strike for c in calls + puts))
    if not strikes:
        return underlying_price
    
    min_pain = float('inf')
    max_pain_strike = underlying_price
    
    for strike in strikes:
        pain = 0
        for c in calls:
            if c.strike < strike:
                pain += (strike - c.strike) * c.open_interest
        for p in puts:
            if p.strike > strike:
                pain += (p.strike - strike) * p.open_interest
        
        if pain < min_pain:
            min_pain = pain
            max_pain_strike = strike
    
    return max_pain_strike


def calculate_put_call_ratio(
    calls: List[OptionQuote],
    puts: List[OptionQuote],
) -> float:
    """Calculate put/call ratio by volume and open interest."""
    call_volume = sum(c.volume for c in calls)
    put_volume = sum(p.volume for p in puts)
    
    if call_volume == 0:
        return 0.0
    
    return round(put_volume / call_volume, 4)


def find_options_by_delta(
    options: List[OptionQuote],
    target_delta: float,
    tolerance: float = 0.1,
) -> List[OptionQuote]:
    """Find options near a target delta (useful for equivalent stock position)."""
    # Approximate delta from moneyness
    result = []
    for opt in options:
        # Simple delta approximation
        if opt.option_type == "call":
            approx_delta = max(0, min(1, (opt.last - opt.strike) / (opt.strike * 0.1) + 0.5)) if opt.last > 0 else 0.5
        else:
            approx_delta = max(-1, min(0, -(opt.last - opt.strike) / (opt.strike * 0.1) - 0.5)) if opt.last > 0 else -0.5
        
        if abs(approx_delta - target_delta) <= tolerance:
            result.append(opt)
    
    return result
